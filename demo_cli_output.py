#!/usr/bin/env python3
"""
Demo Script - Shows CLI Output

This script demonstrates what the CLI looks like when displaying agent messages.
It creates a visual representation of the terminal output.
"""
import sys
import json
from datetime import datetime

# Mock messages that would come from SSE
messages = [
    {
        "message_id": "msg-1",
        "sender_id": "agent-1",
        "sender_role": "backend_developer",
        "sender_name": "Backend Dev (FastAPI)",
        "sender_specialization": "python_fastapi",
        "recipient_id": "agent-2",
        "recipient_role": "tech_lead",
        "recipient_name": "Tech Lead",
        "content": "How should I implement caching for the user API? We're seeing response times of 2-3 seconds.",
        "message_type": "question",
        "metadata": {"priority": "high"},
        "timestamp": "2025-10-21T10:30:00Z",
        "conversation_thread_id": "thread-auth-123"
    },
    {
        "message_id": "msg-2",
        "sender_id": "agent-2",
        "sender_role": "tech_lead",
        "sender_name": "Tech Lead",
        "recipient_id": "agent-1",
        "recipient_role": "backend_developer",
        "recipient_name": "Backend Dev (FastAPI)",
        "content": "Use Redis for caching. Here's why:\n- Fast in-memory storage\n- TTL support for automatic expiration\n- Industry standard for API caching\n\nCache user data with 5-minute TTL. Invalidate on updates.",
        "message_type": "answer",
        "metadata": {},
        "timestamp": "2025-10-21T10:30:15Z",
        "conversation_thread_id": "thread-auth-123"
    },
    {
        "message_id": "msg-3",
        "sender_id": "agent-1",
        "sender_role": "backend_developer",
        "sender_name": "Backend Dev (FastAPI)",
        "sender_specialization": "python_fastapi",
        "recipient_id": "agent-2",
        "recipient_role": "tech_lead",
        "recipient_name": "Tech Lead",
        "content": "Progress: 25% | Status: In Progress\nImplemented Redis caching layer with 5-minute TTL.\nNext: Testing cache invalidation logic.",
        "message_type": "status_update",
        "metadata": {"progress": 25},
        "timestamp": "2025-10-21T10:35:00Z",
        "conversation_thread_id": "thread-auth-123"
    },
    {
        "message_id": "msg-4",
        "sender_id": "agent-1",
        "sender_role": "backend_developer",
        "sender_name": "Backend Dev (FastAPI)",
        "sender_specialization": "python_fastapi",
        "recipient_id": "agent-2",
        "recipient_role": "tech_lead",
        "recipient_name": "Tech Lead",
        "content": "Code review needed!\n\nPR: https://github.com/org/repo/pull/123\nChanges: Added Redis caching for user API\n\nImplemented:\n✓ Redis cache layer\n✓ 5-minute TTL\n✓ Cache invalidation on updates\n✓ Unit tests (95% coverage)\n✓ Integration tests\n\nResponse times improved from 2.5s → 150ms!",
        "message_type": "code_review_request",
        "metadata": {"pr_number": 123},
        "timestamp": "2025-10-21T10:40:00Z",
        "conversation_thread_id": "thread-auth-123"
    },
    {
        "message_id": "msg-5",
        "sender_id": "agent-2",
        "sender_role": "tech_lead",
        "sender_name": "Tech Lead",
        "recipient_id": "agent-1",
        "recipient_role": "backend_developer",
        "recipient_name": "Backend Dev (FastAPI)",
        "content": "Code Review: APPROVED ✅\n\nGreat work! A few observations:\n\n✅ Excellent cache implementation\n✅ Good test coverage\n✅ Proper error handling\n\n💡 Minor suggestion: Consider adding cache warming for frequently accessed users.\n\nReady to merge!",
        "message_type": "code_review_response",
        "metadata": {"approved": True},
        "timestamp": "2025-10-21T10:42:00Z",
        "conversation_thread_id": "thread-auth-123"
    },
    {
        "message_id": "msg-6",
        "sender_id": "agent-1",
        "sender_role": "backend_developer",
        "sender_name": "Backend Dev (FastAPI)",
        "sender_specialization": "python_fastapi",
        "recipient_id": None,
        "recipient_role": "broadcast",
        "recipient_name": "All Agents",
        "content": "🎉 Task completed!\n\nImplemented Redis caching for user API:\n- Response times: 2.5s → 150ms (94% improvement)\n- Cache hit rate: ~85%\n- Zero data consistency issues\n- Full test coverage\n\nPR merged to main. Ready for deployment!",
        "message_type": "task_completion",
        "metadata": {"completed": True},
        "timestamp": "2025-10-21T10:45:00Z",
        "conversation_thread_id": "thread-auth-123"
    }
]

