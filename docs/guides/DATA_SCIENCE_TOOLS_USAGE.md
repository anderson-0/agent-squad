# Data Science Execution Tools - Usage Guide

## Overview

Data science and ML agents now have execution capabilities! They can:
- ✅ Execute Python code
- ✅ Query databases
- ✅ Read/write data files
- ✅ Install packages
- ✅ Run scripts

## Quick Start

### 1. Get E2B API Key (Required for Code Execution)

```bash
# Sign up at https://e2b.dev and get your API key
export E2B_API_KEY="your-e2b-api-key"
```

### 2. Configure Environment Variables

```bash
# E2B (required for Python code execution)
export E2B_API_KEY="e2b_..."

# Database access (optional)
export DATABASE_URL="postgresql://user:pass@localhost/dbname"

# S3 access (optional)
export S3_BUCKET="my-data-bucket"
export S3_REGION="us-east-1"
```

### 3. Install Dependencies

```bash
# Required for Python code execution (E2B)
pip install e2b-code-interpreter

# Required for database access
pip install sqlalchemy

# Required for file operations
pip install pandas pyarrow

# Optional for S3
pip install boto3
```

### 3. Agents Automatically Get Access

When you create a data scientist, ML engineer, or data engineer agent, they automatically have access to these tools via MCP.

## Available Tools

### Python Executor (E2B Sandboxes)

**Tools:**
- `execute_code`: Run Python code in isolated E2B cloud sandbox
- `install_package`: Install Python packages in sandbox
- `run_script`: Execute Python script files in sandbox
- `get_environment`: Get Python environment info from sandbox

**Example Usage:**
```python
# Agent can now do:
result = await agent.execute_tool("python_executor", "execute_code", {
    "code": """
import pandas as pd
import numpy as np

df = pd.DataFrame({'x': [1, 2, 3], 'y': [4, 5, 6]})
print(df.describe())
"""
})
```

**Security (via E2B):**
- ✅ Cloud-based isolated sandboxes (same as Lovable, Cursor, etc.)
- ✅ Automatic resource limits (CPU, memory, disk)
- ✅ Timeout: 60 seconds (default, configurable)
- ✅ Network access control
- ✅ Pre-installed data science packages
- ✅ Automatic cleanup after execution

### Database Access

**Tools:**
- `execute_query`: Run SELECT queries (read-only)
- `get_schema`: Get table schema
- `list_tables`: List all tables
- `get_table_sample`: Get sample rows
- `describe_table`: Get table metadata

**Example Usage:**
```python
# Agent can now do:
result = await agent.execute_tool("database", "execute_query", {
    "query": "SELECT * FROM users LIMIT 100",
    "timeout": 30,
    "max_rows": 10000
})
```

**Security:**
- Read-only mode enforced
- Query timeout: 30 seconds (default)
- Row limit: 10,000 rows (default)
- Only SELECT queries allowed

### File Storage

**Tools:**
- `read_file`: Read text files
- `read_csv`: Read CSV files
- `read_parquet`: Read Parquet files
- `list_files`: List files in directory
- `write_file`: Write files (data engineers/ML engineers only)

**Example Usage:**
```python
# Agent can now do:
result = await agent.execute_tool("file_storage", "read_parquet", {
    "file_path": "s3://bucket/data.parquet",
    "n_rows": 1000
})
```

**Security:**
- File size limit: 100MB (default)
- Path restrictions: Only allowed directories
- Read-only by default (except data engineers/ML engineers)

## Agent Capabilities

### Data Scientist
- ✅ Execute Python code
- ✅ Install packages
- ✅ Query databases
- ✅ Read data files (CSV, Parquet)
- ✅ List files
- ❌ Write files (read-only)

### Data Engineer
- ✅ Execute Python code
- ✅ Run scripts
- ✅ Query databases
- ✅ Read/write data files
- ✅ List files

### ML Engineer
- ✅ Execute Python code
- ✅ Install packages
- ✅ Query databases
- ✅ Read/write data files
- ✅ List files

## Example Workflows

