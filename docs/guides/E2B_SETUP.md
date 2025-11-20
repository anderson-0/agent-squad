# E2B Sandbox Setup Guide

## Overview

Agent Squad uses **E2B** (https://e2b.dev) for secure, isolated code execution - the same sandboxing technology used by Lovable, Cursor, and other leading AI platforms.

## Why E2B?

✅ **Industry Standard**: Used by top AI platforms  
✅ **Better Security**: Cloud-based isolation (better than local subprocess)  
✅ **No Infrastructure**: No Docker setup required  
✅ **Automatic Scaling**: Handles resource management automatically  
✅ **Pre-installed Packages**: Data science packages ready to use  
✅ **Automatic Cleanup**: Sandboxes destroyed after execution  

## Quick Setup

### 1. Get E2B API Key

1. Sign up at https://e2b.dev
2. Get your API key from the dashboard
3. Set it as an environment variable:

```bash
export E2B_API_KEY="your-api-key-here"
```

### 2. Install E2B SDK

```bash
pip install e2b-code-interpreter
```

### 3. Configure Agent Squad

The E2B API key is automatically picked up from the `E2B_API_KEY` environment variable. No additional configuration needed!

## Configuration

### Environment Variable

```bash
# Required for Python code execution
export E2B_API_KEY="e2b_..."
```

### In Code

```python
from backend.core.config import settings

# E2B API key is available via:
e2b_key = settings.E2B_API_KEY
```

## How It Works

```
Agent Request
    ↓
Python Executor MCP Server
    ↓
E2B Sandbox.create()
    ↓
Isolated Cloud Environment
    ├─ Execute code
    ├─ Install packages
    ├─ Access filesystem
    └─ Network access (controlled)
    ↓
Sandbox.close() (automatic cleanup)
```

## Features

### Automatic Resource Management
- CPU limits: Handled by E2B
- Memory limits: Handled by E2B
- Disk limits: Handled by E2B
- Timeout: Configurable (default: 60s)

### Pre-installed Packages
E2B code interpreter template includes:
- pandas, numpy, scipy
- matplotlib, seaborn
- scikit-learn
- jupyter
- And more data science packages

### Security
- ✅ Isolated cloud environment
- ✅ No access to host system
- ✅ Network access control
- ✅ Automatic cleanup
- ✅ Resource limits enforced

## Usage Examples

### Basic Code Execution

```python
# Agent automatically uses E2B
result = await agent.execute_tool("python_executor", "execute_code", {
    "code": """
import pandas as pd
import numpy as np

df = pd.DataFrame({'x': [1, 2, 3], 'y': [4, 5, 6]})
print(df.describe())
"""
})
```

### Install Package

```python
result = await agent.execute_tool("python_executor", "install_package", {
    "package": "xgboost"
})
```

### Get Environment

```python
result = await agent.execute_tool("python_executor", "get_environment", {})
# Returns: Python version, installed packages, platform info
```

## Pricing

E2B offers:
- **Free Tier**: Limited sandbox hours/month
- **Paid Plans**: Based on sandbox usage
- **Enterprise**: Custom pricing

Check current pricing at https://e2b.dev/pricing

## Troubleshooting

### "E2B_API_KEY not configured"
```bash
# Set the environment variable
export E2B_API_KEY="your-key-here"

# Or add to .env file
echo "E2B_API_KEY=your-key-here" >> .env
```

### "E2B SDK not available"
```bash
pip install e2b-code-interpreter
```

### "Sandbox creation failed"
- Check API key is valid
- Check internet connection
- Check E2B service status
- Review E2B dashboard for errors

### Timeout Issues
Increase timeout in tool call:
```python
result = await agent.execute_tool("python_executor", "execute_code", {
    "code": "...",
    "timeout": 120  # 2 minutes
})
```

## Best Practices

1. **Reuse Sandboxes** (Future Enhancement)
   - Currently creates new sandbox per execution
   - Future: Pool sandboxes for better performance

2. **Monitor Usage**
   - Check E2B dashboard for usage
   - Set up alerts for high usage
   - Optimize code execution time

3. **Error Handling**
   - Always check `success` field in result
   - Handle timeout errors gracefully
   - Log execution errors for debugging

## Comparison: E2B vs Alternatives

| Feature | E2B | Docker | Subprocess |
|---------|-----|--------|------------|
| Setup Complexity | ⭐ Easy | ⭐⭐ Medium | ⭐ Easy |
| Security | ⭐⭐⭐ Excellent | ⭐⭐ Good | ⭐ Basic |
| Resource Management | ⭐⭐⭐ Automatic | ⭐⭐ Manual | ⭐ Manual |
| Scalability | ⭐⭐⭐ Cloud | ⭐⭐ Local | ⭐ Local |
| Cost | ⭐⭐ Pay per use | ⭐ Free | ⭐ Free |
| Industry Adoption | ⭐⭐⭐ High | ⭐⭐ Medium | ⭐ Low |

**Recommendation**: E2B is the best choice for production AI platforms.

## Support

- E2B Docs: https://e2b.dev/docs
- E2B Support: support@e2b.dev
- Agent Squad Issues: GitHub Issues


