# How to Run the Agent Communication Demo

I've built a complete system for you to create agents and watch them communicate in real-time! Here's how to run it:

## What's Been Built

1. **CLI Tools** (in `backend/cli/`):
   - `demo.py` - Automated end-to-end demo
   - `create_demo_squad.py` - Create a squad with agents
   - `run_demo_task.py` - Simulate agent communication
   - `stream_agent_messages.py` - Watch messages in real-time (from Phase 2)

2. **Documentation**:
   - `QUICKSTART_DEMO.md` - Complete quick start guide
   - `backend/cli/README.md` - CLI documentation

## Prerequisites

You need to set up your Python environment first. The backend uses either:

### Option A: Using uv (Recommended)

```bash
# Navigate to backend directory
cd backend

# Install dependencies (this creates a virtual environment automatically)
uv sync

# Or if you have requirements.txt:
uv pip install -r requirements.txt
```

### Option B: Using venv + pip

```bash
# Create virtual environment
cd backend
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Demo

Once your environment is set up:

### Terminal 1: Start Backend Server

```bash
cd backend

# With uv:
uv run python main.py

# Or with venv:
source .venv/bin/activate
python main.py
```

Wait until you see: `Application startup complete`

### Terminal 2: Run the Demo

```bash
# With uv:
uv run python -m backend.cli.demo

# Or with venv:
source backend/.venv/bin/activate
python -m backend.cli.demo
```

The demo will:
1. Create a test user (`demo@agentsquad.dev`)
2. Create a squad with 3 agents (PM, Backend Dev, Frontend Dev)
3. Show you an execution ID
4. Wait 10 seconds
5. Simulate 7 agent messages

### Terminal 3: Watch Messages (Optional)

While the demo is running, open a third terminal and watch the messages stream:

```bash
# The demo will tell you the exact command with the execution ID
# It will look like this:

python -m backend.cli.stream_agent_messages \\
  --execution-id <EXECUTION-ID-FROM-DEMO>
```

## What You'll See

**Terminal 2 (Demo Output):**
```
======================================================================
            🤖  AGENT SQUAD - Live Communication Demo
======================================================================

Step 1: Creating test user...
✅ Created user: demo@agentsquad.dev

Step 2: Creating squad...
✅ Squad created: Live Demo Squad
   - 3 agents ready

Step 3: Creating demo task...
✅ Task created: Build User Authentication
   Execution ID: 550e8400-e29b-41d4-a716-446655440000

📺  TO WATCH MESSAGES IN REAL-TIME:
Open a NEW terminal window and run:
  python -m backend.cli.stream_agent_messages \
    --execution-id 550e8400-e29b-41d4-a716-446655440000

⏳ Waiting 10 seconds for you to start the message stream...

🚀  STARTING AGENT COMMUNICATION

  📢 PM → All: Starting standup...
  📝 PM → Backend Dev: Assigning task...
  ✅ Backend Dev → PM: Acknowledged...
  📝 PM → Frontend Dev: Assigning UI work...
  ❓ Frontend Dev → Backend Dev: Asking question...
  💬 Backend Dev → Frontend Dev: Answering...
  🎉 PM → All: Task complete!

✅  DEMO COMPLETED SUCCESSFULLY

📊 Summary:
  • Squad ID: ...
  • Execution ID: ...
  • Agents: 3
  • Messages: 7
```

**Terminal 3 (Message Stream):**
```
╔════════════════════════════════════════════════════════════════╗
║         Agent Squad - Live Message Stream                      ║
║  Execution: abc-123  |  Connected  |  7 messages  |  3 agents  ║
╚════════════════════════════════════════════════════════════════╝

[10:30:15] 📢 PM → All Agents
           STANDUP
           ┌─────────────────────────────────────────────────────┐
           │ Good morning team! Today we're building user        │
           │ authentication.                                     │
           └─────────────────────────────────────────────────────┘

[10:30:17] 📝 PM → Backend Dev (FastAPI)
           TASK ASSIGNMENT
           ┌─────────────────────────────────────────────────────┐
           │ Please implement the authentication API endpoints.  │
           └─────────────────────────────────────────────────────┘

