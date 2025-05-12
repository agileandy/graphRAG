#!/usr/bin/env python3
"""
GraphRAG Service Monitor

This script monitors the GraphRAG services and restarts them if they crash.
It can be run as a cron job or as a daemon.
"""
import os
import sys
import time
import logging
import subprocess
import psutil

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
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load configuration
def load_config():
    """Load configuration from environment file."""
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    config[key] = value
    return config

config = load_config()

# Service definitions
SERVICES = [
    {
        'name': 'neo4j',
        'pid_file': os.path.join(PID_DIR, 'neo4j.pid'),
        'check_url': 'http://localhost:7474',
        'start_cmd': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'graphrag-service.sh') + ' start-neo4j'
    },
    {
        'name': 'api',
        'pid_file': os.path.join(PID_DIR, 'api.pid'),
        'check_url': f"http://localhost:{config.get('GRAPHRAG_API_PORT', '5000')}/health",
        'start_cmd': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'graphrag-service.sh') + ' start-api'
    },
    {
        'name': 'mpc',
        'pid_file': os.path.join(PID_DIR, 'mpc.pid'),
        'start_cmd': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'graphrag-service.sh') + ' start-mpc'
    }
]

def check_service(service):
    """Check if a service is running and restart it if necessary."""
    name = service['name']
    pid_file = service['pid_file']
    
    # Check if PID file exists
    if not os.path.exists(pid_file):
        logging.warning(f"{name} service is not running (no PID file)")
        return False
    
    # Read PID from file
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
    except (IOError, ValueError) as e:
        logging.error(f"Error reading PID file for {name}: {e}")
        return False
    
    # Check if process is running
    try:
        process = psutil.Process(pid)
        if process.is_running():
            # Additional check for HTTP services
            if 'check_url' in service:
                try:
                    result = subprocess.run(
                        ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', service['check_url']],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.stdout.strip() != '200':
                        logging.warning(f"{name} service is not responding properly (HTTP {result.stdout.strip()})")
                        return False
                except subprocess.SubprocessError as e:
                    logging.warning(f"Error checking {name} service URL: {e}")
                    return False
            
            # Service is running
            return True
        else:
            logging.warning(f"{name} service is not running (PID {pid} not found)")
            return False
    except psutil.NoSuchProcess:
        logging.warning(f"{name} service is not running (PID {pid} not found)")
        return False

def restart_service(service):
    """Restart a service."""
    name = service['name']
    pid_file = service['pid_file']
    start_cmd = service['start_cmd']
    
    logging.info(f"Restarting {name} service...")
    
    # Remove PID file if it exists
    if os.path.exists(pid_file):
        os.remove(pid_file)
    
    # Start service
    try:
        result = subprocess.run(
            start_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
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

def monitor_services():
    """Monitor all services and restart them if necessary."""
    for service in SERVICES:
        if not check_service(service):
            restart_service(service)

def collect_resource_usage():
    """Collect resource usage information."""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    logging.info(f"Resource Usage - CPU: {cpu_percent}%, Memory: {memory.percent}%, Disk: {disk.percent}%")

def main():
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
