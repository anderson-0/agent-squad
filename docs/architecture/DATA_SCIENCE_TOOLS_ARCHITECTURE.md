# Data Science Execution Tools Architecture

## Overview

This document describes the architecture for adding execution capabilities to data science and ML agents, enabling them to actually perform data analysis, train models, and execute code rather than just providing recommendations.

## Design Principles

1. **Security First**: All code execution must be sandboxed
2. **Resource Limits**: CPU, memory, and time limits on all executions
3. **Audit Trail**: All executions logged for security and debugging
4. **Isolation**: Each agent execution runs in isolated environment
5. **Graceful Degradation**: Tools fail safely without breaking agents

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Data Science Agent                          │
│  (Data Scientist, ML Engineer, Data Engineer)           │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│              MCP Tool Interface                          │
│  (AgentMCPService)                                       │
└─────────────────────────────────────────────────────────┘
                        ↓
        ┌───────────────┼───────────────┐
        ↓               ↓               ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Python     │ │  Database    │ │   File       │
│  Executor    │ │   Access     │ │   Storage    │
│  MCP Server  │ │  MCP Server  │ │  MCP Server  │
└──────────────┘ └──────────────┘ └──────────────┘
        ↓               ↓               ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Sandboxed   │ │   Database    │ │   S3/Local   │
│  Execution   │ │   Connection  │ │   Storage    │
│  Container   │ │   Pool        │ │   Access     │
└──────────────┘ └──────────────┘ └──────────────┘
```

## MCP Servers to Implement

### 1. Python Executor MCP Server ⭐ E2B Sandboxing
**Purpose**: Execute Python code safely with E2B cloud sandboxes

**Tools**:
- `execute_code`: Run Python code in isolated E2B sandbox
- `install_package`: Install Python packages in sandbox
- `run_script`: Execute Python script file in sandbox
- `get_environment`: Get Python environment info from sandbox

**Security** (via E2B):
- ✅ Cloud-based isolated sandboxes (same as Lovable, Cursor, etc.)
- ✅ Automatic resource limits (CPU, memory, disk)
- ✅ Network access control
- ✅ File system isolation
- ✅ Timeout limits (default: 60 seconds)
- ✅ Pre-installed data science packages
- ✅ Automatic cleanup after execution

**Implementation**:
- Uses E2B (https://e2b.dev) cloud sandboxes
- Python SDK: `e2b-code-interpreter`
- Each execution gets fresh isolated environment
- Sandbox automatically destroyed after use
- No local resource management needed

### 2. Database Access MCP Server
**Purpose**: Execute SQL queries safely

**Tools**:
- `execute_query`: Run SELECT queries
- `get_schema`: Get table schemas
- `list_tables`: List available tables
- `get_table_sample`: Get sample rows (limited)
- `describe_table`: Get table metadata

**Security**:
- Read-only access by default
- Query timeout (default: 30 seconds)
- Row limit (default: 10,000 rows)
- Query whitelist/blacklist patterns
- Connection pooling with limits

**Implementation**:
- Use SQLAlchemy for database connections
- Support PostgreSQL, MySQL, SQLite
- Connection string from environment/config
- Query result size limits

### 3. File Storage MCP Server
**Purpose**: Access data files (CSV, Parquet, JSON, etc.)

**Tools**:
- `read_file`: Read file (with size limits)
- `list_files`: List files in directory/bucket
- `write_file`: Write file (with approval)
- `read_parquet`: Read Parquet file (optimized)
- `read_csv`: Read CSV file (with chunking)

**Security**:
- Path restrictions (whitelist directories)
- File size limits (default: 100MB)
- Read-only by default
- Write operations require explicit permission

**Implementation**:
- Support local filesystem
- Support S3 (via boto3)
- Support GCS (via google-cloud-storage)
- Automatic format detection

### 4. Jupyter Notebook MCP Server (Future)
**Purpose**: Create and execute Jupyter notebooks

**Tools**:
- `create_notebook`: Create new notebook
- `execute_cell`: Execute notebook cell
- `get_notebook`: Get notebook content
- `save_notebook`: Save notebook

### 5. MLflow Integration MCP Server (Future)
**Purpose**: Track experiments and manage models

**Tools**:
- `log_experiment`: Log ML experiment
- `log_model`: Log trained model
- `load_model`: Load model from registry
- `search_experiments`: Search experiments

## Security Model

### Sandboxing Strategy

**✅ E2B Cloud Sandboxes (Implemented)**
- Cloud-based isolated sandboxes (same as Lovable, Cursor, etc.)
- Automatic resource limits (CPU, memory, disk)
- Network access control
- File system isolation
- Automatic cleanup after execution
- Pre-installed data science packages
- No local infrastructure needed
- Get API key at https://e2b.dev

**Why E2B?**
- Industry standard (used by Lovable, Cursor, and other AI platforms)
- Better security than local subprocess
- No Docker setup required
- Automatic resource management
- Scales automatically

### Resource Limits

```yaml
python_executor:
  e2b_api_key: "${E2B_API_KEY}"  # Required: Get from https://e2b.dev
  timeout: 60  # seconds (default)
  template_id: "base"  # E2B template (code interpreter)
  # Resource limits handled automatically by E2B

