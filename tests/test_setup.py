#!/usr/bin/env python3
"""
Test environment setup for GraphRAG.

This script sets up the test environment for GraphRAG by:
1. Checking port availability
2. Starting required services
3. Verifying service health
4. Providing a clean shutdown mechanism
"""
import os
import sys
import time
import signal
import argparse
import subprocess
import logging
from typing import Dict, List, Optional, Tuple

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import port configuration
try:
    from src.config.ports import (
        get_port,
        is_port_in_use,
        find_available_port,
        get_service_for_port,
        check_port_conflicts,
        print_port_configuration
    )
except ImportError:
    print("Error: Could not import port configuration. Make sure src/config/ports.py exists.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_setup')

# Global variables
processes = {}
original_ports = {}
actual_ports = {}

def signal_handler(sig, frame):
    """Handle signals to ensure clean shutdown."""
    logger.info("Shutting down services...")
    stop_all_services()
    sys.exit(0)

def start_service(service_name: str, command: List[str], 
                 check_ready_func: Optional[callable] = None,
                 timeout: int = 30) -> Tuple[bool, Optional[subprocess.Popen]]:
    """
    Start a service and wait for it to be ready.
    
    Args:
        service_name: Name of the service
        command: Command to start the service
        check_ready_func: Function to check if the service is ready
        timeout: Timeout in seconds
        
    Returns:
        Tuple of (success, process)
    """
    logger.info(f"Starting {service_name}...")
    
    try:
        # Get the port for this service
        port = get_port(service_name)
        original_ports[service_name] = port
        
        # Check if port is in use
        if is_port_in_use(port):
            service = get_service_for_port(port)
            if service and service != service_name:
                logger.warning(f"Port {port} is already in use by {service}")
            else:
                logger.warning(f"Port {port} is already in use")
            
            # Find an available port
            new_port = find_available_port(port + 1)
            logger.info(f"Using alternative port {new_port} for {service_name}")
            
            # Update command with new port
            for i, arg in enumerate(command):
                if arg == str(port):
                    command[i] = str(new_port)
                elif f"--port={port}" in arg:
                    command[i] = f"--port={new_port}"
                elif f"--port {port}" in ' '.join(command[i:i+2]):
                    if arg == "--port":
                        command[i+1] = str(new_port)
            
            # Store the actual port used
            actual_ports[service_name] = new_port
        else:
            actual_ports[service_name] = port
        
        # Start the process
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Store the process
        processes[service_name] = process
        
        # Wait for the service to be ready
        if check_ready_func:
            logger.info(f"Waiting for {service_name} to be ready...")
            start_time = time.time()
            while time.time() - start_time < timeout:
                if check_ready_func(actual_ports[service_name]):
                    logger.info(f"{service_name} is ready")
                    return True, process
                time.sleep(1)
            
            logger.error(f"{service_name} failed to start within {timeout} seconds")
            stop_service(service_name)
            return False, None
        
        # If no check function, assume it's ready
        logger.info(f"{service_name} started (no readiness check)")
        return True, process
    
    except Exception as e:
        logger.error(f"Error starting {service_name}: {e}")
        return False, None

def stop_service(service_name: str) -> bool:
    """
    Stop a service.
    
    Args:
        service_name: Name of the service
        
    Returns:
        True if successful, False otherwise
    """
    if service_name not in processes:
        logger.warning(f"{service_name} is not running")
        return False
    
    logger.info(f"Stopping {service_name}...")
    
    try:
        process = processes[service_name]
        process.terminate()
        
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            logger.warning(f"{service_name} did not terminate gracefully, killing...")
            process.kill()
        
        del processes[service_name]
        logger.info(f"{service_name} stopped")
        return True
    
    except Exception as e:
        logger.error(f"Error stopping {service_name}: {e}")
        return False

def stop_all_services():
    """Stop all services."""
    for service_name in list(processes.keys()):
        stop_service(service_name)

def check_neo4j_ready(port: int) -> bool:
    """Check if Neo4j is ready."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect(('localhost', port))
        s.close()
        return True
    except:
        return False

def check_api_ready(port: int) -> bool:
    """Check if the API is ready."""
    import requests
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=1)
        return response.status_code == 200
    except:
        return False

def check_mcp_ready(port: int) -> bool:
    """Check if the MCP server is ready."""
    import websockets
    import asyncio
    import json
    
    async def check_connection():
        try:
            uri = f"ws://localhost:{port}"
            async with websockets.connect(uri, timeout=1) as websocket:
                await websocket.send(json.dumps({
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {
                            "name": "test-client",
                            "version": "0.1.0"
                        }
                    },
                    "id": 0
                }))
                
                response = await websocket.recv()
                return "result" in json.loads(response)
        except:
            return False
    
    try:
        return asyncio.run(check_connection())
    except:
        return False

def check_mpc_ready(port: int) -> bool:
    """Check if the MPC server is ready."""
    import websockets
    import asyncio
    import json
    
    async def check_connection():
        try:
            uri = f"ws://localhost:{port}"
            async with websockets.connect(uri, timeout=1) as websocket:
                await websocket.send(json.dumps({"action": "ping"}))
                response = await websocket.recv()
                return True
        except:
            return False
    
    try:
        return asyncio.run(check_connection())
    except:
        return False

def setup_test_environment():
    """Set up the test environment."""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check for port conflicts
    conflicts = check_port_conflicts()
    if conflicts:
        logger.warning("Port conflicts detected:")
        for service, port in conflicts:
            logger.warning(f"  {service}: {port}")
    
    # Start Neo4j
    neo4j_success, _ = start_service(
        "neo4j_bolt",
        ["./scripts/service_management/graphrag-service.sh", "start-neo4j"],
        check_neo4j_ready
    )
    
    if not neo4j_success:
        logger.error("Failed to start Neo4j, aborting")
        stop_all_services()
        return False
    
    # Start API server
    api_success, _ = start_service(
        "api",
        ["./scripts/service_management/graphrag-service.sh", "start-api"],
        check_api_ready
    )
    
    if not api_success:
        logger.error("Failed to start API server, aborting")
        stop_all_services()
        return False
    
    # Start MCP server
    mcp_success, _ = start_service(
        "mcp",
        [".venv-py312/bin/python", "-m", "src.mpc.mcp_server", "--host", "0.0.0.0", "--port", str(get_port("mcp"))],
        check_mcp_ready
    )
    
    if not mcp_success:
        logger.warning("Failed to start MCP server, continuing anyway")
    
    # Start MPC server
    mpc_success, _ = start_service(
        "mpc",
        [".venv-py312/bin/python", "src/mpc/server.py", "--host", "0.0.0.0", "--port", str(get_port("mpc"))],
        check_mpc_ready
    )
    
    if not mpc_success:
        logger.warning("Failed to start MPC server, continuing anyway")
    
    # Print port configuration
    logger.info("Test environment set up with the following ports:")
    for service, port in actual_ports.items():
        original = original_ports.get(service)
        if original != port:
            logger.info(f"  {service}: {port} (originally {original})")
        else:
            logger.info(f"  {service}: {port}")
    
    return True

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Test environment setup for GraphRAG')
    parser.add_argument('--start', action='store_true', help='Start the test environment')
    parser.add_argument('--stop', action='store_true', help='Stop the test environment')
    parser.add_argument('--status', action='store_true', help='Show the status of the test environment')
    
    args = parser.parse_args()
    
    if args.start:
        if setup_test_environment():
            logger.info("Test environment set up successfully")
            logger.info("Press Ctrl+C to stop")
            
            # Keep the script running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                stop_all_services()
    
    elif args.stop:
        stop_all_services()
        logger.info("Test environment stopped")
    
    elif args.status:
        print_port_configuration()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
