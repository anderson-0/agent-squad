#!/usr/bin/env python3
"""
Cache Metrics Visualization CLI

Quick command-line tool to visualize cache and task monitoring metrics.

Usage:
    python backend/cli/view_cache_metrics.py
    python backend/cli/view_cache_metrics.py --watch  # Auto-refresh every 5s
    python backend/cli/view_cache_metrics.py --json   # Raw JSON output
"""
import argparse
import time
import sys
from datetime import datetime
import asyncio
import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich import box
from rich.progress import Progress, BarColumn, TextColumn

console = Console()

BASE_URL = "http://localhost:8000/api/v1"


async def fetch_metrics():
    """Fetch all metrics from API"""
    async with httpx.AsyncClient() as client:
        try:
            # Fetch cache metrics
            cache_response = await client.get(f"{BASE_URL}/cache/metrics", timeout=5.0)
            cache_data = cache_response.json() if cache_response.status_code == 200 else None

            # Fetch task monitoring
            task_response = await client.get(f"{BASE_URL}/task-monitoring/metrics", timeout=5.0)
            task_data = task_response.json() if task_response.status_code == 200 else None

            # Fetch recommendations
            rec_response = await client.get(f"{BASE_URL}/task-monitoring/ttl-recommendations", timeout=5.0)
            rec_data = rec_response.json() if rec_response.status_code == 200 else None

            return {
                "cache": cache_data,
                "tasks": task_data,
                "recommendations": rec_data,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            console.print(f"[red]Error fetching metrics: {e}[/red]")
            return None


def create_cache_metrics_table(cache_data):
    """Create table for cache metrics"""
    if not cache_data or not cache_data.get("metrics_by_type"):
        return Panel("[yellow]No cache data available[/yellow]", title="Cache Metrics")

    table = Table(title="Cache Performance by Entity Type", box=box.ROUNDED)
    table.add_column("Entity", style="cyan", no_wrap=True)
    table.add_column("Hit Rate", style="magenta", justify="right")
    table.add_column("Hits", style="green", justify="right")
    table.add_column("Misses", style="red", justify="right")
    table.add_column("Total", justify="right")
    table.add_column("Status", justify="center")

    for entity_type, metrics in cache_data["metrics_by_type"].items():
        hit_rate = metrics.get("hit_rate", 0)
        hits = metrics.get("hits", 0)
        misses = metrics.get("misses", 0)
        total = metrics.get("total_requests", 0)

        # Status emoji based on hit rate
        if hit_rate >= 80:
            status = "✅ Excellent"
            hit_rate_style = "bold green"
        elif hit_rate >= 70:
            status = "✅ Good"
            hit_rate_style = "green"
        elif hit_rate >= 60:
            status = "⚠️  Fair"
            hit_rate_style = "yellow"
        else:
            status = "❌ Poor"
            hit_rate_style = "red"

        table.add_row(
            entity_type.upper(),
            f"[{hit_rate_style}]{hit_rate:.1f}%[/{hit_rate_style}]",
            f"{hits:,}",
            f"{misses:,}",
            f"{total:,}",
            status
        )

    overall_rate = cache_data.get("overall_hit_rate", 0)
    total_requests = cache_data.get("total_requests", 0)

    summary = f"\n[bold]Overall:[/bold] {overall_rate:.1f}% hit rate | {total_requests:,} total requests"

    return Panel(table, title=f"📊 Cache Metrics {summary}", border_style="blue")


def create_task_metrics_panel(task_data):
    """Create panel for task lifecycle metrics"""
    if not task_data:
        return Panel("[yellow]No task data available[/yellow]", title="Task Metrics")

    completed = task_data.get("total_tasks_completed", 0)
    avg_time = task_data.get("avg_completion_time_seconds", 0)
    active = task_data.get("active_tasks_count", 0)
    updates = task_data.get("total_status_updates", 0)
    update_interval = task_data.get("avg_time_between_updates_seconds", 0)

    p50 = task_data.get("completion_time_p50", 0)
    p95 = task_data.get("completion_time_p95", 0)
    p99 = task_data.get("completion_time_p99", 0)

    # Insights
    completion_speed = task_data.get("insights", {}).get("completion_speed", "unknown")
    update_frequency = task_data.get("insights", {}).get("update_frequency", "unknown")

    # Speed emoji
    speed_emoji = {
        "fast": "⚡",
        "moderate": "⏱️",
        "slow": "🐌"
    }.get(completion_speed, "❓")

    # Update emoji
    update_emoji = {
        "high": "🔄",
        "moderate": "⏰",
        "low": "💤"
    }.get(update_frequency, "❓")

    content = f"""[bold cyan]Task Completion:[/bold cyan]
  • Total Completed: [green]{completed}[/green]
  • Avg Time: [yellow]{avg_time/60:.1f} minutes[/yellow] ({avg_time:.0f}s)
  • P50 (Median): {p50/60:.1f} min | P95: {p95/60:.1f} min | P99: {p99/60:.1f} min
  • Speed: {speed_emoji} [bold]{completion_speed.upper()}[/bold]

[bold cyan]Status Updates:[/bold cyan]
  • Total Updates: [blue]{updates}[/blue]
  • Avg Interval: [yellow]{update_interval:.0f} seconds[/yellow]
  • Frequency: {update_emoji} [bold]{update_frequency.upper()}[/bold]

[bold cyan]Current Activity:[/bold cyan]
  • Active Tasks: [magenta]{active}[/magenta]
"""

    return Panel(content, title="⏱️  Task Lifecycle Metrics", border_style="green")


def create_recommendations_table(rec_data):
    """Create table for TTL recommendations"""
    if not rec_data or not rec_data.get("recommendations"):
        return Panel("[yellow]No recommendations available - need more data[/yellow]", title="Recommendations")

    table = Table(title="TTL Optimization Recommendations", box=box.ROUNDED)
    table.add_column("Entity", style="cyan", no_wrap=True)
    table.add_column("Current TTL", justify="right")
    table.add_column("→", justify="center", style="bold yellow")
    table.add_column("Recommended", justify="right", style="bold green")
    table.add_column("Confidence", justify="center")
    table.add_column("Reason", style="dim")

    for rec in rec_data["recommendations"]:
        entity_type = rec["entity_type"]
        current_ttl = rec["current_ttl_seconds"]
        recommended_ttl = rec["recommended_ttl_seconds"]
        confidence = rec["confidence"]
        reason = rec["reason"]

        # Determine if change is needed
        if abs(current_ttl - recommended_ttl) > 10:
            change_arrow = "→"
            change_style = "bold yellow"
        else:
            change_arrow = "✓"
            change_style = "green"

        # Confidence styling
        conf_emoji = {
            "high": "🟢",
            "medium": "🟡",
            "low": "🔴"
        }.get(confidence, "⚪")

        table.add_row(
            entity_type.upper(),
            f"{current_ttl}s",
            change_arrow,
            f"{recommended_ttl}s",
            f"{conf_emoji} {confidence}",
            reason[:60] + "..." if len(reason) > 60 else reason
        )

    metrics_summary = rec_data.get("metrics_summary", {})
    tasks_analyzed = metrics_summary.get("tasks_analyzed", 0)

    footer = f"\n[dim]Based on {tasks_analyzed} tasks analyzed[/dim]"
    if tasks_analyzed < 10:
        footer += " [yellow]⚠️  Need more data for reliable recommendations[/yellow]"

    return Panel(table, title=f"🎯 Recommendations{footer}", border_style="yellow")


def create_dashboard(metrics_data):
    """Create full dashboard layout"""
    if not metrics_data:
        return Panel("[red]Unable to fetch metrics - is the API running?[/red]", title="Error")

    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="cache", size=12),
        Layout(name="tasks", size=12),
        Layout(name="recommendations", size=10),
        Layout(name="footer", size=3)
    )

    # Header
    timestamp = metrics_data.get("timestamp", "")
    header_text = f"[bold cyan]Agent Squad - Cache & Task Monitoring Dashboard[/bold cyan]\n[dim]{timestamp}[/dim]"
    layout["header"].update(Panel(header_text, border_style="cyan"))

    # Cache metrics
    layout["cache"].update(create_cache_metrics_table(metrics_data.get("cache")))

    # Task metrics
    layout["tasks"].update(create_task_metrics_panel(metrics_data.get("tasks")))

    # Recommendations
    layout["recommendations"].update(create_recommendations_table(metrics_data.get("recommendations")))

    # Footer
    footer_text = "[dim]Press Ctrl+C to exit | Use --watch for auto-refresh[/dim]"
    layout["footer"].update(Panel(footer_text, border_style="dim"))

    return layout