[10:30:19] ✅ Backend Dev (FastAPI) → PM
           ACKNOWLEDGMENT
           ┌─────────────────────────────────────────────────────┐
           │ Got it! I'll start with the data models.           │
           └─────────────────────────────────────────────────────┘
```

## Troubleshooting

### Dependencies Not Installed

If you get `ModuleNotFoundError`, make sure you've installed dependencies:

```bash
# With uv
cd backend && uv sync

# Or with pip
cd backend && pip install -r requirements.txt
```

### Port Already in Use

If port 8000 is in use:

```bash
# Find and kill the process
lsof -ti:8000 | xargs kill

# Or use a different port
export PORT=8001
python main.py
```

### Database Not Set Up

If you get database errors:

```bash
# Run migrations
cd backend
alembic upgrade head
```

### "User not found"

The demo creates a user automatically. If it fails, check database connection in `.env`

## Manual Step-by-Step (More Control)

If you want more control over each step:

### 1. Create a Squad

```bash
python -m backend.cli.create_demo_squad --user-email your@email.com
```

Save the Squad ID that's printed!

### 2. Run a Task

```bash
python -m backend.cli.run_demo_task --squad-id <SQUAD-ID>
```

Optional: Customize the task:
```bash
python -m backend.cli.run_demo_task \
  --squad-id <SQUAD-ID> \
  --task-description "Build a real-time chat feature"
```

### 3. Watch Messages

```bash
# By execution ID (recommended)
python -m backend.cli.stream_agent_messages --execution-id <EXECUTION-ID>

# By squad ID (sees all executions)
python -m backend.cli.stream_agent_messages --squad-id <SQUAD-ID>

# With filters
python -m backend.cli.stream_agent_messages \
  --execution-id <ID> \
  --filter-role backend_developer

# Debug mode (raw JSON)
python -m backend.cli.stream_agent_messages \
  --execution-id <ID> \
  --debug
```

## What's Happening Under the Hood

1. **Squad Creation** (`create_demo_squad.py`):
   - Creates 3 agents with different roles
   - Assigns different LLM providers/models
   - Configures specializations

2. **Task Execution** (`run_demo_task.py`):
   - Creates a task in the database
   - Starts a task execution
   - Simulates 7 realistic agent messages
   - Uses the Message Bus to route messages
   - Messages are persisted to database
   - Messages are broadcast via SSE

3. **Message Streaming** (`stream_agent_messages.py`):
   - Connects to SSE endpoint
   - Receives real-time message broadcasts
   - Displays with colors and formatting
   - Shows live statistics

## Architecture

```
Demo Script
    ↓
Creates Squad & Agents
    ↓
Starts Task Execution
    ↓
Sends Messages via Message Bus
    ↓
Message Bus:
  • Persists to Database
  • Broadcasts via SSE
    ↓
    ├─→ Terminal (stream_agent_messages.py)
    └─→ Frontend (future: Phase 3)
```

## Next Steps

1. **Run the demo** - See it working!
2. **Explore the code**:
   - `backend/cli/demo.py` - Full demo
   - `backend/agents/communication/message_bus.py` - Message routing
   - `backend/services/sse_service.py` - SSE broadcasting

3. **Customize**:
   - Add more agents to the squad
   - Change task descriptions
   - Modify message types
   - Add more communication scenarios

4. **Build real agents**:
   - Replace simulated messages with real LLM calls
   - Implement actual task delegation
   - Add code review automation

5. **Frontend** (Phase 3):
   - Build React SSE client
   - Create message visualization
   - Add interactive features

## Files Created

- `backend/cli/demo.py` - Automated demo
- `backend/cli/create_demo_squad.py` - Squad creation
- `backend/cli/run_demo_task.py` - Task simulation
- `QUICKSTART_DEMO.md` - Detailed guide
- `RUN_DEMO.md` - This file

## Support

- **Full documentation**: See `QUICKSTART_DEMO.md`
- **CLI reference**: See `backend/cli/README.md`
- **Implementation plan**: See `AGENT_STREAMING_IMPLEMENTATION_PLAN.md`
- **Agent architecture**: See `backend/agents/CLAUDE.md`

---

**Ready to see your AI agents collaborate!** 🤖🚀

Just set up your Python environment and run: `uv run python -m backend.cli.demo`
