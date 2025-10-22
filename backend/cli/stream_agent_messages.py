#!/usr/bin/env python3
"""
Agent Message Streaming CLI

Real-time visualization of agent-to-agent communication in the terminal.

Usage:
    python -m backend.cli.stream_agent_messages --execution-id <uuid>
    python -m backend.cli.stream_agent_messages --squad-id <uuid>
    python -m backend.cli.stream_agent_messages --execution-id <uuid> --filter-role backend_developer
    python -m backend.cli.stream_agent_messages --execution-id <uuid> --debug

Requirements:
    pip install sseclient-py rich click requests
"""
import sys
import os
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
from collections import defaultdict
import signal

import click
import requests
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich import box
from rich.spinner import Spinner

try:
    from sseclient import SSEClient
except ImportError:
    print("Error: sseclient-py not installed. Run: pip install sseclient-py")
    sys.exit(1)


# Color scheme by agent role
AGENT_COLORS = {
    "project_manager": "cyan",
    "tech_lead": "yellow",
    "backend_developer": "green",
    "frontend_developer": "blue",
    "qa_tester": "magenta",
    "tester": "magenta",
    "solution_architect": "bright_cyan",
    "devops_engineer": "red",
    "ai_engineer": "bright_magenta",
    "designer": "bright_blue",
    "broadcast": "white",
}

# Message type icons
MESSAGE_ICONS = {
    "task_assignment": "📝",
    "question": "❓",
    "answer": "✅",
    "code_review_request": "👀",
    "code_review_response": "📋",
    "status_update": "📊",
    "status_request": "❔",
    "standup": "📢",
    "human_intervention_required": "🚨",
    "task_completion": "🎉",
}


