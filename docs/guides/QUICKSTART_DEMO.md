# Agent Communication Demo - Quick Start

This guide will walk you through seeing AI agents communicate with each other in real-time!

## Prerequisites

1. Backend server running
2. Database set up and migrated
3. Python dependencies installed

## Option 1: Automated Demo (Recommended)

The easiest way to see agent communication in action:

### Terminal 1: Start Backend Server

```bash
cd backend
python main.py
```

Wait for the server to start (you should see "Application startup complete")

### Terminal 2: Watch Messages (Start this first!)

```bash
# This will wait for messages - keep it open
python -m backend.cli.stream_agent_messages --execution-id <PASTE-ID-HERE>
```

Don't worry about the execution ID yet - we'll get it in the next step.

### Terminal 3: Run Demo

```bash
python -m backend.cli.demo
```

This will:
1. Create a test user (if needed)
2. Create a demo squad with 3 agents:
   - Project Manager
   - Backend Developer
   - Frontend Developer
3. Show you the execution ID to paste into Terminal 2
4. Wait 10 seconds for you to start the message stream
5. Simulate agents communicating about a task

**What you'll see:**
- Terminal 3: Progress messages as agents communicate
- Terminal 2: Live, color-coded agent messages with timestamps

## Option 2: Manual Step-by-Step

If you want more control:

### Step 1: Create a Demo Squad

```bash
python -m backend.cli.create_demo_squad --user-email demo@example.com
```

This outputs:
- Squad ID
- Agent IDs and details
- Next steps

**Save the Squad ID!** You'll need it for the next step.

### Step 2: Run a Demo Task

```bash
python -m backend.cli.run_demo_task --squad-id <SQUAD-ID>
```

Optional: Customize the task description:
```bash
python -m backend.cli.run_demo_task \
  --squad-id <SQUAD-ID> \
  --task-description "Build a real-time chat application"
```

### Step 3: Watch Messages (In Another Terminal)

While the task is running:

```bash
# Watch by execution ID (recommended)
python -m backend.cli.stream_agent_messages --execution-id <EXECUTION-ID>

# Or watch by squad ID (sees all executions)
python -m backend.cli.stream_agent_messages --squad-id <SQUAD-ID>
```

## What's Happening?

The demo simulates a realistic workflow:

1. **PM starts standup** - Broadcasts to team
2. **PM assigns tasks** - To backend and frontend devs
3. **Devs acknowledge** - Confirm they understand
4. **Frontend asks question** - About API format
5. **Backend answers** - Explains the API structure
6. **Devs send status updates** - Progress reports to PM
7. **Backend requests review** - Code is ready
8. **PM approves** - Merges the code
9. **Frontend completes** - UI is done
10. **PM celebrates** - Task complete!

## Message Stream Features

The stream CLI shows:
- **Color-coded agents** - Different color per role
- **Message type icons** - 📝 tasks, ❓ questions, ✅ answers, etc.
- **Timestamps** - When each message was sent
- **Agent names** - Who's talking to whom
- **Live statistics** - Message count, duration, connection status

### Stream CLI Options

```bash
# Filter by agent role
python -m backend.cli.stream_agent_messages \
  --execution-id <ID> \
  --filter-role backend_developer

# Filter by message type
python -m backend.cli.stream_agent_messages \
  --execution-id <ID> \
  --filter-type question

# Debug mode (raw JSON)
python -m backend.cli.stream_agent_messages \
  --execution-id <ID> \
  --debug

# Custom API URL
python -m backend.cli.stream_agent_messages \
  --execution-id <ID> \
  --base-url http://localhost:8000
```

## Example Output