async def display_dashboard(watch=False, json_output=False):
    """Display the dashboard"""
    if json_output:
        # JSON output mode
        metrics = await fetch_metrics()
        if metrics:
            import json
            console.print_json(data=metrics)
        return

    if watch:
        # Watch mode - auto-refresh
        console.clear()
        with Live(console=console, refresh_per_second=0.2) as live:
            try:
                while True:
                    metrics = await fetch_metrics()
                    if metrics:
                        dashboard = create_dashboard(metrics)
                        live.update(dashboard)
                    await asyncio.sleep(5)
            except KeyboardInterrupt:
                console.print("\n[yellow]Monitoring stopped[/yellow]")
    else:
        # Single display
        console.clear()
        metrics = await fetch_metrics()
        if metrics:
            dashboard = create_dashboard(metrics)
            console.print(dashboard)
        else:
            console.print("[red]Failed to fetch metrics. Is the API running?[/red]")


def main():
    parser = argparse.ArgumentParser(
        description="Visualize cache and task monitoring metrics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Display current metrics
  %(prog)s --watch            # Auto-refresh every 5 seconds
  %(prog)s --json             # Output raw JSON
  %(prog)s --url http://...   # Use custom API URL
        """
    )
    parser.add_argument(
        "--watch", "-w",
        action="store_true",
        help="Auto-refresh every 5 seconds"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output raw JSON instead of dashboard"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000/api/v1",
        help="API base URL (default: http://localhost:8000/api/v1)"
    )

    args = parser.parse_args()

    global BASE_URL
    BASE_URL = args.url

    try:
        asyncio.run(display_dashboard(watch=args.watch, json_output=args.json))
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
        sys.exit(0)


if __name__ == "__main__":
    main()