# Icons
icons = {
    "question": "❓",
    "answer": "✅",
    "status_update": "📊",
    "code_review_request": "👀",
    "code_review_response": "📋",
    "task_completion": "🎉"
}

# Colors (for text representation)
colors = {
    "backend_developer": "GREEN",
    "tech_lead": "YELLOW",
    "broadcast": "WHITE"
}

print("\n" + "=" * 80)
print("  AGENT MESSAGE STREAMING CLI - DEMONSTRATION")
print("=" * 80)
print()
print("This is what the CLI looks like when displaying agent messages in real-time:")
print()
print("=" * 80)
print()

# Header
print("╔═══════════════════════════════════════════════════════════════════════════════╗")
print("║ Agent Squad - Live Message Stream                                             ║")
print("║ Execution: test-exe...                                                        ║")
print("╚═══════════════════════════════════════════════════════════════════════════════╝")
print()
print("✓ Connected successfully!")
print("Waiting for messages...")
print()

# Display messages
for msg in messages:
    icon = icons.get(msg["message_type"], "💬")
    sender = msg["sender_name"]
    recipient = msg["recipient_name"]
    content = msg["content"]
    msg_type = msg["message_type"].replace("_", " ").upper()

    # Format time
    try:
        dt = datetime.fromisoformat(msg["timestamp"].replace('Z', '+00:00'))
        time_str = dt.strftime("%H:%M:%S")
    except:
        time_str = "10:30:00"

    # Print message
    print(f"[{time_str}] {icon} {sender} → {recipient}")
    print(f"           {msg_type}")
    print("           ┌─────────────────────────────────────────────────────────────────┐")

    # Print content (wrapped)
    lines = content.split('\n')
    for line in lines:
        if len(line) <= 60:
            print(f"           │ {line:<60}│")
        else:
            # Simple wrapping
            words = line.split()
            current_line = ""
            for word in words:
                if len(current_line) + len(word) + 1 <= 60:
                    current_line += (" " if current_line else "") + word
                else:
                    print(f"           │ {current_line:<60}│")
                    current_line = word
            if current_line:
                print(f"           │ {current_line:<60}│")

    print("           └─────────────────────────────────────────────────────────────────┘")
    print()

# Final stats
print("╔═══════════════════════════════════════════════════════════════════════════════╗")
print("║                     📊 Stream Statistics                                      ║")
print("╠═══════════════════════════════════════════════════════════════════════════════╣")
print("║  Status:         ● Connected                                                  ║")
print("║  Duration:       00:15:00                                                     ║")
print("║  Messages:       6                                                            ║")
print("║  Top Type:       question (1)                                                 ║")
print("║  Most Active:    Backend Dev (FastAPI) (4)                                    ║")
print("╚═══════════════════════════════════════════════════════════════════════════════╝")
print()
print("Stream closed.")
print()

print("=" * 80)
print()
print("KEY FEATURES DEMONSTRATED:")
print()
print("✅ Color-coded agents (Backend Dev in GREEN, Tech Lead in YELLOW)")
print("✅ Message type icons (❓ question, ✅ answer, 📊 status, 👀 code review, 🎉 completion)")
print("✅ Real-time message display with sender → recipient")
print("✅ Formatted content in bordered boxes")
print("✅ Statistics panel showing stream status and metrics")
print("✅ Timestamp for each message")
print("✅ Message type labels (QUESTION, ANSWER, etc.)")
print()
print("ACTUAL CLI FEATURES (not shown here due to text limitations):")
print("  - True color coding (each agent role has a different color)")
print("  - Rich terminal formatting with boxes and panels")
print("  - Live updating statistics")
print("  - Filter by agent role or message type")
print("  - Debug mode to see raw JSON")
print("  - Graceful shutdown with Ctrl+C")
print()
print("To run the actual CLI:")
print("  python -m backend.cli.stream_agent_messages \\")
print("    --execution-id <uuid> \\")
print("    --token <jwt-token>")
print()
print("=" * 80)
print()
