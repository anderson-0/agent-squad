# Agent Configuration Module

## Overview

The `configuration/` module provides configuration management for agent interactions, including timeouts, escalation rules, and message templates.

## Key Files

### `interaction_config.py` - Interaction Configuration

**Purpose**: Centralized configuration for hierarchical agent conversations

**Configuration Structure**:
```python
class InteractionConfig:
    # Feature flags
    enable_auto_acknowledgment: bool = True
    enable_auto_escalation: bool = True
    enable_timeout_monitoring: bool = True

    # Timeouts (seconds)
    timeouts: dict = {
        "initial_timeout_seconds": 1800,      # 30 minutes
        "reminder_timeout_seconds": 3600,     # 1 hour
        "escalation_timeout_seconds": 7200,   # 2 hours
        "max_reminder_count": 2,
        "max_escalation_level": 3
    }

    # Message templates
    message_templates: dict = {
        "acknowledgment": "I've received your question and will respond shortly.",
        "reminder": "Following up on your question from {time_ago}.",
        "escalation": "This question has been escalated to {responder_role}.",
        "timeout": "Your question timed out after {duration}.",
        "resolution": "This conversation has been resolved."
    }

    # Escalation rules
    escalation_rules: dict = {
        "max_escalation_level": 3,
        "auto_escalate_to_human": True,
        "escalate_on_responder_offline": True,
        "escalation_cooldown_seconds": 300  # 5 minutes
    }

    # Routing defaults
    routing_defaults: dict = {
        "default_priority": 0,
        "fallback_to_pm": True,
        "allow_self_routing": False
    }
```

---

## Usage

### Get Configuration
```python
from backend.agents.configuration.interaction_config import get_interaction_config

config = get_interaction_config()

# Access settings
timeout = config.timeouts["initial_timeout_seconds"]
template = config.get_message_template("acknowledgment")
max_level = config.escalation_rules["max_escalation_level"]
```

### Custom Configuration
```python
# Create custom config
custom_config = InteractionConfig(
    timeouts={
        "initial_timeout_seconds": 900,  # 15 minutes (faster)
        "max_reminder_count": 1
    }
)

# Use with manager
manager = ConversationManager(db, config=custom_config)
```

---

## Environment Variables

Can be overridden via environment variables:
```bash
# Timeouts
AGENT_INITIAL_TIMEOUT_SECONDS=1800
AGENT_MAX_REMINDER_COUNT=2

# Feature flags
AGENT_AUTO_ACKNOWLEDGMENT=true
AGENT_AUTO_ESCALATION=true
AGENT_TIMEOUT_MONITORING=true

# Escalation
AGENT_MAX_ESCALATION_LEVEL=3
AGENT_AUTO_ESCALATE_TO_HUMAN=true
```

---

## Configuration Profiles

### Development (Fast Iteration)
```python
dev_config = InteractionConfig(
    timeouts={
        "initial_timeout_seconds": 300,   # 5 minutes
        "reminder_timeout_seconds": 600,  # 10 minutes
        "max_reminder_count": 1
    }
)
```

### Production (Standard)
```python
prod_config = InteractionConfig(
    timeouts={
        "initial_timeout_seconds": 1800,  # 30 minutes
        "reminder_timeout_seconds": 3600, # 1 hour
        "max_reminder_count": 2
    }
)
```

### Enterprise (High Volume)
```python
enterprise_config = InteractionConfig(
    timeouts={
        "initial_timeout_seconds": 900,   # 15 minutes
        "max_reminder_count": 3
    },
    escalation_rules={
        "max_escalation_level": 5,  # More levels
        "escalation_cooldown_seconds": 180
    }
)
```

---

## Message Templates

### Template Variables
Available in message templates:
- `{time_ago}` - Time since question
- `{responder_role}` - Role of responder
- `{asker_name}` - Name of asker
- `{duration}` - Duration (formatted)
- `{escalation_level}` - Current level

### Custom Templates
```python
config.message_templates["acknowledgment"] = (
    "Hi {asker_name}, I've got your question. "
    "I'll respond within {estimated_time}."
)
```

---

## Related Documentation

- See `../interaction/CLAUDE.md` for interaction module
- See `../CLAUDE.md` for agent architecture
