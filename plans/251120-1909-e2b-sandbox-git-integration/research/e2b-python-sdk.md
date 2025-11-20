# E2B Python SDK Implementation Patterns

## 1. SDK Installation and Setup

### Installation
```bash
pip install e2b-code-interpreter
```

### Authentication
- Obtain API key from E2B platform
- Set environment variable: `E2B_API_KEY=e2b_***`

## 2. Sandbox Lifecycle Management

### Creating a Sandbox
```python
from e2b_code_interpreter import Sandbox

# Basic sandbox creation
sandbox = Sandbox.create()

# With optional parameters
sandbox = Sandbox.create(
    template='optional_template',
    timeout=3600,  # seconds
    metadata={},
    envs={'MY_VAR': 'value'}
)
```

### Connecting to Existing Sandbox
```python
# Save sandbox ID when creating
sandbox_id = sandbox.sandbox_id

# Connect to same sandbox later
same_sandbox = Sandbox.connect(sandbox_id)
```

### Destroying Sandbox
```python
# Directly kill a sandbox
sandbox.kill()

# Or kill by sandbox ID
Sandbox.kill(sandbox_id)
```

## 3. Code Execution Methods

### Running Python Code
```python
with Sandbox.create() as sandbox:
    # Simple code execution
    sandbox.run_code("x = 1")
    execution = sandbox.run_code("x+=1; x")
    print(execution.text)  # outputs: 2
```

### Terminal Commands
```python
# Run command and wait for completion
result = sandbox.commands.run("ls -l")

# Get command handle for interaction
cmd_handle = sandbox.commands.run("long_running_process", wait=False)
cmd_handle.wait()  # Optional wait
```

### File Operations
```python
# Write file
sandbox.filesystem.write("/path/to/file.txt", "file contents")

# Read file
content = sandbox.filesystem.read("/path/to/file.txt")

# List files
files = sandbox.filesystem.list("/directory")
```

## 4. Environment & Secret Management

### Passing Environment Variables
```python
# When creating sandbox
sandbox = Sandbox.create(
    envs={
        'SECRET_KEY': 'your_secret_key',
        'DATABASE_URL': 'your_connection_string'
    }
)
```

### Async Integration
```python
from e2b_code_interpreter import AsyncSandbox

async def execute_in_sandbox():
    async with AsyncSandbox.create() as sandbox:
        result = await sandbox.run_code("async def test(): return 42")
        print(result.text)
```

## 5. Best Practices

- Always use context managers (`with` statement) to ensure sandbox cleanup
- Store sensitive information in environment variables
- Use async methods for non-blocking operations
- Set appropriate timeouts for long-running tasks
- Utilize `sandbox.commands.list()` to monitor active processes

## Unresolved Questions

1. How to handle large file transfers between host and sandbox?
2. What are the network access limitations in sandbox?
3. Can custom Docker images be used as sandbox templates?