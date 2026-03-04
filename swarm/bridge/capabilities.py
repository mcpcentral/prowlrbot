"""Capability executor for macOS Bridge API."""

import logging
import subprocess
from typing import Any

logger = logging.getLogger(__name__)


class CapabilityExecutor:
    """Executes capabilities on the local macOS system."""

    CAPABILITIES = {
        "browser_automation": {
            "description": "Control browser via Playwright",
            "parameters": {
                "action": "str",  # navigate, click, type, screenshot
                "url": "str",
                "selector": "str",
                "text": "str"
            }
        },
        "code_execution": {
            "description": "Execute Python code safely",
            "parameters": {
                "code": "str",
                "timeout": "int"
            }
        },
        "file_operations": {
            "description": "Read/write files on the system",
            "parameters": {
                "action": "str",  # read, write, append
                "path": "str",
                "content": "str"
            }
        },
        "shell_command": {
            "description": "Execute shell commands",
            "parameters": {
                "command": "str",
                "cwd": "str",
                "timeout": "int"
            }
        },
        "system_info": {
            "description": "Get system information",
            "parameters": {}
        }
    }

    def __init__(self):
        self.audit_log = []
        logger.info("CapabilityExecutor initialized")

    def list_capabilities(self) -> list:
        """List available capabilities."""
        return [
            {
                "name": name,
                "description": spec["description"],
                "parameters": spec["parameters"]
            }
            for name, spec in self.CAPABILITIES.items()
        ]

    async def execute(self, capability: str, parameters: dict) -> Any:
        """Execute a capability with the given parameters."""
        if capability not in self.CAPABILITIES:
            raise ValueError(f"Unknown capability: {capability}")

        logger.info(f"Executing capability: {capability}")

        # Route to handler
        handler = getattr(self, f"_handle_{capability}", None)
        if not handler:
            raise ValueError(f"Handler not implemented for: {capability}")

        result = await handler(parameters)
        self._audit_log(capability, parameters, result)
        return result

    def _audit_log(self, capability: str, parameters: dict, result: Any):
        """Log capability execution for audit trail."""
        import time
        self.audit_log.append({
            "timestamp": time.time(),
            "capability": capability,
            "parameters": parameters,
            "success": result.get("success", False) if isinstance(result, dict) else True
        })

    async def _handle_shell_command(self, parameters: dict) -> dict:
        """Execute a shell command safely."""
        command = parameters.get("command", "")
        cwd = parameters.get("cwd")
        timeout = parameters.get("timeout", 60)

        if not command:
            raise ValueError("Command is required")

        # Security: block dangerous commands
        blocked = ["rm -rf /", "rm -rf /*", "> /dev/sda", "dd if=/dev/zero"]
        for b in blocked:
            if b in command.lower():
                raise ValueError(f"Blocked dangerous command: {b}")

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_file_operations(self, parameters: dict) -> dict:
        """Handle file read/write operations."""
        action = parameters.get("action")
        path = parameters.get("path", "")
        content = parameters.get("content", "")

        if not path:
            raise ValueError("Path is required")

        # Security: normalize and validate path
        import os
        path = os.path.expanduser(path)
        path = os.path.abspath(path)

        try:
            if action == "read":
                with open(path, "r") as f:
                    return {"success": True, "content": f.read()}
            elif action == "write":
                with open(path, "w") as f:
                    f.write(content)
                return {"success": True, "bytes_written": len(content)}
            elif action == "append":
                with open(path, "a") as f:
                    f.write(content)
                return {"success": True, "bytes_written": len(content)}
            else:
                raise ValueError(f"Unknown action: {action}")
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_system_info(self, parameters: dict) -> dict:
        """Get system information."""
        import platform
        import psutil

        return {
            "success": True,
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total": psutil.disk_usage("/").total,
                "free": psutil.disk_usage("/").free,
                "percent": psutil.disk_usage("/").percent
            }
        }

    async def _handle_code_execution(self, parameters: dict) -> dict:
        """Execute Python code safely (stub - to be implemented)."""
        return {"success": False, "error": "Not yet implemented"}

    async def _handle_browser_automation(self, parameters: dict) -> dict:
        """Browser automation via Playwright (stub - to be implemented)."""
        return {"success": False, "error": "Not yet implemented"}