class AgentStreamCLI:
    """
    Terminal CLI for streaming agent messages.

    Displays real-time agent-to-agent communication with:
    - Color-coded agents
    - Message type icons
    - Filters by role/type
    - Statistics
    - Debug mode
    """

    def __init__(
        self,
        base_url: str,
        execution_id: Optional[str] = None,
        squad_id: Optional[str] = None,
        token: Optional[str] = None,
        filter_role: Optional[str] = None,
        filter_type: Optional[str] = None,
        debug: bool = False,
        max_messages: int = 100,
    ):
        """
        Initialize the CLI.

        Args:
            base_url: Backend base URL (e.g., http://localhost:8000)
            execution_id: Task execution ID to stream
            squad_id: Squad ID to stream (all executions)
            token: JWT authentication token
            filter_role: Filter messages by agent role
            filter_type: Filter messages by message type
            debug: Enable debug mode (show raw JSON)
            max_messages: Maximum messages to keep in memory
        """
        self.base_url = base_url.rstrip('/')
        self.execution_id = execution_id
        self.squad_id = squad_id
        self.token = token
        self.filter_role = filter_role
        self.filter_type = filter_type
        self.debug = debug
        self.max_messages = max_messages

        self.console = Console()
        self.messages: List[Dict[str, Any]] = []
        self.stats = {
            "total": 0,
            "by_type": defaultdict(int),
            "by_role": defaultdict(int),
            "by_sender": defaultdict(int),
        }
        self.connected = False
        self.start_time = None
        self.running = True

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        self.running = False
        self.console.print("\n[yellow]Shutting down...[/yellow]")
        sys.exit(0)

    def connect_sse(self) -> SSEClient:
        """
        Connect to SSE endpoint.

        Returns:
            SSEClient instance

        Raises:
            requests.RequestException: If connection fails
        """
        # Determine endpoint
        if self.execution_id:
            endpoint = f"{self.base_url}/api/v1/sse/execution/{self.execution_id}"
        elif self.squad_id:
            endpoint = f"{self.base_url}/api/v1/sse/squad/{self.squad_id}"
        else:
            raise ValueError("Must provide either execution_id or squad_id")

        # Set up headers
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        # Connect
        self.console.print(f"[dim]Connecting to {endpoint}...[/dim]")

        try:
            response = requests.get(endpoint, headers=headers, stream=True)
            response.raise_for_status()

            self.connected = True
            self.start_time = datetime.now()

            return SSEClient(response)
        except requests.RequestException as e:
            self.console.print(f"[red]Connection failed: {e}[/red]")
            raise

    def should_display_message(self, message: Dict[str, Any]) -> bool:
        """
        Check if message should be displayed based on filters.

        Args:
            message: Message data

        Returns:
            True if message should be displayed
        """
        # Filter by role
        if self.filter_role:
            sender_role = message.get("sender_role", "")
            recipient_role = message.get("recipient_role", "")
            if (self.filter_role.lower() not in sender_role.lower() and
                self.filter_role.lower() not in recipient_role.lower()):
                return False

        # Filter by type
        if self.filter_type:
            message_type = message.get("message_type", "")
            if self.filter_type.lower() not in message_type.lower():
                return False

        return True

    def format_message(self, message: Dict[str, Any]) -> Panel:
        """
        Format a message for display.

        Args:
            message: Message data

        Returns:
            Rich Panel with formatted message
        """
        # Extract data
        sender_name = message.get("sender_name", "Unknown")
        sender_role = message.get("sender_role", "unknown")
        recipient_name = message.get("recipient_name", "Unknown")
        recipient_role = message.get("recipient_role", "unknown")
        content = message.get("content", "")
        message_type = message.get("message_type", "message")
        timestamp = message.get("timestamp", "")

        # Get colors
        sender_color = AGENT_COLORS.get(sender_role, "white")
        recipient_color = AGENT_COLORS.get(recipient_role, "white")

        # Get icon
        icon = MESSAGE_ICONS.get(message_type, "💬")

        # Format timestamp
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_str = dt.strftime("%H:%M:%S")
        except:
            time_str = timestamp[:8] if timestamp else "??:??:??"

        # Create header
        header = Text()
        header.append(f"[{time_str}] ", style="dim")
        header.append(f"{icon} ", style="")
        header.append(sender_name, style=f"bold {sender_color}")
        header.append(" → ", style="dim")
        header.append(recipient_name, style=f"bold {recipient_color}")

        # Create message type label
        type_label = message_type.replace("_", " ").upper()

        # Create content box
        content_text = Text()
        content_text.append(content[:500])  # Limit length
        if len(content) > 500:
            content_text.append("...", style="dim")

        # Create panel
        panel = Panel(
            content_text,
            title=header,
            subtitle=f"[dim]{type_label}[/dim]",
            border_style="dim",
            box=box.ROUNDED,
        )

        return panel

    def format_debug_message(self, message: Dict[str, Any]) -> str:
        """
        Format message as JSON for debug mode.

        Args:
            message: Message data

        Returns:
            Formatted JSON string
        """
        return json.dumps(message, indent=2, default=str)

    def update_stats(self, message: Dict[str, Any]):
        """
        Update statistics with new message.

        Args:
            message: Message data
        """
        self.stats["total"] += 1

        message_type = message.get("message_type", "unknown")
        self.stats["by_type"][message_type] += 1

        sender_role = message.get("sender_role", "unknown")
        self.stats["by_role"][sender_role] += 1

        sender_name = message.get("sender_name", "Unknown")
        self.stats["by_sender"][sender_name] += 1

    def create_stats_panel(self) -> Panel:
        """
        Create statistics panel.

        Returns:
            Rich Panel with statistics
        """
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Label", style="cyan")
        table.add_column("Value", style="bold")

        # Connection info
        status_color = "green" if self.connected else "red"
        status_text = "Connected" if self.connected else "Disconnected"
        table.add_row("Status:", f"[{status_color}]● {status_text}[/{status_color}]")

        # Duration
        if self.start_time:
            duration = datetime.now() - self.start_time
            hours, remainder = divmod(int(duration.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            table.add_row("Duration:", duration_str)

        # Message count
        table.add_row("Messages:", str(self.stats["total"]))

        # Top message type
        if self.stats["by_type"]:
            top_type = max(self.stats["by_type"], key=self.stats["by_type"].get)
            top_count = self.stats["by_type"][top_type]
            table.add_row("Top Type:", f"{top_type} ({top_count})")

        # Most active agent
        if self.stats["by_sender"]:
            top_sender = max(self.stats["by_sender"], key=self.stats["by_sender"].get)
            top_count = self.stats["by_sender"][top_sender]
            table.add_row("Most Active:", f"{top_sender} ({top_count})")

        return Panel(
            table,
            title="📊 Stream Statistics",
            border_style="cyan",
            box=box.ROUNDED,
        )

    def create_header(self) -> Panel:
        """
        Create header panel.

        Returns:
            Rich Panel with header
        """
        title = Text()
        title.append("Agent Squad ", style="bold cyan")
        title.append("- Live Message Stream", style="bold white")

        info = Text()
        if self.execution_id:
            info.append(f"Execution: ", style="dim")
            info.append(self.execution_id[:8] + "...", style="yellow")
        elif self.squad_id:
            info.append(f"Squad: ", style="dim")
            info.append(self.squad_id[:8] + "...", style="yellow")

        if self.filter_role:
            info.append(" | Filter: ", style="dim")
            info.append(self.filter_role, style="magenta")

        if self.filter_type:
            info.append(" | Type: ", style="dim")
            info.append(self.filter_type, style="magenta")

        header_text = Text()
        header_text.append(title)
        header_text.append("\n")
        header_text.append(info)

        return Panel(
            header_text,
            border_style="cyan",
            box=box.DOUBLE,
        )

    def create_footer(self) -> Panel:
        """
        Create footer panel with controls.

        Returns:
            Rich Panel with controls
        """
        controls = Text()
        controls.append("[D]ebug ", style="bold")
        controls.append("| ", style="dim")
        controls.append("[S]tats ", style="bold")
        controls.append("| ", style="dim")
        controls.append("[Q]uit / Ctrl+C", style="bold")

        return Panel(
            controls,
            border_style="dim",
            box=box.ROUNDED,
        )

    def run(self):
        """
        Main run loop - connect to SSE and display messages.
        """
        try:
            # Show header
            self.console.print(self.create_header())
            self.console.print()

            # Connect to SSE
            sse_client = self.connect_sse()

            self.console.print("[green]✓ Connected successfully![/green]")
            self.console.print("[dim]Waiting for messages...[/dim]\n")

            # Stream messages
            for event in sse_client.events():
                if not self.running:
                    break

                # Parse event
                if event.event == "heartbeat":
                    # Heartbeat - update connection status
                    continue

                if event.event == "connected":
                    # Initial connection message
                    try:
                        data = json.loads(event.data)
                        msg = data.get("message", "Connected")
                        self.console.print(f"[dim]{msg}[/dim]")
                    except:
                        pass
                    continue

                if event.event == "message":
                    # Actual agent message
                    try:
                        message = json.loads(event.data)

                        # Check filters
                        if not self.should_display_message(message):
                            continue

                        # Update stats
                        self.update_stats(message)

                        # Store message
                        self.messages.append(message)
                        if len(self.messages) > self.max_messages:
                            self.messages.pop(0)

                        # Display message
                        if self.debug:
                            self.console.print(f"[dim]═══════════════════════════════════════[/dim]")
                            self.console.print(self.format_debug_message(message))
                        else:
                            self.console.print(self.format_message(message))

                        self.console.print()

                    except json.JSONDecodeError as e:
                        if self.debug:
                            self.console.print(f"[red]Error parsing message: {e}[/red]")
                            self.console.print(f"[dim]Raw data: {event.data}[/dim]")

                elif event.event == "error":
                    # Error event
                    try:
                        error_data = json.loads(event.data)
                        self.console.print(f"[red]Error: {error_data.get('error', 'Unknown error')}[/red]")
                    except:
                        self.console.print(f"[red]Error event received[/red]")

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Stream interrupted by user[/yellow]")
        except requests.RequestException as e:
            self.console.print(f"[red]Connection error: {e}[/red]")
            sys.exit(1)
        except Exception as e:
            self.console.print(f"[red]Unexpected error: {e}[/red]")
            if self.debug:
                import traceback
                self.console.print(traceback.format_exc())
            sys.exit(1)
        finally:
            # Show final stats
            if self.stats["total"] > 0:
                self.console.print("\n")
                self.console.print(self.create_stats_panel())

            self.console.print("\n[cyan]Stream closed.[/cyan]")


@click.command()
@click.option(
    "--execution-id",
    type=str,
    help="Task execution ID to stream messages from"
)
@click.option(
    "--squad-id",
    type=str,
    help="Squad ID to stream messages from (all executions)"
)
@click.option(
    "--base-url",
    type=str,
    default="http://localhost:8000",
    help="Backend base URL (default: http://localhost:8000)"
)
@click.option(
    "--token",
    type=str,
    envvar="AGENT_SQUAD_TOKEN",
    help="JWT authentication token (or set AGENT_SQUAD_TOKEN env var)"
)
@click.option(
    "--filter-role",
    type=str,
    help="Filter messages by agent role (e.g., backend_developer)"
)
@click.option(
    "--filter-type",
    type=str,
    help="Filter messages by type (e.g., question)"
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug mode (show raw JSON)"
)
@click.option(
    "--max-messages",
    type=int,
    default=100,
    help="Maximum messages to keep in memory (default: 100)"
)
def main(
    execution_id: Optional[str],
    squad_id: Optional[str],
    base_url: str,
    token: Optional[str],
    filter_role: Optional[str],
    filter_type: Optional[str],
    debug: bool,
    max_messages: int,
):
    """
    Agent Message Streaming CLI

    Stream and visualize real-time agent-to-agent communication.

    Examples:

        # Stream messages for a specific execution
        python -m backend.cli.stream_agent_messages --execution-id abc-123 --token YOUR_TOKEN

        # Stream all messages in a squad
        python -m backend.cli.stream_agent_messages --squad-id xyz-789 --token YOUR_TOKEN

        # Filter by agent role
        python -m backend.cli.stream_agent_messages --execution-id abc-123 --filter-role backend_developer

        # Filter by message type
        python -m backend.cli.stream_agent_messages --execution-id abc-123 --filter-type question

        # Debug mode (show raw JSON)
        python -m backend.cli.stream_agent_messages --execution-id abc-123 --debug

        # Use environment variable for token
        export AGENT_SQUAD_TOKEN=your_token_here
        python -m backend.cli.stream_agent_messages --execution-id abc-123
    """
    # Validate inputs
    if not execution_id and not squad_id:
        click.echo("Error: Must provide either --execution-id or --squad-id", err=True)
        sys.exit(1)

    if execution_id and squad_id:
        click.echo("Error: Cannot provide both --execution-id and --squad-id", err=True)
        sys.exit(1)

    # Create and run CLI
    cli = AgentStreamCLI(
        base_url=base_url,
        execution_id=execution_id,
        squad_id=squad_id,
        token=token,
        filter_role=filter_role,
        filter_type=filter_type,
        debug=debug,
        max_messages=max_messages,
    )

    cli.run()


if __name__ == "__main__":
    main()
