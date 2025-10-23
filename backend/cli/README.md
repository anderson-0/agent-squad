# Agent Squad CLI Tools

Command-line tools for managing squads, templates, and monitoring agent communication.

## Available Tools

### 1. Apply Template (`apply_template.py`)
Quickly create squads from pre-built templates with agents and routing rules.

```bash
# List available templates
python -m backend.cli.apply_template --list

# Create a development squad
python -m backend.cli.apply_template \
  --user-email user@example.com \
  --template software-dev-squad \
  --squad-name "Alpha Team"
```

### 2. Create Demo Squad (`create_demo_squad.py`)
Create a simple demo squad for testing.

```bash
python -m backend.cli.create_demo_squad \
  --user-email user@example.com \
  --squad-name "Test Squad"
```

### 3. Stream Agent Messages (`stream_agent_messages.py`)
Real-time visualization of agent-to-agent communication.

```bash
python -m backend.cli.stream_agent_messages \
  --execution-id abc-123 \
  --filter-role backend_developer
```

## Features

### Template Application
- 🚀 **Quick Setup**: Create complete squads in seconds
- 📋 **Pre-configured**: Templates include agents and routing rules
- 🎨 **Customizable**: Override template settings as needed
- 📊 **Clear Output**: Beautiful formatting showing all created resources

### Message Streaming
- 🎨 **Color-Coded Agents**: Different color for each agent role
- 🎯 **Message Type Icons**: Visual indicators for different message types
- 🔍 **Filters**: Filter by agent role or message type
- 📊 **Live Statistics**: Real-time stats on message activity
- 🐛 **Debug Mode**: View raw JSON for debugging
- ⚡ **Real-Time**: See messages as they happen
- 🎭 **Beautiful UI**: Rich terminal formatting with boxes and panels

## Installation

```bash
# Install required dependencies
pip install sseclient-py rich click requests

# Or add to your requirements.txt
sseclient-py==1.8.0
rich==13.7.0
click==8.1.7
requests==2.31.0
```

## Apply Template Tool

The `apply_template` CLI is the fastest way to create production-ready squads.

### List Available Templates

```bash
python -m backend.cli.apply_template --list
```

Output:
```
================================================================================
                           📋 AVAILABLE SQUAD TEMPLATES
================================================================================

⭐ Software Development Squad
    Slug: software-dev-squad
    Category: development
    Description: Complete development team with PM, developers, architects, and QA
    Used: 20 times
    Contains: 6 agents, 17 routing rules
    Roles: project_manager, solution_architect, tech_lead, backend_developer,
           frontend_developer, qa_tester

================================================================================
Total: 1 template(s)
💡 Tip: Use --template <slug> to apply a template
```

### Create Squad from Template

```bash
python -m backend.cli.apply_template \
  --user-email demo@test.com \
  --template software-dev-squad \
  --squad-name "Alpha Development Team" \
  --description "Main product development team"
```

This creates:
- ✅ 1 Squad
- ✅ 6 Agents (PM, Architect, Tech Lead, Backend Dev, Frontend Dev, QA)
- ✅ 17 Routing Rules (complete escalation hierarchy)

### Options

```
Options:
  -l, --list                  List all available templates
  -u, --user-email TEXT       Email of the user who will own the squad
  -t, --template TEXT         Template slug (e.g., 'software-dev-squad')
  -n, --squad-name TEXT       Name for the new squad
  -d, --description TEXT      Description for the squad (optional)
  --help                      Show help message
```

### Examples

```bash
# List templates
python -m backend.cli.apply_template --list

# Create dev squad with short flags
python -m backend.cli.apply_template \
  -u user@example.com \
  -t software-dev-squad \
  -n "Team Alpha"

# Create with full description
python -m backend.cli.apply_template \
  --user-email user@example.com \
  --template software-dev-squad \
  --squad-name "Backend Services Team" \
  --description "Team responsible for core API services"
```

## Quick Start (Message Streaming)

### 1. Get Your Auth Token

First, authenticate with the backend and get your JWT token:

```bash
# Login and get token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "your@email.com", "password": "yourpassword"}'

# Save the token
export AGENT_SQUAD_TOKEN="your_jwt_token_here"
```

### 2. Run the CLI

```bash
# Stream messages for a specific execution
python -m backend.cli.stream_agent_messages --execution-id <execution-uuid>

# Stream all messages in a squad
python -m backend.cli.stream_agent_messages --squad-id <squad-uuid>
```

