#!/usr/bin/env python3
"""GraphRAG Service Monitor.

This script monitors the GraphRAG services and restarts them if they crash.
It can be run as a cron job or as a daemon.
"""

import logging
import os
import subprocess
import sys
import time
import psutil
from src.config import get_port

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
LOG_FILE = os.path.expanduser("~/.graphrag/logs/monitor.log")
PID_DIR = os.path.expanduser("~/.graphrag/pids")
CONFIG_FILE = os.path.expanduser("~/.graphrag/config.env")
CHECK_INTERVAL = 60  # seconds

# Configure logging
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# Load configuration
def load_config():
    """Load configuration from environment file."""
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    config[key] = value
    return config


config = load_config()

# Get ports from centralized configuration
neo4j_http_port = get_port("neo4j_http")
api_port = get_port("api")

# Service definitions
SERVICES = [
    {
        "name": "neo4j",
        "pid_file": os.path.join(PID_DIR, "neo4j.pid"),
        "check_url": f"http://localhost:{neo4j_http_port}",
        "start_cmd": os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "graphrag-service.sh"
        )
        + " start-neo4j",
    },
    {
        "name": "api",
        "pid_file": os.path.join(PID_DIR, "api.pid"),
        "check_url": f"http://localhost:{api_port}/health",
        "start_cmd": os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "graphrag-service.sh"
        )
        + " start-api",
    },
    {
        "name": "mpc",
        "pid_file": os.path.join(PID_DIR, "mpc.pid"),
        "start_cmd": os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "graphrag-service.sh"
        )
        + " start-mpc",
    },
]


def check_service(service) -> bool | None:
    """Check if a service is running and restart it if necessary."""
    name = service["name"]
    pid_file = service["pid_file"]

    # Check if PID file exists
    if not os.path.exists(pid_file):
        logging.warning(f"{name} service is not running (no PID file)")
        return False

    # Read PID from file
    try:
        with open(pid_file) as f:
            pid = int(f.read().strip())
    except Exception as e:
        logging.error(f"Error reading PID file for {name}: {e}")
        return False

    # Check if process is running
    try:
        process = psutil.Process(pid)
        if process.is_running():
            # Additional check for HTTP services
            if "check_url" in service:
                try:
                    result = subprocess.run(
                        [
                            "curl",
                            "-s",
                            "-o",
                            "/dev/null",
                            "-w",
                            "%{http_code}",
                            service["check_url"],
                        ],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if result.stdout.strip() != "200":
                        logging.warning(
                            f"{name} service is not responding properly "
                            f"(HTTP {result.stdout.strip()})"
                        )
                        return False
                except subprocess.SubprocessError as e:
                    logging.warning(f"Error checking {name} service URL: {e}")
                    return False

            # Service is running
            return True
        else:
            logging.warning(
                f"{name} service is not running (PID {pid} not found)"
            )
            return False
    except psutil.NoSuchProcess:
        logging.warning(f"{name} service is not running (PID {pid} not found)")
        return False


def restart_service(service) -> bool | None:
    """Restart a service."""
    name = service["name"]
    pid_file = service["pid_file"]
    start_cmd = service["start_cmd"]

    logging.info(f"Restarting {name} service...")

    # Remove PID file if it exists
    if os.path.exists(pid_file):
        os.remove(pid_file)

    # Start service
    try:
        result = subprocess.run(
            start_cmd, shell=True, capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            logging.info(f"Successfully restarted {name} service")
            return True
        else:
            logging.error(f"Failed to restart {name} service: {result.stderr}")
            return False
    except subprocess.SubprocessError as e:
        logging.error(f"Error restarting {name} service: {e}")
        return False


def monitor_services() -> None:
    """Monitor all services and restart them if necessary."""
    for service in SERVICES:
        if not check_service(service):
            restart_service(service)


def collect_resource_usage() -> None:
    """Collect resource usage information."""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    logging.info(
        f"Resource Usage - CPU: {cpu_percent}%, "
        f"Memory: {memory.percent}%, Disk: {disk.percent}%"
    )


def main() -> None:
    """Main function."""
    logging.info("Starting GraphRAG Service Monitor")

    try:
        while True:
            monitor_services()
            collect_resource_usage()
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        logging.info("Stopping GraphRAG Service Monitor")
        sys.exit(0)


if __name__ == "__main__":
    main()
