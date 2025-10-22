#!/usr/bin/env python3
"""
Live Streaming Demo - Agent Messages

Shows messages streaming in real-time, one by one, like ChatGPT/Claude.
"""
import sys
import time
from datetime import datetime

# Try to import rich, fall back to basic if not available
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Note: Install 'rich' for better formatting: uv pip install rich")
    print()

# Message data
messages = [
    {
        "sender": "Backend Dev (FastAPI)",
        "sender_color": "green",
        "recipient": "Tech Lead",
        "recipient_color": "yellow",
        "icon": "❓",
        "type": "QUESTION",
        "content": "How should I implement caching for the user API? We're seeing response times of 2-3 seconds.",
        "time": "10:30:00",
        "delay": 2
    },
    {
        "sender": "Tech Lead",
        "sender_color": "yellow",
        "recipient": "Backend Dev (FastAPI)",
        "recipient_color": "green",
        "icon": "✅",
        "type": "ANSWER",
        "content": "Use Redis for caching. Here's why:\n- Fast in-memory storage\n- TTL support for automatic expiration\n- Industry standard for API caching\n\nCache user data with 5-minute TTL. Invalidate on updates.",
        "time": "10:30:15",
        "delay": 3
    },
    {
        "sender": "Backend Dev (FastAPI)",
        "sender_color": "green",
        "recipient": "Tech Lead",
        "recipient_color": "yellow",
        "icon": "📊",
        "type": "STATUS UPDATE",
        "content": "Progress: 25% | Status: In Progress\nImplemented Redis caching layer with 5-minute TTL.\nNext: Testing cache invalidation logic.",
        "time": "10:35:00",
        "delay": 4
    },
    {
        "sender": "Tech Lead",
        "sender_color": "yellow",
        "recipient": "Backend Dev (FastAPI)",
        "recipient_color": "green",
        "icon": "❓",
        "type": "QUESTION",
        "content": "Did you add cache invalidation on user updates? That's critical for data consistency.",
        "time": "10:37:00",
        "delay": 2
    },
    {
        "sender": "Backend Dev (FastAPI)",
        "sender_color": "green",
        "recipient": "Tech Lead",
        "recipient_color": "yellow",
        "icon": "✅",
        "type": "ANSWER",
        "content": "Yes! Added cache invalidation in the update_user() endpoint. Also added tests to verify cache is cleared on updates.",
        "time": "10:37:30",
        "delay": 3
    },
    {
        "sender": "Backend Dev (FastAPI)",
        "sender_color": "green",
        "recipient": "Tech Lead",
        "recipient_color": "yellow",
        "icon": "👀",
        "type": "CODE REVIEW REQUEST",
        "content": "Code review needed!\n\nPR: https://github.com/org/repo/pull/123\nChanges: Added Redis caching for user API\n\nImplemented:\n✓ Redis cache layer\n✓ 5-minute TTL\n✓ Cache invalidation on updates\n✓ Unit tests (95% coverage)\n✓ Integration tests\n\nResponse times improved from 2.5s → 150ms!",
        "time": "10:40:00",
        "delay": 3
    },
    {
        "sender": "Tech Lead",
        "sender_color": "yellow",
        "recipient": "Backend Dev (FastAPI)",
        "recipient_color": "green",
        "icon": "📋",
        "type": "CODE REVIEW RESPONSE",
        "content": "Code Review: APPROVED ✅\n\nGreat work! A few observations:\n\n✅ Excellent cache implementation\n✅ Good test coverage\n✅ Proper error handling\n\n💡 Minor suggestion: Consider adding cache warming for frequently accessed users.\n\nReady to merge!",
        "time": "10:42:00",
        "delay": 3
    },
    {
        "sender": "Backend Dev (FastAPI)",
        "sender_color": "green",
        "recipient": "All Agents",
        "recipient_color": "white",
        "icon": "🎉",
        "type": "TASK COMPLETION",
        "content": "🎉 Task completed!\n\nImplemented Redis caching for user API:\n- Response times: 2.5s → 150ms (94% improvement)\n- Cache hit rate: ~85%\n- Zero data consistency issues\n- Full test coverage\n\nPR merged to main. Ready for deployment!",
        "time": "10:45:00",
        "delay": 2
    }
]

def print_header():
    """Print the CLI header"""
    print("\n" + "=" * 80)
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║ Agent Squad - Live Message Stream                                          ║")
    print("║ Execution: test-exe...                                                     ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print()
    print("✓ Connected successfully!")
    print("Waiting for messages...")
    print()
    print("=" * 80)
    print()

def print_message_rich(msg):
    """Print message with Rich formatting"""
    console = Console()

    # Create header
    header = Text()
    header.append(f"[{msg['time']}] ", style="dim")
    header.append(f"{msg['icon']} ", style="")
    header.append(msg['sender'], style=f"bold {msg['sender_color']}")
    header.append(" → ", style="dim")
    header.append(msg['recipient'], style=f"bold {msg['recipient_color']}")

    # Create content
    content_text = Text(msg['content'])

    # Create panel
    panel = Panel(
        content_text,
        title=header,
        subtitle=f"[dim]{msg['type']}[/dim]",
        border_style="dim",
        box=box.ROUNDED,
    )

    console.print(panel)
    console.print()

def print_message_basic(msg):
    """Print message with basic formatting (no Rich)"""
    print(f"[{msg['time']}] {msg['icon']} {msg['sender']} → {msg['recipient']}")
    print(f"           {msg['type']}")
    print("           ┌" + "─" * 65 + "┐")

    # Print content lines
    for line in msg['content'].split('\n'):
        print(f"           │ {line:<64}│")

    print("           └" + "─" * 65 + "┘")
    print()

def print_stats(message_count):
    """Print statistics"""
    print()
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                     📊 Stream Statistics                                   ║")
    print("╠════════════════════════════════════════════════════════════════════════════╣")
    print("║  Status:         ● Connected                                               ║")
    print("║  Duration:       00:15:00                                                  ║")
    print(f"║  Messages:       {message_count:<58}║")
    print("║  Top Type:       question (2)                                              ║")
    print("║  Most Active:    Backend Dev (FastAPI) (5)                                 ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print()

def animate_typing(text, delay=0.02):
    """Simulate typing effect"""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def main():
    """Main streaming demo"""
    print_header()

    # Show "Connecting..." with animation
    sys.stdout.write("Connecting")
    for _ in range(3):
        time.sleep(0.5)
        sys.stdout.write(".")
        sys.stdout.flush()
    print(" ✓")
    print()
    time.sleep(1)

    # Stream messages one by one
    for i, msg in enumerate(messages, 1):
        print(f"\n[Streaming message {i}/{len(messages)}...]")
        time.sleep(0.3)

        # Print the message
        if RICH_AVAILABLE:
            print_message_rich(msg)
        else:
            print_message_basic(msg)

        # Wait before next message (simulating real-time arrival)
        if i < len(messages):
            print(f"[Waiting for next message...]")
            time.sleep(msg['delay'])

    # Show final stats
    print("\n[Stream complete! Showing statistics...]")
    time.sleep(1)
    print_stats(len(messages))

    print("Stream closed.")
    print("=" * 80)
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[Stream interrupted by user]")
        sys.exit(0)