database:
  query_timeout: 30  # seconds
  max_rows: 10000
  read_only: true
  max_connections: 5

file_storage:
  max_file_size: 100MB
  allowed_paths: ["/data", "/tmp/agent-data"]
  read_only: true  # by default
```

### Audit Logging

All executions logged:
- Agent ID and role
- Tool called
- Input parameters (sanitized)
- Execution time
- Success/failure
- Error messages (if any)
- Resource usage

## Configuration

### MCP Tool Mapping Update

```yaml
data_scientist:
  mcp_servers:
    - python_executor
    - database
    - file_storage
  tools:
    python_executor:
      - execute_code
      - install_package
      - run_script
    database:
      - execute_query
      - get_schema
      - list_tables
      - get_table_sample
    file_storage:
      - read_file
      - read_parquet
      - read_csv
      - list_files

ml_engineer:
  mcp_servers:
    - python_executor
    - database
    - file_storage
    - mlflow  # future
  tools:
    python_executor:
      - execute_code
      - install_package
    database:
      - execute_query
    file_storage:
      - read_file
      - write_file  # with approval

data_engineer:
  mcp_servers:
    - python_executor
    - database
    - file_storage
  tools:
    python_executor:
      - execute_code
      - run_script
    database:
      - execute_query
      - get_schema
      - list_tables
    file_storage:
      - read_file
      - write_file
      - list_files
```

## Implementation Phases

### Phase 1: Core Execution (Week 1) ✅
- [x] Python Executor MCP Server with E2B sandboxing
- [x] E2B cloud sandboxes (industry-standard security)
- [x] Database Access MCP Server (read-only)
- [x] File Storage MCP Server (read-only)
- [x] Update MCP tool mapping

### Phase 2: Enhanced Security (Week 2)
- [x] E2B sandboxing (better than Docker for this use case)
- [ ] Enhanced audit logging system
- [ ] Security testing
- [ ] Sandbox pooling for performance

### Phase 3: Advanced Features (Week 3-4)
- [ ] Jupyter Notebook integration
- [ ] MLflow integration
- [ ] Write permissions (with approval)
- [ ] Performance optimization

## Usage Examples

### Data Scientist: Exploratory Data Analysis

```python
# Agent calls: database.execute_query
query = "SELECT * FROM user_behavior LIMIT 1000"
result = await agent.execute_tool("database", "execute_query", {"query": query})

# Agent calls: python_executor.execute_code
code = """
import pandas as pd
import matplotlib.pyplot as plt

df = pd.DataFrame(result)
df.describe()
"""
analysis = await agent.execute_tool("python_executor", "execute_code", {"code": code})
```

### ML Engineer: Train Model

```python
# Agent calls: file_storage.read_parquet
data = await agent.execute_tool("file_storage", "read_parquet", {
    "path": "s3://bucket/training_data.parquet"
})

# Agent calls: python_executor.execute_code
code = """
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X, y)
model = RandomForestClassifier()
model.fit(X_train, y_train)
accuracy = model.score(X_test, y_test)
"""
result = await agent.execute_tool("python_executor", "execute_code", {"code": code})
```

## Testing Strategy

1. **Unit Tests**: Test each tool independently
2. **Integration Tests**: Test agent → tool → execution flow
3. **Security Tests**: Test sandboxing and limits
4. **Performance Tests**: Test resource usage
5. **End-to-End Tests**: Full data science workflow

## Monitoring

- Execution success/failure rates
- Average execution time
- Resource usage (CPU, memory)
- Error rates by tool
- Security violations
- Agent tool usage patterns

