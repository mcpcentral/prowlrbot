#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ProwlrHub MCP Server — stdio transport for Claude Code integration.

Each Claude Code terminal spawns this as an MCP server process.
All instances share the same SQLite database for coordination.

Run directly: python -m prowlrbot.hub.mcp_server
Or via MCP config in .mcp.json
"""

from __future__ import annotations

import json
import logging
import os
import platform
import sys
import uuid
from typing import Any, Dict, List, Optional

from .engine import WarRoomEngine

logger = logging.getLogger(__name__)

# Per-process state
_engine: Optional[WarRoomEngine] = None
_remote: Optional[Any] = None  # RemoteWarRoom when using bridge
_agent_id: Optional[str] = None
_session_id: Optional[str] = None
_room_id: Optional[str] = None
_agent_name: Optional[str] = None
_is_remote: bool = False


def _get_engine() -> WarRoomEngine:
    global _engine
    if _engine is None:
        db_path = os.environ.get("PROWLR_HUB_DB", None)
        _engine = WarRoomEngine(db_path)
    return _engine


def _get_remote():
    """Get the remote client for bridge mode."""
    global _remote
    if _remote is None:
        from .remote_client import RemoteWarRoom

        url = os.environ["PROWLR_HUB_URL"]
        _remote = RemoteWarRoom(url)
    return _remote


def _auto_register() -> Dict[str, str]:
    """Auto-register this Claude Code instance on first tool call."""
    global _agent_id, _session_id, _room_id, _agent_name, _is_remote

    hub_url = os.environ.get("PROWLR_HUB_URL", "")
    _is_remote = bool(hub_url)

    if _agent_id:
        # Already registered — just heartbeat
        if _is_remote:
            _get_remote().heartbeat()
        else:
            _get_engine().heartbeat(_agent_id)
        return {"agent_id": _agent_id, "room_id": _room_id}

    # Generate agent name from environment — always append PID for uniqueness
    base_name = os.environ.get("PROWLR_AGENT_NAME", "")
    if not base_name:
        base_name = f"claude-{platform.node().split('.')[0]}"
    terminal_id = f"{base_name}-{os.getpid()}"

    capabilities = os.environ.get("PROWLR_CAPABILITIES", "").split(",")
    capabilities = [c.strip() for c in capabilities if c.strip()]

    if _is_remote:
        remote = _get_remote()
        result = remote.register(terminal_id, capabilities or ["general"])
        _agent_id = result.get("agent_id", "")
        _room_id = result.get("room_id", "")
        _agent_name = terminal_id
        logger.info(
            "Registered (remote) as %s (agent_id=%s)",
            terminal_id,
            _agent_id,
        )
    else:
        engine = _get_engine()
        room = engine.get_or_create_default_room()
        _room_id = room["room_id"]
        result = engine.register_agent(
            name=terminal_id,
            room_id=_room_id,
            capabilities=capabilities or ["general"],
        )
        _agent_id = result["agent_id"]
        _session_id = result["session_id"]
        _agent_name = terminal_id
        logger.info(
            "Registered (local) as %s (agent_id=%s) in room %s",
            terminal_id,
            _agent_id,
            _room_id,
        )

    return {"agent_id": _agent_id, "room_id": _room_id}


# --- MCP Tool Implementations ---

TOOLS = {
    "check_mission_board": {
        "description": "See all tasks on the war room mission board — who owns what, what's available, what's blocked. ALWAYS call this before starting any work.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filter_status": {
                    "type": "string",
                    "description": "Filter by status: pending, claimed, in_progress, done, failed, or empty for all",
                    "default": "",
                },
            },
        },
    },
    "claim_task": {
        "description": "Atomically claim a task from the mission board. Locks all file scopes. If claim fails (files locked, already taken), pick a different task — never force through.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Task title (creates new task and claims it)",
                },
                "task_id": {
                    "type": "string",
                    "description": "Existing task ID to claim (use instead of title)",
                    "default": "",
                },
                "file_scopes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Files this task will edit (all get locked)",
                    "default": [],
                },
                "description": {
                    "type": "string",
                    "description": "What you plan to do",
                    "default": "",
                },
                "required_capabilities": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Capabilities needed for this task",
                    "default": [],
                },
                "priority": {
                    "type": "string",
                    "enum": ["critical", "high", "normal", "low"],
                    "default": "normal",
                },
            },
            "required": ["title"],
        },
    },
    "update_task": {
        "description": "Update progress on your current task. Call at meaningful milestones so other agents can see your progress.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "Task ID to update",
                },
                "progress_note": {
                    "type": "string",
                    "description": "What you've done so far",
                },
            },
            "required": ["task_id", "progress_note"],
        },
    },
    "complete_task": {
        "description": "Mark your task as done. Releases all file locks automatically. Include a summary of what was accomplished.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "Task ID to complete",
                },
                "summary": {
                    "type": "string",
                    "description": "Summary of what was accomplished",
                },
            },
            "required": ["task_id", "summary"],
        },
    },
    "fail_task": {
        "description": "Mark a task as failed and release all locks. Use when you can't complete the work.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "reason": {
                    "type": "string",
                    "description": "Why the task failed",
                },
            },
            "required": ["task_id", "reason"],
        },
    },
    "lock_file": {
        "description": "Lock a file before editing it (advisory lock). Other agents will see it's locked and back off.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path relative to repo root",
                },
            },
            "required": ["path"],
        },
    },
    "unlock_file": {
        "description": "Release a file lock when you're done editing.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path to unlock",
                },
            },
            "required": ["path"],
        },
    },
    "check_conflicts": {
        "description": "Check if any of these files are locked by other agents before you start editing.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "File paths to check",
                },
            },
            "required": ["paths"],
        },
    },
    "get_agents": {
        "description": "See who's connected to the war room — their names, capabilities, current tasks, and status.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    "broadcast_status": {
        "description": "Announce what you're doing to all other agents. Use when blocked, need help, or have important findings.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Status message to broadcast",
                },
            },
            "required": ["message"],
        },
    },
    "share_finding": {
        "description": "Share a finding or discovery with all agents in the room. Other agents can query shared findings before starting work.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Short key for this finding (e.g. 'auth-vuln-1', 'api-pattern')",
                },
                "value": {
                    "type": "string",
                    "description": "The finding details",
                },
            },
            "required": ["key", "value"],
        },
    },
    "get_shared_context": {
        "description": "Read findings and context shared by other agents. Check this before starting research to avoid duplicate discovery.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Specific key to look up (empty = get all)",
                    "default": "",
                },
            },
        },
    },
    "get_events": {
        "description": "See recent war room events — who claimed what, who completed what, broadcasts, etc.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 20,
                    "description": "Number of events to return",
                },
                "event_type": {
                    "type": "string",
                    "default": "",
                    "description": "Filter by event type (e.g. task.completed)",
                },
            },
        },
    },
}


def handle_tool_call(
    tool_name: str,
    arguments: Dict[str, Any],
) -> Dict[str, Any]:
    """Execute a war room tool and return the result."""
    reg = _auto_register()
    agent_id = _agent_id

    # Route through remote client if using bridge
    if _is_remote:
        return _handle_remote_tool(tool_name, arguments)

    engine = _get_engine()
    room_id = _room_id

    if tool_name == "check_mission_board":
        tasks = engine.get_mission_board(room_id)
        filter_status = arguments.get("filter_status", "")
        if filter_status:
            tasks = [t for t in tasks if t["status"] == filter_status]

        # Format as readable board
        if not tasks:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Mission board is empty. No tasks yet.",
                    },
                ],
            }

        lines = ["# Mission Board\n"]
        for t in tasks:
            status_icon = {
                "pending": "⬜",
                "claimed": "🔵",
                "in_progress": "🟡",
                "done": "✅",
                "failed": "❌",
            }.get(t["status"], "❓")
            owner = (
                f" → {t.get('owner_name', 'unknown')}"
                if t.get("owner_agent_id")
                else ""
            )
            blocked = " [BLOCKED]" if t.get("is_blocked") else ""
            prio = f" [{t['priority'].upper()}]" if t["priority"] != "normal" else ""
            files = f" files: {t['file_scopes']}" if t["file_scopes"] else ""
            note = f"\n   Note: {t['progress_note']}" if t.get("progress_note") else ""
            lines.append(
                f"{status_icon} {t['task_id']} | {t['title']}{prio}{owner}{blocked}{files}{note}",
            )

        return {"content": [{"type": "text", "text": "\n".join(lines)}]}

    elif tool_name == "claim_task":
        task_id = arguments.get("task_id", "")
        if not task_id:
            # Create new task and claim it
            task = engine.create_task(
                room_id=room_id,
                title=arguments["title"],
                description=arguments.get("description", ""),
                file_scopes=arguments.get("file_scopes", []),
                required_capabilities=arguments.get(
                    "required_capabilities",
                    [],
                ),
                priority=arguments.get("priority", "normal"),
            )
            task_id = task["task_id"]

        result = engine.claim_task(task_id, agent_id, room_id)
        if result.success:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Claimed task {task_id}. Lock token: {result.lock_token}. You own the file scopes — proceed with your work.",
                    },
                ],
            }
        else:
            conflict_info = ""
            if result.conflicts:
                conflict_info = "\nConflicts:\n" + "\n".join(
                    f"  - {c['file']} locked by {c['owner_agent_id']}"
                    for c in result.conflicts
                )
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Claim FAILED: {result.reason}.{conflict_info}\nPick a different task or wait.",
                    },
                ],
            }

    elif tool_name == "update_task":
        engine.update_task(
            arguments["task_id"],
            agent_id,
            arguments["progress_note"],
        )
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Updated task {arguments['task_id']}: {arguments['progress_note']}",
                },
            ],
        }

    elif tool_name == "complete_task":
        ok = engine.complete_task(
            arguments["task_id"],
            agent_id,
            arguments.get("summary", ""),
        )
        if ok:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Task {arguments['task_id']} completed. All file locks released.",
                    },
                ],
            }
        return {
            "content": [
                {
                    "type": "text",
                    "text": "Failed to complete task — you may not own it.",
                },
            ],
        }

    elif tool_name == "fail_task":
        ok = engine.fail_task(
            arguments["task_id"],
            agent_id,
            arguments.get("reason", ""),
        )
        if ok:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Task {arguments['task_id']} marked as failed. Locks released.",
                    },
                ],
            }
        return {
            "content": [
                {
                    "type": "text",
                    "text": "Failed to mark task — you may not own it.",
                },
            ],
        }

    elif tool_name == "lock_file":
        result = engine.lock_file(arguments["path"], agent_id, room_id)
        if result.success:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Locked {arguments['path']}. Token: {result.lock_token}",
                    },
                ],
            }
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Lock failed: {result.reason}. Owner: {result.owner}",
                },
            ],
        }

    elif tool_name == "unlock_file":
        ok = engine.unlock_file(arguments["path"], agent_id, room_id)
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"{'Unlocked' if ok else 'Not found:'} {arguments['path']}",
                },
            ],
        }

    elif tool_name == "check_conflicts":
        conflicts = engine.check_conflicts(arguments["paths"], room_id)
        if not conflicts:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "All files are free — safe to edit.",
                    },
                ],
            }
        lines = ["File conflicts found:"]
        for c in conflicts:
            lines.append(
                f"  {c['file']} → locked by {c['agent_name']} ({c['agent_id']})",
            )
        return {"content": [{"type": "text", "text": "\n".join(lines)}]}

    elif tool_name == "get_agents":
        agents = engine.get_agents(room_id)
        if not agents:
            return {
                "content": [{"type": "text", "text": "No agents connected."}],
            }
        lines = ["# War Room Agents\n"]
        for a in agents:
            status_icon = {
                "idle": "🟢",
                "working": "🔵",
                "disconnected": "⚪",
            }.get(
                a["status"],
                "❓",
            )
            task_info = (
                f" → task {a['current_task_id']}" if a.get("current_task_id") else ""
            )
            caps = ", ".join(a["capabilities"]) if a["capabilities"] else "general"
            me = " (you)" if a["agent_id"] == agent_id else ""
            lines.append(
                f"{status_icon} {a['name']}{me} | caps: [{caps}] | {a['status']}{task_info}",
            )
        return {"content": [{"type": "text", "text": "\n".join(lines)}]}

    elif tool_name == "broadcast_status":
        engine.broadcast_status(room_id, agent_id, arguments["message"])
        return {
            "content": [
                {"type": "text", "text": f"Broadcast: {arguments['message']}"},
            ],
        }

    elif tool_name == "share_finding":
        engine.set_context(
            room_id,
            agent_id,
            arguments["key"],
            arguments["value"],
        )
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Shared finding '{arguments['key']}' with the room.",
                },
            ],
        }

    elif tool_name == "get_shared_context":
        ctx = engine.get_context(room_id, arguments.get("key", ""))
        if not ctx:
            return {
                "content": [
                    {"type": "text", "text": "No shared context found."},
                ],
            }
        lines = ["# Shared Findings\n"]
        for c in ctx:
            lines.append(
                f"**{c['key']}** (by {c['agent_id']}, {c['updated_at']}):",
            )
            lines.append(f"  {c['value']}\n")
        return {"content": [{"type": "text", "text": "\n".join(lines)}]}

    elif tool_name == "get_events":
        events = engine.get_events(
            room_id,
            limit=arguments.get("limit", 20),
            event_type=arguments.get("event_type", ""),
        )
        if not events:
            return {"content": [{"type": "text", "text": "No events yet."}]}
        lines = ["# Recent Events\n"]
        for e in events:
            agent = e.get("agent_id", "system")[:20]
            task = f" task={e['task_id']}" if e.get("task_id") else ""
            payload_str = json.dumps(e["payload"]) if e["payload"] else ""
            lines.append(
                f"[{e['timestamp']}] {e['type']} | {agent}{task} {payload_str}",
            )
        return {"content": [{"type": "text", "text": "\n".join(lines)}]}

    return {
        "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
        "isError": True,
    }


def _handle_remote_tool(
    tool_name: str,
    arguments: Dict[str, Any],
) -> Dict[str, Any]:
    """Handle tool calls via the HTTP bridge (remote mode)."""
    remote = _get_remote()

    def _text(msg: str) -> Dict[str, Any]:
        return {"content": [{"type": "text", "text": msg}]}

    if tool_name == "check_mission_board":
        tasks = remote.get_mission_board(arguments.get("filter_status", ""))
        if not tasks:
            return _text("Mission board is empty. No tasks yet.")
        lines = ["# Mission Board\n"]
        for t in tasks:
            status_icon = {
                "pending": "⬜",
                "claimed": "🔵",
                "in_progress": "🟡",
                "done": "✅",
                "failed": "❌",
            }.get(t.get("status", ""), "❓")
            owner = (
                f" → {t.get('owner_name', 'unknown')}"
                if t.get("owner_agent_id")
                else ""
            )
            blocked = " [BLOCKED]" if t.get("is_blocked") else ""
            prio = (
                f" [{t.get('priority', 'normal').upper()}]"
                if t.get("priority") != "normal"
                else ""
            )
            files = (
                f" files: {t.get('file_scopes', [])}" if t.get("file_scopes") else ""
            )
            note = (
                f"\n   Note: {t.get('progress_note')}" if t.get("progress_note") else ""
            )
            lines.append(
                f"{status_icon} {t.get('task_id', '?')} | {t.get('title', '?')}{prio}{owner}{blocked}{files}{note}",
            )
        return _text("\n".join(lines))

    elif tool_name == "claim_task":
        result = remote.claim_task(
            title=arguments.get("title", ""),
            task_id=arguments.get("task_id", ""),
            file_scopes=arguments.get("file_scopes", []),
            description=arguments.get("description", ""),
            priority=arguments.get("priority", "normal"),
        )
        if result.get("success"):
            return _text(
                f"Claimed task. Lock token: {result.get('lock_token', '')}. Proceed with your work.",
            )
        return _text(
            f"Claim FAILED: {result.get('reason', 'unknown')}. Pick a different task.",
        )

    elif tool_name == "update_task":
        remote.update_task(arguments["task_id"], arguments["progress_note"])
        return _text(f"Updated task {arguments['task_id']}")

    elif tool_name == "complete_task":
        result = remote.complete_task(
            arguments["task_id"],
            arguments.get("summary", ""),
        )
        return _text(
            f"Task {arguments['task_id']} completed."
            if result.get("ok")
            else "Failed to complete.",
        )

    elif tool_name == "fail_task":
        result = remote.fail_task(
            arguments["task_id"],
            arguments.get("reason", ""),
        )
        return _text(
            f"Task {arguments['task_id']} failed."
            if result.get("ok")
            else "Failed to mark task.",
        )

    elif tool_name == "lock_file":
        result = remote.lock_file(arguments["path"])
        if result.get("success"):
            return _text(
                f"Locked {arguments['path']}. Token: {result.get('lock_token', '')}",
            )
        return _text(f"Lock failed: {result.get('reason', 'unknown')}")

    elif tool_name == "unlock_file":
        result = remote.unlock_file(arguments["path"])
        return _text(
            f"{'Unlocked' if result.get('ok') else 'Not found:'} {arguments['path']}",
        )

    elif tool_name == "check_conflicts":
        conflicts = remote.check_conflicts(arguments["paths"])
        if not conflicts:
            return _text("All files are free — safe to edit.")
        lines = ["File conflicts:"] + [
            f"  {c['file']} → locked by {c.get('agent_name', c.get('agent_id', '?'))}"
            for c in conflicts
        ]
        return _text("\n".join(lines))

    elif tool_name == "get_agents":
        agents = remote.get_agents()
        if not agents:
            return _text("No agents connected.")
        lines = ["# War Room Agents\n"]
        for a in agents:
            status_icon = {
                "idle": "🟢",
                "working": "🔵",
                "disconnected": "⚪",
            }.get(
                a.get("status", ""),
                "❓",
            )
            task_info = (
                f" → task {a['current_task_id']}" if a.get("current_task_id") else ""
            )
            caps = (
                ", ".join(a.get("capabilities", []))
                if a.get("capabilities")
                else "general"
            )
            me = " (you)" if a.get("agent_id") == _agent_id else ""
            lines.append(
                f"{status_icon} {a.get('name', '?')}{me} | caps: [{caps}] | {a.get('status', '?')}{task_info}",
            )
        return _text("\n".join(lines))

    elif tool_name == "broadcast_status":
        remote.broadcast_status(arguments["message"])
        return _text(f"Broadcast: {arguments['message']}")

    elif tool_name == "share_finding":
        remote.share_finding(arguments["key"], arguments["value"])
        return _text(f"Shared finding '{arguments['key']}'")

    elif tool_name == "get_shared_context":
        ctx = remote.get_shared_context(arguments.get("key", ""))
        if not ctx:
            return _text("No shared context found.")
        lines = ["# Shared Findings\n"]
        for c in ctx:
            lines.append(
                f"**{c.get('key', '?')}** (by {c.get('agent_id', '?')}, {c.get('updated_at', '?')}):",
            )
            lines.append(f"  {c.get('value', '')}\n")
        return _text("\n".join(lines))

    elif tool_name == "get_events":
        events = remote.get_events(
            arguments.get("limit", 20),
            arguments.get("event_type", ""),
        )
        if not events:
            return _text("No events yet.")
        lines = ["# Recent Events\n"]
        for e in events:
            agent = str(e.get("agent_id", "system"))[:20]
            task = f" task={e['task_id']}" if e.get("task_id") else ""
            payload_str = json.dumps(e.get("payload", {}))
            lines.append(
                f"[{e.get('timestamp', '?')}] {e.get('type', '?')} | {agent}{task} {payload_str}",
            )
        return _text("\n".join(lines))

    return {
        "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
        "isError": True,
    }


# --- MCP stdio Protocol ---


def run_mcp_server():
    """Run the MCP server over stdio (JSON-RPC 2.0)."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [ProwlrHub] %(message)s",
        stream=sys.stderr,  # Logs go to stderr, protocol goes to stdout
    )

    logger.info("ProwlrHub MCP server starting (pid=%d)", os.getpid())

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue

        method = request.get("method", "")
        req_id = request.get("id")
        params = request.get("params", {})

        response: Dict[str, Any] = {"jsonrpc": "2.0", "id": req_id}

        if method == "initialize":
            response["result"] = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "prowlr-hub",
                    "version": "1.0.0",
                },
            }

        elif method == "notifications/initialized":
            continue  # No response needed

        elif method == "tools/list":
            tool_list = []
            for name, spec in TOOLS.items():
                tool_list.append(
                    {
                        "name": name,
                        "description": spec["description"],
                        "inputSchema": spec["inputSchema"],
                    },
                )
            response["result"] = {"tools": tool_list}

        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            try:
                result = handle_tool_call(tool_name, arguments)
                response["result"] = result
            except Exception as e:
                logger.error("Tool call error: %s", e, exc_info=True)
                response["result"] = {
                    "content": [{"type": "text", "text": f"Error: {e}"}],
                    "isError": True,
                }

        elif method == "ping":
            response["result"] = {}

        else:
            response["error"] = {
                "code": -32601,
                "message": f"Method not found: {method}",
            }

        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    run_mcp_server()