## Usage Examples

### Basic Usage

```bash
# Stream execution messages
python -m backend.cli.stream_agent_messages \
  --execution-id abc-123-def-456 \
  --token your_token_here

# Or use environment variable for token
export AGENT_SQUAD_TOKEN=your_token_here
python -m backend.cli.stream_agent_messages --execution-id abc-123-def-456
```

### With Filters

```bash
# Filter by agent role (only show backend developer messages)
python -m backend.cli.stream_agent_messages \
  --execution-id abc-123 \
  --filter-role backend_developer

# Filter by message type (only show questions)
python -m backend.cli.stream_agent_messages \
  --execution-id abc-123 \
  --filter-type question

# Combine filters
python -m backend.cli.stream_agent_messages \
  --execution-id abc-123 \
  --filter-role tech_lead \
  --filter-type code_review
```

### Debug Mode

```bash
# Show raw JSON for debugging
python -m backend.cli.stream_agent_messages \
  --execution-id abc-123 \
  --debug
```

### Custom Backend URL

```bash
# Connect to a different backend
python -m backend.cli.stream_agent_messages \
  --execution-id abc-123 \
  --base-url https://api.mycompany.com
```

### Limit Message History

```bash
# Keep only last 50 messages in memory
python -m backend.cli.stream_agent_messages \
  --execution-id abc-123 \
  --max-messages 50
```

## Output Example

```
╔══════════════════════════════════════════════════════════════╗
║         Agent Squad - Live Message Stream                    ║
║  Execution: abc-123...  |  Filter: backend_developer        ║
╚══════════════════════════════════════════════════════════════╝

[10:30:15] 📝 PM → Backend Dev #1
           TASK ASSIGNMENT
           ┌─────────────────────────────────────────────────────┐
           │ Implement user authentication API                   │
           │ Priority: HIGH  |  Est: 8 hours                     │
           └─────────────────────────────────────────────────────┘

[10:32:45] ❓ Backend Dev #1 → Tech Lead
           QUESTION
           ┌─────────────────────────────────────────────────────┐
           │ Should we use JWT or session-based auth?            │
           └─────────────────────────────────────────────────────┘

[10:33:10] ✅ Tech Lead → Backend Dev #1
           ANSWER
           ┌─────────────────────────────────────────────────────┐
           │ Use JWT for stateless authentication. Here's why:   │
           │ - Scalable across multiple servers                  │
           │ - Industry standard                                 │
           │ - Works well with our microservices                 │
           └─────────────────────────────────────────────────────┘

╔══════════════════════════════════════════════════════════════╗
║                    📊 Stream Statistics                       ║
╠══════════════════════════════════════════════════════════════╣
║  Status:         ● Connected                                 ║
║  Duration:       00:15:32                                    ║
║  Messages:       23                                          ║
║  Top Type:       question (8)                                ║
║  Most Active:    Backend Dev #1 (12)                         ║
╚══════════════════════════════════════════════════════════════╝

[D]ebug  |  [S]tats  |  [Q]uit / Ctrl+C
```

## Color Scheme

Each agent role has a distinct color for easy identification:

| Role | Color |
|------|-------|
| Project Manager | Cyan |
| Tech Lead | Yellow |
| Backend Developer | Green |
| Frontend Developer | Blue |
| QA Tester | Magenta |
| Solution Architect | Bright Cyan |
| DevOps Engineer | Red |
| AI Engineer | Bright Magenta |
| Designer | Bright Blue |
| Broadcast | White |

## Message Type Icons

| Message Type | Icon |
|--------------|------|
| Task Assignment | 📝 |
| Question | ❓ |
| Answer | ✅ |
| Code Review Request | 👀 |
| Code Review Response | 📋 |
| Status Update | 📊 |
| Status Request | ❔ |
| Standup | 📢 |
| Human Intervention | 🚨 |
| Task Completion | 🎉 |

## Command-Line Options

```
Options:
  --execution-id TEXT     Task execution ID to stream messages from
  --squad-id TEXT         Squad ID to stream messages from (all executions)
  --base-url TEXT         Backend base URL (default: http://localhost:8000)
  --token TEXT            JWT authentication token (or set AGENT_SQUAD_TOKEN env var)
  --filter-role TEXT      Filter messages by agent role (e.g., backend_developer)
  --filter-type TEXT      Filter messages by type (e.g., question)
  --debug                 Enable debug mode (show raw JSON)
  --max-messages INTEGER  Maximum messages to keep in memory (default: 100)
  --help                  Show this message and exit
```

