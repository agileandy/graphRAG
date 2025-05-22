"""Job management system for GraphRAG project.

This module provides a job queue and management system for handling
long-running background tasks in the GraphRAG system.
"""

import glob
import json
import logging
import os
import threading
import traceback
import uuid
from collections.abc import Callable
from datetime import datetime
from enum import Enum
from typing import Any

# Configure logging
logger = logging.getLogger(__name__)


# Job status enum
class JobStatus(str, Enum):
    """Job status enum."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job:
    """Job class for tracking background tasks."""

    def __init__(
        self,
        job_id: str,
        job_type: str,
        params: dict[str, Any],
        created_by: str | None = None,
    ) -> None:
        """Initialize a job.

        Args:
            job_id: Unique job ID
            job_type: Type of job (e.g., "add-document", "add-folder")
            params: Job parameters
            created_by: ID of the client that created the job

        """
        self.job_id = job_id
        self.job_type = job_type
        self.params = params
        self.created_by = created_by
        self.status = JobStatus.QUEUED
        self.progress = 0.0
        self.total_items = 0
        self.processed_items = 0
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.result = None
        self.error = None
        self.task = None  # Will hold the asyncio task

    def to_dict(self) -> dict[str, Any]:
        """Convert job to dictionary.

        Returns:
            Job as dictionary

        """
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "status": self.status,
            "progress": self.progress,
            "total_items": self.total_items,
            "processed_items": self.processed_items,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "result": self.result,
            "error": self.error,
        }

    def update_progress(self, processed_items: int, total_items: int) -> None:
        """Update job progress.

        Args:
            processed_items: Number of processed items
            total_items: Total number of items

        """
        old_progress = self.progress
        self.processed_items = processed_items
        self.total_items = total_items
        if total_items > 0:
            self.progress = (processed_items / total_items) * 100
        else:
            self.progress = 0

        logger.debug(
            f"Job {self.job_id} progress updated: {old_progress:.1f}% -> {self.progress:.1f}% ({processed_items}/{total_items})"
        )

    def start(self) -> None:
        """Mark job as started."""
        logger.info(f"Job {self.job_id} ({self.job_type}) starting")
        self.status = JobStatus.RUNNING
        self.started_at = datetime.now()

    def complete(self, result: Any = None) -> None:
        """Mark job as completed.

        Args:
            result: Job result

        """
        logger.info(f"Job {self.job_id} ({self.job_type}) completed successfully")
        if result:
            logger.debug(f"Job {self.job_id} result: {result}")

        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now()
        self.progress = 100
        self.result = result

    def fail(self, error: str) -> None:
        """Mark job as failed.

        Args:
            error: Error message

        """
        logger.error(f"Job {self.job_id} ({self.job_type}) failed: {error}")
        self.status = JobStatus.FAILED
        self.completed_at = datetime.now()
        self.error = error

    def cancel(self) -> None:
        """Mark job as cancelled."""
        logger.info(f"Job {self.job_id} ({self.job_type}) cancelled")
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.now()


class JobManager:
    """Job manager for handling background tasks."""

    _instance = None

    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize job manager."""
        if self._initialized:
            return

        self.jobs: dict[str, Job] = {}
        self.lock = threading.RLock()
        self._initialized = True

        # Create a directory for persisting jobs
        self.jobs_dir = os.path.expanduser("~/.graphrag/jobs")
        os.makedirs(self.jobs_dir, exist_ok=True)

        # Load any persisted jobs
        self._load_jobs()

    def _load_jobs(self) -> None:
        """Load persisted jobs from disk."""
        try:
            # Get all job files
            job_files = glob.glob(os.path.join(self.jobs_dir, "*.json"))
            logger.info(f"Loading {len(job_files)} persisted jobs from {self.jobs_dir}")

            for job_file in job_files:
                try:
                    logger.debug(f"Loading job from {job_file}")
                    with open(job_file) as f:
                        job_data = json.load(f)

                    # Create a job object from the data
                    job_id = job_data.get("job_id")
                    job_type = job_data.get("job_type")
                    params = job_data.get("params", {})
                    created_by = job_data.get("created_by")

                    if job_id and job_type:
                        logger.debug(f"Creating job object for {job_id} ({job_type})")
                        job = Job(job_id, job_type, params, created_by)

                        # Restore job state
                        loaded_status = job_data.get("status", JobStatus.QUEUED)
                        if loaded_status == JobStatus.RUNNING:
                            # If the job was running when the server shut down, mark it as failed
                            job.status = JobStatus.FAILED
                            job.error = "Job failed due to server restart."
                            logger.warning(
                                f"Job {job_id} was running during shutdown, marked as FAILED."
                            )
                        else:
                            job.status = loaded_status

                        job.progress = job_data.get("progress", 0.0)
                        job.total_items = job_data.get("total_items", 0)
                        job.processed_items = job_data.get("processed_items", 0)

                        # Parse datetime strings
                        if job_data.get("created_at"):
                            job.created_at = datetime.fromisoformat(
                                job_data.get("created_at")
                            )
                        if job_data.get("started_at"):
                            job.started_at = datetime.fromisoformat(
                                job_data.get("started_at")
                            )
                        if job_data.get("completed_at"):
                            job.completed_at = datetime.fromisoformat(
                                job_data.get("completed_at")
                            )

                        job.result = job_data.get("result")
                        job.error = job_data.get("error")

                        # Add to jobs dictionary
                        self.jobs[job_id] = job
                        logger.debug(f"Loaded job {job_id} with status {job.status}")
                    else:
                        logger.warning(
                            f"Invalid job data in {job_file}: missing job_id or job_type"
                        )
                except Exception as e:
                    logger.error(f"Error loading job from {job_file}: {e}")
                    logger.debug(f"Exception details: {traceback.format_exc()}")
        except Exception as e:
            logger.error(f"Error loading jobs: {e}")
            logger.debug(f"Exception details: {traceback.format_exc()}")

    def _save_job(self, job: Job) -> None:
        """Save a job to disk.

        Args:
            job: Job to save

        """
        try:
            # Create a serializable representation of the job
            job_data = job.to_dict()

            # Add params and created_by which aren't in to_dict()
            job_data["params"] = job.params
            job_data["created_by"] = job.created_by

            # Save to file
            job_file = os.path.join(self.jobs_dir, f"{job.job_id}.json")
            logger.debug(f"Saving job {job.job_id} to {job_file}")

            with open(job_file, "w") as f:
                json.dump(job_data, f, indent=2)

            logger.debug(f"Job {job.job_id} saved successfully")
        except Exception as e:
            logger.error(f"Error saving job {job.job_id}: {e}")
            logger.debug(f"Exception details: {traceback.format_exc()}")

    def create_job(
        self, job_type: str, params: dict[str, Any], created_by: str | None = None
    ) -> Job:
        """Create a new job.

        Args:
            job_type: Type of job
            params: Job parameters
            created_by: ID of the client that created the job

        Returns:
            Created job

        """
        job_id = str(uuid.uuid4())
        logger.info(
            f"Creating new job: id={job_id}, type={job_type}, created_by={created_by}"
        )
        logger.debug(f"Job parameters: {params}")

        job = Job(job_id, job_type, params, created_by)

        with self.lock:
            self.jobs[job_id] = job
            logger.debug(
                f"Added job {job_id} to jobs dictionary (total jobs: {len(self.jobs)})"
            )

        # Persist the job
        self._save_job(job)

        return job

    def get_job(self, job_id: str) -> Job | None:
        """Get a job by ID.

        Args:
            job_id: Job ID

        Returns:
            Job or None if not found

        """
        logger.debug(f"Looking up job with ID: {job_id}")

        with self.lock:
            job = self.jobs.get(job_id)

        if job:
            logger.debug(f"Found job {job_id} with status {job.status}")
        else:
            logger.warning(f"Job {job_id} not found")

        return job

    def get_jobs(
        self,
        status: JobStatus | list[JobStatus] | None = None,
        job_type: str | None = None,
        created_by: str | None = None,
    ) -> list[Job]:
        """Get jobs filtered by status, type, and creator.

        Args:
            status: Filter by status
            job_type: Filter by job type
            created_by: Filter by creator

        Returns:
            List of jobs

        """
        logger.debug(
            f"Getting jobs with filters: status={status}, job_type={job_type}, created_by={created_by}"
        )

        with self.lock:
            jobs = list(self.jobs.values())
            logger.debug(f"Total jobs before filtering: {len(jobs)}")

        # Filter by status
        if status:
            if isinstance(status, list):
                jobs = [job for job in jobs if job.status in status]
                logger.debug(f"Filtered to {len(jobs)} jobs with status in {status}")
            else:
                jobs = [job for job in jobs if job.status == status]
                logger.debug(f"Filtered to {len(jobs)} jobs with status {status}")

        # Filter by job type
        if job_type:
            jobs = [job for job in jobs if job.job_type == job_type]
            logger.debug(f"Filtered to {len(jobs)} jobs with type {job_type}")

        # Filter by creator
        if created_by:
            jobs = [job for job in jobs if job.created_by == created_by]
            logger.debug(f"Filtered to {len(jobs)} jobs created by {created_by}")

        return jobs

    def run_job_async(self, job: Job, task_func: Callable[[Job], Any]) -> None:
        """Run a job asynchronously using threading.

        Args:
            job: Job to run
            task_func: Function to run in a separate thread

        """
        logger.info(f"Starting job {job.job_id} ({job.job_type}) asynchronously")

        def _run_job() -> None:
            logger.debug(f"Thread for job {job.job_id} started")
            job.start()
            try:
                logger.debug(f"Executing task function for job {job.job_id}")
                result = task_func(job)
                logger.debug(
                    f"Task function for job {job.job_id} completed successfully"
                )
                job.complete(result)
                logger.info(f"Job {job.job_id} completed successfully")
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Job {job.job_id} failed with error: {error_msg}")
                logger.debug(f"Exception details: {traceback.format_exc()}")
                job.fail(error_msg)
                raise

        # Create and start a thread
        thread = threading.Thread(target=_run_job)
        thread.daemon = (
            True  # Allow the thread to be terminated when the main program exits
        )
        # Store thread in job.task
        job.task = thread  # type: ignore
        thread.start()
        logger.debug(f"Thread for job {job.job_id} created and started")

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job.

        Args:
            job_id: Job ID

        Returns:
            True if job was cancelled, False otherwise

        """
        logger.info(f"Attempting to cancel job {job_id}")

        job = self.get_job(job_id)
        if not job:
            logger.warning(f"Cannot cancel job {job_id}: job not found")
            return False

        if job.status in [JobStatus.QUEUED, JobStatus.RUNNING]:
            logger.info(f"Cancelling job {job_id} with status {job.status}")

            if job.task and hasattr(job.task, "done") and not job.task.done():
                logger.debug(f"Cancelling task for job {job_id}")
                job.task.cancel()  # type: ignore

            job.cancel()

            # Persist the updated job
            self._save_job(job)

            logger.info(f"Job {job_id} cancelled successfully")
            return True
        else:
            logger.info(
                f"Cannot cancel job {job_id}: job is already in {job.status} state"
            )
            return False

    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """Clean up old completed jobs.

        Args:
            max_age_hours: Maximum age in hours

        Returns:
            Number of jobs cleaned up

        """
        logger.info(f"Cleaning up jobs older than {max_age_hours} hours")

        now = datetime.now()
        jobs_to_remove = []

        with self.lock:
            for job_id, job in self.jobs.items():
                if job.status in [
                    JobStatus.COMPLETED,
                    JobStatus.FAILED,
                    JobStatus.CANCELLED,
                ]:
                    if job.completed_at:
                        age = (now - job.completed_at).total_seconds() / 3600
                        if age > max_age_hours:
                            logger.debug(
                                f"Marking job {job_id} for removal (age: {age:.1f} hours)"
                            )
                            jobs_to_remove.append(job_id)

        # Remove jobs outside the lock to avoid deadlocks
        for job_id in jobs_to_remove:
            with self.lock:
                self.jobs.pop(job_id, None)
                logger.debug(f"Removed job {job_id}")

                # Also remove the job file
                job_file = os.path.join(self.jobs_dir, f"{job_id}.json")
                try:
                    if os.path.exists(job_file):
                        os.remove(job_file)
                        logger.debug(f"Removed job file {job_file}")
                except Exception as e:
                    logger.warning(f"Failed to remove job file {job_file}: {e}")

        logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")
        return len(jobs_to_remove)