### Terminal 2 (Message Stream):
```
╔════════════════════════════════════════════════════════════════╗
║         Agent Squad - Live Message Stream                      ║
║  Execution: abc-123  |  Connected  |  13 messages  |  3 agents ║
╚════════════════════════════════════════════════════════════════╝

[10:30:15] 📢 PM → All Agents
           STANDUP
           ┌─────────────────────────────────────────────────────┐
           │ Good morning team! Today we're tackling: Build a    │
           │ user authentication system                          │
           └─────────────────────────────────────────────────────┘

[10:30:17] 📝 PM → Backend Dev (FastAPI)
           TASK ASSIGNMENT
           ┌─────────────────────────────────────────────────────┐
           │ Please implement the API endpoints for this         │
           │ feature. We'll need authentication, data            │
           │ validation, and error handling.                     │
           └─────────────────────────────────────────────────────┘

[10:30:19] ❓ Frontend Dev (React) → Backend Dev (FastAPI)
           QUESTION
           ┌─────────────────────────────────────────────────────┐
           │ Hey! What will the API response format be?          │
           └─────────────────────────────────────────────────────┘
```

### Terminal 3 (Demo Script):
```
🤖  AGENT SQUAD - Live Communication Demo

Step 1: Setting up user...
✅ Using existing user: demo@agentsquad.dev

Step 2: Creating demo squad...
✅ Squad created: Live Demo Squad
   - 3 agents ready

Step 3: Creating demo task...
✅ Task created: Demo Task
   Execution ID: 550e8400-e29b-41d4-a716-446655440000

📺 TO WATCH MESSAGES IN REAL-TIME:
Open a NEW terminal window and run:
  python -m backend.cli.stream_agent_messages \
    --execution-id 550e8400-e29b-41d4-a716-446655440000

🚀 STARTING AGENT COMMUNICATION

📢 PM: Starting daily standup...
📝 PM → Backend Dev: Assigning backend work...
✅ Backend Dev → PM: Acknowledged task...
...
```

## Troubleshooting

### "User not found"
```bash
# The demo script creates one automatically, or specify:
python -m backend.cli.demo --user-email your@email.com
```

### "Squad not found"
Make sure you're using the correct Squad ID from the create_demo_squad output.

### "Connection refused" in stream CLI
Make sure the backend server is running on the correct port (default: 8000).

### No messages appearing
- Check that both terminals are running
- Verify the execution ID matches
- Ensure the backend server is running

### "Squad needs at least 3 agents"
The demo requires a squad with PM, Backend Dev, and Frontend Dev. Use `create_demo_squad` which creates these automatically.

## Next Steps

Now that you've seen agents communicate:

1. **Explore the code**:
   - `backend/cli/demo.py` - Complete demo script
   - `backend/cli/run_demo_task.py` - Task simulation
   - `backend/agents/communication/message_bus.py` - Message routing

2. **Customize**:
   - Modify the task description
   - Add more agents to the squad
   - Create different message types
   - Build real agent LLM integration

3. **Build the frontend**:
   - See `AGENT_STREAMING_IMPLEMENTATION_PLAN.md` Phase 3
   - Implement React SSE client
   - Create message visualization components

4. **Production features**:
   - Real LLM calls instead of simulated messages
   - Task delegation logic
   - Code review automation
   - Human escalation

## Architecture

```
┌─────────────┐
│   Demo CLI  │ Creates squad & agents
└──────┬──────┘
       │
       ▼
┌─────────────────────────────┐
│  run_demo_task.py           │
│  - Simulates task execution │
│  - Sends agent messages     │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│  Message Bus                │
│  - Routes messages          │
│  - Persists to DB           │
│  - Broadcasts via SSE       │
└──────┬──────────────────────┘
       │
       ├──────────────┬─────────────────┐
       ▼              ▼                 ▼
┌─────────────┐ ┌──────────────┐ ┌──────────────┐
│  Database   │ │  SSE Stream  │ │  Frontend    │
│  (History)  │ │  (Real-time) │ │  (Phase 3)   │
└─────────────┘ └──────────────┘ └──────────────┘
```

## Learn More

- **CLI Documentation**: `backend/cli/README.md`
- **Implementation Plan**: `AGENT_STREAMING_IMPLEMENTATION_PLAN.md`
- **Agent Architecture**: `backend/agents/CLAUDE.md`
- **Message Bus**: `backend/agents/communication/CLAUDE.md`

---

**Enjoy watching your AI agents collaborate!** 🤖🚀
