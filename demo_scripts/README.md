# Demo Scripts

This folder contains demonstration scripts and utilities for testing and showcasing Agent Squad features.

## Demo Scripts

### Multi-turn Conversations
- **demo_multi_turn_with_context.py** - Demonstrates multi-turn conversations with context awareness
- **demo_hierarchical_conversations.py** - Shows hierarchical conversation patterns with parent-child relationships
- **demo_cli_output.py** - CLI-based conversation demo

### Streaming & Real-time
- **demo_phase3_streaming.py** - Phase 3 streaming implementation demo
- **live_streaming_demo.py** - Live streaming with real-time updates
- **realtime_streaming_demo.py** - Real-time message streaming demonstration
- **mock_sse_server.py** - Mock Server-Sent Events server for testing

### Message Bus & NATS
- **demo_nats_agents.py** - NATS message bus integration with agents

### Template System
- **demo_template_system.py** - Squad template system demonstration
- **demo_template_squad_conversations.py** - Template-based squad conversations

### AI Responses
- **demo_phase1_ai_responses.py** - Phase 1 AI response handling demo

## Utility Scripts

- **apply_template_quick.py** - Quick utility to apply squad templates
- **create_squad_now.py** - Utility to create squads on demand
- **reset_db.py** - Database reset utility for testing

## Usage

Most demo scripts can be run directly:

```bash
# Example: Run multi-turn conversation demo
python demo_scripts/demo_multi_turn_with_context.py

# Example: Run streaming demo
python demo_scripts/demo_phase3_streaming.py

# Example: Apply a squad template
python demo_scripts/apply_template_quick.py
```

## Environment Setup

Make sure you have:
1. `.env` file configured with required credentials
2. Database running and migrated
3. Required services (NATS, Redis, etc.) running if needed

Refer to the main [README.md](../README.md) for setup instructions.

## Testing vs Demo Scripts

- **Demo scripts** (this folder) - Interactive demonstrations and utilities
- **Test scripts** (`/tests/`) - Automated test suites for validation

## Documentation

For detailed information about each phase:
- See [docs/implementation_phases/](../docs/implementation_phases/)
- Main docs: [README.md](../README.md)