### 1. Exploratory Data Analysis

```python
# Data Scientist workflow:
# 1. Request data from database
data = await agent.execute_tool("database", "execute_query", {
    "query": "SELECT * FROM user_behavior LIMIT 10000"
})

# 2. Analyze with Python
analysis = await agent.execute_tool("python_executor", "execute_code", {
    "code": f"""
import pandas as pd
import json

df = pd.DataFrame({data['rows']})
print(df.describe())
print(df.info())
"""
})
```

### 2. Model Training

```python
# ML Engineer workflow:
# 1. Load training data
data = await agent.execute_tool("file_storage", "read_parquet", {
    "file_path": "s3://bucket/training_data.parquet"
})

# 2. Train model
result = await agent.execute_tool("python_executor", "execute_code", {
    "code": """
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import pandas as pd

# Load data
df = pd.DataFrame(data['data'])

# Train model
X = df.drop('target', axis=1)
y = df['target']
X_train, X_test, y_train, y_test = train_test_split(X, y)

model = RandomForestClassifier()
model.fit(X_train, y_train)
accuracy = model.score(X_test, y_test)

print(f"Accuracy: {accuracy}")
"""
})
```

### 3. Data Pipeline

```python
# Data Engineer workflow:
# 1. Query source database
source_data = await agent.execute_tool("database", "execute_query", {
    "query": "SELECT * FROM raw_logs WHERE date >= '2024-01-01'"
})

# 2. Process and save
await agent.execute_tool("python_executor", "execute_code", {
    "code": f"""
import pandas as pd
import json

df = pd.DataFrame({source_data['rows']})
# Process data...
processed = df.groupby('user_id').agg({{'value': 'sum'}})

# Save to file
processed.to_parquet('/tmp/processed_data.parquet')
"""
})

# 3. Write to storage
await agent.execute_tool("file_storage", "write_file", {
    "file_path": "s3://bucket/processed_data.parquet",
    "content": open('/tmp/processed_data.parquet', 'rb').read()
})
```

## Security Considerations

### Current Security Features

1. **Code Execution:**
   - Timeout limits (60s default)
   - Memory limits (2GB default)
   - No network access by default
   - Resource limits via `resource` module

2. **Database Access:**
   - Read-only mode enforced
   - Query validation (SELECT only)
   - Row limits (10,000 default)
   - Connection pooling with limits

3. **File Access:**
   - Path whitelisting
   - File size limits (100MB default)
   - Read-only by default
   - S3 access requires credentials

### Recommended Enhancements

For production, consider:
- Docker-based sandboxing (more secure)
- Enhanced resource limits
- Audit logging
- Query whitelisting/blacklisting
- File access approval workflow

## Troubleshooting

### "MCP SDK not available"
Install the MCP SDK:
```bash
pip install mcp
```

### "Database not configured"
Set the `DATABASE_URL` environment variable:
```bash
export DATABASE_URL="postgresql://user:pass@localhost/dbname"
```

### "Path not allowed"
Configure allowed paths in the file storage server config, or use paths in `/tmp/agent-data`.

### "Query timeout"
Increase timeout or optimize query:
```python
await agent.execute_tool("database", "execute_query", {
    "query": "...",
    "timeout": 60  # Increase timeout
})
```

## Next Steps

1. **Test with a Data Scientist Agent:**
   ```python
   # Create agent
   agent = AgentFactory.create_agent(
       agent_id=uuid4(),
       role="data_scientist",
       llm_provider="openai",
       llm_model="gpt-4"
   )
   
   # Agent can now use tools!
   result = await agent.process_message(
       "Analyze the user_behavior table and provide insights"
   )
   ```

2. **Configure Security:**
   - Review resource limits
   - Set up path restrictions
   - Configure database read-only user

3. **Monitor Usage:**
   - Check execution logs
   - Monitor resource usage
   - Review tool execution history

## Support

For issues or questions:
- Check logs: `backend/logs/`
- Review architecture: `docs/architecture/DATA_SCIENCE_TOOLS_ARCHITECTURE.md`
- File issues on GitHub

