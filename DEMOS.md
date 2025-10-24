# Demo Files

## Overview

Demo files showcase different features and capabilities of the Agent Squad system. Each demo is self-contained and can be run independently.

## Demo Files

### ✅ `verify_agno_only.py` - Agno Migration Verification

**Purpose**: Verify complete migration to Agno framework

**What It Tests**:
- All imports working
- Legacy code removed
- All 9 agents creating successfully
- Factory registry correct
- Supported roles validated

**Run**:
```bash
python verify_agno_only.py
```

**Output**: 5/5 verifications passed ✅

---

### 🤖 `demo_agno_agents.py` - Basic Agno Agent Demo

**Purpose**: Demonstrate basic Agno agent creation and messaging

**Features**:
- Create Agno agents for different roles
- Send messages
- Show persistent sessions
- Demonstrate memory

**Run**:
```bash
PYTHONPATH=$PWD python demo_agno_agents.py
```

---

### 🚀 `demo_agno_agents_auto.py` - Automated Agno Demo

**Purpose**: Automated agent interactions

**Features**:
- Automatic agent creation
- Multi-turn conversations
- Session resumption
- Performance metrics

**Run**:
```bash
PYTHONPATH=$PWD python demo_agno_agents_auto.py
```

---

### 📨 `demo_agno_message_bus.py` - NATS Message Bus Demo

**Purpose**: Demonstrate NATS JetStream integration with Agno agents

**Prerequisites**:
```bash
# Start NATS server
nats-server -js

# Set environment
export MESSAGE_BUS=nats
export NATS_URL=nats://localhost:4222
```

**Features**:
- NATS JetStream setup
- Agent-to-agent messaging
- Message persistence
- Consumer groups

**Run**:
```bash
PYTHONPATH=$PWD MESSAGE_BUS=nats python demo_agno_message_bus.py
```

---

### 👥 `demo_squad_collaboration.py` - Squad Collaboration

**Purpose**: Demonstrate hierarchical agent collaboration

**Features**:
- Question routing
- Backend dev → Tech lead communication
- Automatic escalation
- Conversation tracking

**Run**:
```bash
PYTHONPATH=$PWD MESSAGE_BUS=nats python demo_squad_collaboration.py
```

---

### 📊 `demo_hierarchical_squad.py` - Hierarchical Structure

**Purpose**: Show organizational hierarchy and message routing

**Features**:
- PM → TL → Dev hierarchy
- Task delegation
- Status updates
- Progress tracking

**Run**:
```bash
PYTHONPATH=$PWD python demo_hierarchical_squad.py
```

---

### 💬 `demo_agent_conversations.py` - Agent Conversations

**Purpose**: Multi-agent conversations and coordination

**Features**:
- Multiple agents communicating
- Conversation context
- Message threading
- History tracking

**Run**:
```bash
PYTHONPATH=$PWD python demo_agent_conversations.py
```

---

### 🧪 `test_agent_factory_agno.py` - Factory Tests

**Purpose**: Test Agno agent factory

**Features**:
- Agent creation tests
- Configuration validation
- Role validation
- Error handling

**Run**:
```bash
PYTHONPATH=$PWD python test_agent_factory_agno.py
```

---

### 🔌 `test_nats_agno_integration.py` - NATS Integration Test

**Purpose**: Test NATS + Agno integration

**Prerequisites**:
```bash
export MESSAGE_BUS=nats
export USE_AGNO_AGENTS=true
export NATS_URL=nats://localhost:4222
```

**Features**:
- NATS connection test
- Agent messaging via NATS
- Message persistence
- Error recovery

**Run**:
```bash
PYTHONPATH=$PWD MESSAGE_BUS=nats python test_nats_agno_integration.py
```

---

## Running All Demos

### Sequential
```bash
#!/bin/bash
# run_all_demos.sh

echo "1. Verify Agno Migration"
python verify_agno_only.py

echo "2. Basic Agno Demo"
PYTHONPATH=$PWD python demo_agno_agents.py

echo "3. Message Bus Demo (requires NATS)"
PYTHONPATH=$PWD MESSAGE_BUS=nats python demo_agno_message_bus.py

echo "4. Squad Collaboration"
PYTHONPATH=$PWD python demo_squad_collaboration.py

echo "All demos complete!"
```

### With Docker Compose
```bash
# Start all services
docker-compose up -d postgres nats

# Run demos
./run_all_demos.sh

# Stop services
docker-compose down
```

---

## Demo Environment Setup

### Prerequisites
```bash
# Python environment
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Environment variables
cp .env.example .env
# Edit .env with your values

# Database
createdb agent_squad
alembic upgrade head

# NATS (optional for message bus demos)
nats-server -js
```

### Required Environment Variables
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/agent_squad
OPENAI_API_KEY=sk-...          # For Agno agents
ANTHROPIC_API_KEY=...           # Optional
NATS_URL=nats://localhost:4222  # For message bus demos
MESSAGE_BUS=nats                # Use NATS (default: memory)
```

---

## Demo Categories

### 🤖 Agent Basics
- `verify_agno_only.py` - Verification
- `demo_agno_agents.py` - Basic usage
- `demo_agno_agents_auto.py` - Automated

### 📨 Message Bus
- `demo_agno_message_bus.py` - NATS integration
- `test_nats_agno_integration.py` - Integration testing

### 👥 Collaboration
- `demo_squad_collaboration.py` - Hierarchical collaboration
- `demo_hierarchical_squad.py` - Organizational structure
- `demo_agent_conversations.py` - Multi-agent conversations

### 🧪 Testing
- `test_agent_factory_agno.py` - Factory tests
- `test_nats_agno_integration.py` - Integration tests

---

## Troubleshooting

**Q: ImportError when running demos?**
```bash
# Set PYTHONPATH
export PYTHONPATH=/path/to/agent-squad
# OR
PYTHONPATH=$PWD python demo_file.py
```

**Q: Database connection errors?**
```bash
# Check DATABASE_URL
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL
```

**Q: NATS connection errors?**
```bash
# Check NATS is running
nats-server -js

# Test connection
nats pub test "hello"
nats sub test
```

**Q: OpenAI API errors?**
```bash
# Check API key
echo $OPENAI_API_KEY

# Test API
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

---

## Adding New Demos

### 1. Create Demo File
```python
#!/usr/bin/env python3
"""
Demo: Your Feature Name
Purpose: What this demo shows
"""
import sys
sys.path.insert(0, '/path/to/agent-squad')

# Your demo code
```

### 2. Document in DEMOS.md
Add entry to this file with:
- Purpose
- Features
- Prerequisites
- Run command

### 3. Test Demo
```bash
# Test on clean environment
python your_demo.py

# Test with different configs
MESSAGE_BUS=memory python your_demo.py
MESSAGE_BUS=nats python your_demo.py
```

---

## Related Documentation

- See `backend/agents/CLAUDE.md` for agent architecture
- See `backend/agents/specialized/CLAUDE.md` for agent roles
- See `AGNO_ARCHITECTURE_GUIDE.md` for Agno framework guide
- See `backend/tests/CLAUDE.md` for testing documentation
