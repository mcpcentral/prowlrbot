# -*- coding: utf-8 -*-
"""Swarm CLI commands for AI agent swarm management."""

from __future__ import annotations

import json
import logging

import click

logger = logging.getLogger(__name__)


@click.group(name="swarm", help="AI agent swarm management")
def swarm_group():
    """Manage AI agent swarm connecting ProwlrBot to remote agents."""
    pass


@swarm_group.command(name="status", help="Check swarm status")
def swarm_status():
    """Check the status of the AI swarm."""
    click.echo("AI Swarm Status")
    click.echo("-" * 40)
    click.echo("Worker: Not running (use 'prowlr swarm up' to start)")
    click.echo("Bridge: Unknown (requires Mac with Bridge API)")
    click.echo("Redis: Check with 'docker ps'")


@swarm_group.command(name="up", help="Start swarm infrastructure")
@click.option(
    "--env-file",
    default=".env.swarm",
    help="Path to environment file",
)
def swarm_up(env_file: str):
    """Start the swarm infrastructure (Redis + Worker)."""
    click.echo(f"Starting AI Swarm with config: {env_file}")
    click.echo("Run: docker compose -f docker-compose.swarm.yml up -d")
    click.echo("\nOr manually:")
    click.echo("  docker compose -f docker-compose.swarm.yml up -d")


@swarm_group.command(name="down", help="Stop swarm infrastructure")
def swarm_down():
    """Stop the swarm infrastructure."""
    click.echo("Stopping AI Swarm...")
    click.echo("Run: docker compose -f docker-compose.swarm.yml down")


@swarm_group.command(name="logs", help="View swarm logs")
@click.option("--follow", "-f", is_flag=True, help="Follow log output")
def swarm_logs(follow: bool):
    """View swarm logs."""
    cmd = "docker compose -f docker-compose.swarm.yml logs"
    if follow:
        cmd += " -f"
    click.echo(f"Run: {cmd}")


@swarm_group.command(name="enqueue", help="Enqueue a job to the swarm")
@click.argument("capability")
@click.option("--param", "-p", multiple=True, help="Parameters as key=value")
@click.option("--wait", "-w", is_flag=True, help="Wait for result")
def swarm_enqueue(capability: str, param: tuple, wait: bool):
    """Enqueue a job to the swarm for execution.

    Examples:
        prowlr swarm enqueue browser:open -p url=https://example.com
        prowlr swarm enqueue file:read -p path=~/Documents/file.txt -w
    """
    import sys
    import os

    # Add swarm/client to path relative to prowlrbot package
    prowlrbot_root = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)),
    )
    project_root = os.path.dirname(prowlrbot_root)
    client_path = os.path.join(project_root, "swarm", "client")
    sys.path.insert(0, client_path)
    try:
        from client import JobQueue
    except ImportError:
        click.echo("Error: Cannot import JobQueue client", err=True)
        sys.exit(1)

    # Parse parameters
    params = {}
    for p in param:
        if "=" not in p:
            click.echo(f"Error: Parameter must be key=value: {p}", err=True)
            sys.exit(1)
        key, value = p.split("=", 1)
        params[key] = value

    queue = JobQueue()
    if not queue.connect():
        click.echo("Error: Failed to connect to Redis", err=True)
        sys.exit(1)

    job_id = queue.enqueue(capability, params)
    click.echo(f"Enqueued job: {job_id}")

    if wait:
        click.echo("Waiting for result...")
        try:
            result = queue.get_result(job_id, timeout=300)
            click.echo(json.dumps(result, indent=2))
        except Exception as e:
            click.echo(f"Error: {e}", err=True)


@swarm_group.command(name="result", help="Get job result")
@click.argument("job_id")
@click.option(
    "--timeout",
    "-t",
    default=0,
    type=int,
    help="Seconds to wait (0 = immediate)",
)
def swarm_result(job_id: str, timeout: int):
    """Get the result of a job."""
    import sys
    import os

    # Get project root relative to this file's location
    # src/prowlrbot/cli/swarm_cmd.py -> project root
    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", ".."),
    )
    swarm_client_path = os.path.join(project_root, "swarm", "client")

    sys.path.insert(0, swarm_client_path)
    try:
        from client import JobQueue
    except ImportError as e:
        click.echo(
            f"Error: Cannot import JobQueue client from {swarm_client_path}: {e}",
            err=True,
        )
        sys.exit(1)

    queue = JobQueue()
    if not queue.connect():
        click.echo("Error: Failed to connect to Redis", err=True)
        sys.exit(1)

    result = queue.get_result(job_id, timeout=timeout)
    if result:
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo("Result not available yet")


@swarm_group.command(name="capabilities", help="List available capabilities")
def swarm_capabilities():
    """List capabilities available on the swarm."""
    capabilities = {
        "browser:open": "Open a URL in the default browser",
        "browser:screenshot": "Take a screenshot of a webpage",
        "shell:execute": "Execute a shell command",
        "file:read": "Read a file",
        "file:write": "Write to a file",
        "file:list": "List directory contents",
    }

    click.echo("Available Capabilities:")
    click.echo("-" * 60)
    for name, desc in capabilities.items():
        click.echo(f"  {name:25} - {desc}")


@swarm_group.command(name="config", help="Show swarm configuration")
def swarm_config():
    """Show current swarm configuration."""
    import os

    click.echo("AI Swarm Configuration:")
    click.echo("-" * 40)
    click.echo(f"REDIS_HOST: {os.getenv('REDIS_HOST', 'localhost')}")
    click.echo(f"REDIS_PORT: {os.getenv('REDIS_PORT', '6379')}")
    click.echo(f"BRIDGE_HOST: {os.getenv('BRIDGE_HOST', 'not set')}")
    click.echo(f"BRIDGE_PORT: {os.getenv('BRIDGE_PORT', '8765')}")
    click.echo(
        f"HMAC_SECRET: {'*' * 10 if os.getenv('HMAC_SECRET') else 'not set'}",
    )
