#!/usr/bin/env python3
"""
Bug Tracking API Server

This module implements a simple FastAPI server for bug tracking.
It provides RESTful endpoints for managing bugs.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('bugAPI')

# File to store bugs
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bugs.json")

# Global storage
bugs = []
next_id = 1
VALID_STATUSES = {'open', 'fixed'}

# Pydantic models
class BugBase(BaseModel):
    """Base model for a bug."""
    description: str
    cause: str

class BugCreate(BugBase):
    """Model for creating a bug."""
    pass

class BugUpdate(BaseModel):
    """Model for updating a bug."""
    status: Optional[str] = None
    resolution: Optional[str] = None

class Bug(BugBase):
    """Model for a bug."""
    id: int
    status: str
    resolution: str

class BugResponse(BaseModel):
    """Model for a bug response."""
    status: str
    message: str
    bug_id: Optional[int] = None

class BugListResponse(BaseModel):
    """Model for a bug list response."""
    status: str
    total_records: int
    bugs: List[Bug]

class BugGetResponse(BaseModel):
    """Model for a bug get response."""
    status: str
    bug: Optional[Bug] = None
    message: Optional[str] = None

def save_bugs():
    """Save bugs to a JSON file."""
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump({
                'bugs': bugs,
                'next_id': next_id
            }, f, indent=2)
        logger.info(f"Bugs saved to {DATA_FILE}")
    except Exception as e:
        logger.error(f"Error saving bugs: {e}")

def load_bugs():
    """Load bugs from a JSON file."""
    global bugs, next_id
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                bugs = data.get('bugs', [])
                next_id = data.get('next_id', 1)
            logger.info(f"Loaded {len(bugs)} bugs from {DATA_FILE}")
        else:
            logger.info(f"No data file found at {DATA_FILE}, starting with empty bug list")
    except Exception as e:
        logger.error(f"Error loading bugs: {e}")

# Create FastAPI app
app = FastAPI(
    title="Bug Tracking API",
    description="A simple API for bug tracking",
    version="1.0.0"
)

@app.on_event("startup")
def startup_event():
    """Load bugs on startup."""
    load_bugs()

@app.on_event("shutdown")
def shutdown_event():
    """Save bugs on shutdown."""
    save_bugs()

@app.post("/bugs", response_model=BugResponse)
def add_bug(bug: BugCreate):
    """Add a new bug."""
    global next_id
    
    new_bug = {
        'id': next_id,
        'description': bug.description,
        'cause': bug.cause,
        'status': 'open',
        'resolution': ''
    }
    
    bugs.append(new_bug)
    next_id += 1
    save_bugs()
    
    return {
        'status': 'success',
        'message': 'Bug added successfully',
        'bug_id': new_bug['id']
    }

@app.put("/bugs/{bug_id}", response_model=BugResponse)
def update_bug(bug_id: int, bug_update: BugUpdate):
    """Update an existing bug."""
    bug = next((b for b in bugs if b['id'] == bug_id), None)
    if not bug:
        raise HTTPException(status_code=404, detail=f"Bug not found with ID: {bug_id}")
    
    updated_fields = []
    
    if bug_update.status is not None:
        if bug_update.status not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status. Allowed values: {VALID_STATUSES}")
        bug['status'] = bug_update.status
        updated_fields.append('status')
    
    if bug_update.resolution is not None:
        bug['resolution'] = bug_update.resolution
        updated_fields.append('resolution')
    
    if updated_fields:
        save_bugs()
        return {
            'status': 'success',
            'message': f'Updated bug {bug_id}',
            'bug_id': bug_id
        }
    else:
        return {
            'status': 'success',
            'message': 'No changes made',
            'bug_id': bug_id
        }

@app.delete("/bugs/{bug_id}", response_model=BugResponse)
def delete_bug(bug_id: int):
    """Delete a bug."""
    global bugs
    original_length = len(bugs)
    bugs = [b for b in bugs if b['id'] != bug_id]
    
    if original_length > len(bugs):
        save_bugs()
        return {
            'status': 'success',
            'message': f'Deleted bug {bug_id}',
            'bug_id': bug_id
        }
    else:
        raise HTTPException(status_code=404, detail=f"Bug not found with ID: {bug_id}")

@app.get("/bugs/{bug_id}", response_model=BugGetResponse)
def get_bug(bug_id: int):
    """Get a specific bug."""
    bug = next((b for b in bugs if b['id'] == bug_id), None)
    
    if bug:
        return {
            'status': 'success',
            'bug': bug
        }
    else:
        raise HTTPException(status_code=404, detail=f"Bug not found with ID: {bug_id}")

@app.get("/bugs", response_model=BugListResponse)
def list_bugs():
    """List all bugs."""
    return {
        'status': 'success',
        'total_records': len(bugs),
        'bugs': bugs
    }

def main():
    """Main function to start the API server."""
    import argparse
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Start the Bug Tracking API server")
    parser.add_argument("--port", type=int, default=5005, help="Server port")
    parser.add_argument("--host", type=str, default="localhost", help="Server host")
    parser.add_argument("--log-level", type=str, default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Logging level")
    args = parser.parse_args()
    
    # Set logging level
    logger.setLevel(getattr(logging, args.log_level))
    
    # Start the server
    logger.info(f"Starting Bug Tracking API server on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()