## Environment Variables

- `AGENT_SQUAD_TOKEN`: JWT authentication token (avoids passing via command line)

## Troubleshooting

### Connection Failed

```
Error: Connection failed: 401 Unauthorized
```

**Solution**: Check your token is valid:
```bash
# Get a fresh token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "your@email.com", "password": "yourpassword"}'

export AGENT_SQUAD_TOKEN="new_token_here"
```

### No Messages Appearing

1. **Check execution/squad exists**:
   ```bash
   curl http://localhost:8000/api/v1/task-executions/<execution-id> \
     -H "Authorization: Bearer $AGENT_SQUAD_TOKEN"
   ```

2. **Verify messages are being sent**:
   - Check if agents are actually communicating
   - Look for messages in the database

3. **Try without filters**:
   - Remove `--filter-role` and `--filter-type` to see all messages

### Module Import Errors

```
Error: sseclient-py not installed
```

**Solution**:
```bash
pip install sseclient-py rich click requests
```

### Backend Not Running

```
Error: Connection refused
```

**Solution**: Start the backend:
```bash
cd backend
python main.py
```

## Tips & Tricks

### Save Messages to File

```bash
# Redirect output to file
python -m backend.cli.stream_agent_messages --execution-id abc-123 > messages.log

# In debug mode for JSON
python -m backend.cli.stream_agent_messages --execution-id abc-123 --debug > messages.json
```

### Monitor Specific Agent

```bash
# Watch only backend developer
python -m backend.cli.stream_agent_messages \
  --execution-id abc-123 \
  --filter-role backend_developer
```

### Watch Code Reviews Only

```bash
python -m backend.cli.stream_agent_messages \
  --execution-id abc-123 \
  --filter-type code_review
```

### Multiple Terminals

Run multiple CLI instances in different terminals to watch different aspects:

**Terminal 1** (Questions):
```bash
python -m backend.cli.stream_agent_messages --execution-id abc-123 --filter-type question
```

**Terminal 2** (Code Reviews):
```bash
python -m backend.cli.stream_agent_messages --execution-id abc-123 --filter-type code_review
```

**Terminal 3** (All Messages):
```bash
python -m backend.cli.stream_agent_messages --execution-id abc-123
```

## Integration with Other Tools

### tmux

```bash
# Create tmux session with split panes
tmux new-session -s agent-squad \; \
  split-window -h \; \
  send-keys 'python -m backend.cli.stream_agent_messages --execution-id abc-123 --filter-type question' C-m \; \
  split-window -v \; \
  send-keys 'python -m backend.cli.stream_agent_messages --execution-id abc-123 --filter-type code_review' C-m
```

### Watch Script

```bash
#!/bin/bash
# watch-agents.sh

EXECUTION_ID=$1

if [ -z "$EXECUTION_ID" ]; then
  echo "Usage: ./watch-agents.sh <execution-id>"
  exit 1
fi

python -m backend.cli.stream_agent_messages \
  --execution-id $EXECUTION_ID \
  --token $AGENT_SQUAD_TOKEN
```

## Advanced Usage

### Programmatic Access

You can also use the CLI class in your own Python scripts:

```python
from backend.cli.stream_agent_messages import AgentStreamCLI

cli = AgentStreamCLI(
    base_url="http://localhost:8000",
    execution_id="abc-123",
    token="your_token",
    filter_role="backend_developer",
)

cli.run()
```

## Performance

- **Memory Usage**: ~1KB per message × max_messages (default: 100KB)
- **Network**: Minimal (SSE keeps connection open)
- **CPU**: Very low (event-driven)

## Limitations

- **Authentication Required**: Must have valid JWT token
- **Network Dependent**: Requires active connection to backend
- **No Offline Mode**: Messages not cached locally
- **Terminal Size**: Best viewed on terminals 80+ columns wide

## Future Enhancements

- [ ] Export to JSON/CSV
- [ ] Message search
- [ ] Historical replay
- [ ] Conversation threading view
- [ ] Sound notifications
- [ ] TUI (Terminal User Interface) mode with mouse support

## Support

For issues or questions:
1. Check backend logs
2. Try debug mode (`--debug`)
3. Verify network connectivity
4. Check authentication token

## License

Part of Agent Squad project.
