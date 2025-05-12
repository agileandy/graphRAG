# Updating Port References

This document provides guidance on updating hardcoded port references to use the centralized port configuration.

## Finding Hardcoded Port References

Use the `scripts/update_port_references.py` script to find hardcoded port references in the codebase:

```bash
python scripts/update_port_references.py
```

This script will scan the codebase for hardcoded port numbers and suggest replacements using the centralized port configuration.

## Manual Updates

For each hardcoded port reference, you'll need to update the code to use the `get_port()` function. Here are some common patterns and their replacements:

### Python Files

#### Before:
```python
port = 8765
```

#### After:
```python
from src.config import get_port
port = get_port('mpc')
```

### Shell Scripts

#### Before:
```bash
PORT=8765
```

#### After:
```bash
# Option 1: Source the .env file
source .env
PORT=$GRAPHRAG_PORT_MPC

# Option 2: Use Python to get the port
PORT=$(python -c "from src.config import get_port; print(get_port('mpc'))")
```

### Configuration Files

#### Before:
```json
{
  "port": 8765
}
```

#### After:
```json
{
  "port": "${GRAPHRAG_PORT_MPC}"
}
```

## Testing Changes

After updating port references, test the affected components to ensure they still work correctly:

1. Run the component with the updated port configuration
2. Verify that it uses the correct port
3. Test overriding the port through environment variables

## Common Issues

### Import Errors

If you encounter import errors when adding `from src.config import get_port`, you may need to adjust the import path based on the file's location in the project structure.

### Environment Variable Access

In some contexts (e.g., Docker containers), environment variables may not be accessible. In these cases, you may need to pass the port values explicitly or use a different configuration approach.

### Port Conflicts

If you encounter port conflicts after updating to the centralized configuration, you can:

1. Override the conflicting ports in the `.env` file
2. Use the `find_available_port()` function to dynamically find an available port
3. Update the default port values in `src/config/ports.py`