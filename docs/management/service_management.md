# Service Management

This document explains how to manage GraphRAG services using the [`scripts/service_management/graphrag-service.sh`](scripts/service_management/graphrag-service.sh) script.

## Available Commands

### Start Services
```bash
./scripts/service_management/graphrag-service.sh start
```
Starts all GraphRAG services:
- API Server (Gunicorn)
- MPC Server
- MCP Server

### Stop Services
```bash
./scripts/service_management/graphrag-service.sh stop
```
Stops all GraphRAG services using `pkill` with the following patterns:
- `gunicorn.*src.api.server:app`
- `python.*src.mpc.server`
- `python.*src.mcp.server`

### Check Service Status
```bash
./scripts/service_management/graphrag-service.sh status
```
Checks if each service process is running and reports its status.

## Troubleshooting

### Services Not Starting
1. Check if required ports are available:
   ```bash
   python -c "from src.config.ports import print_port_configuration; print_port_configuration()"
   ```
2. Verify environment variables are set correctly (see [`config/env.sample`](config/env.sample))
3. Check log files:
   - `api_server.log`
   - `mpc_server.log`
   - `mcp_server.log`

### Services Not Stopping
1. Manually check for running processes:
   ```bash
   pgrep -f "gunicorn.*src.api.server:app"
   pgrep -f "python.*src.mpc.server"
   pgrep -f "python.*src.mcp.server"
   ```
2. Force stop processes:
   ```bash
   pkill -9 -f "gunicorn.*src.api.server:app"
   pkill -9 -f "python.*src.mpc.server"
   pkill -9 -f "python.*src.mcp.server"
   ```

### Service Status Inaccurate
If the status command reports incorrect information:
1. Verify the process patterns in [`scripts/service_management/graphrag-service.sh`](scripts/service_management/graphrag-service.sh) match your actual service commands
2. Check if processes are running under different patterns