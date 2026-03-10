# -*- coding: utf-8 -*-
# flake8: noqa: E501
# pylint: disable=line-too-long
"""The shell command tool."""

import asyncio
import locale
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from agentscope.tool import ToolResponse
from agentscope.message import TextBlock

from prowlrbot.constant import WORKING_DIR


@dataclass
class ShellPolicy:
    """Policy for shell command validation."""

    blocked_patterns: List[str] = field(default_factory=lambda: [
        r"\brm\b.*-[rR].*-[fF]",       # rm -rf variants
        r"\brm\b.*-[fF].*-[rR]",       # rm -fr variants
        r"\brm\b\s+-rf\b",             # rm -rf
        r"\bdd\b.*\bof=/dev/",          # dd to device
        r"\bmkfs\b",                     # format filesystem
        r"\bchmod\b.*\b777\b",          # chmod 777
        r"\bchmod\b.*\+s\b",           # setuid
        r"\bchown\b.*root",             # chown to root
        r">\s*/dev/[sh]d",              # write to disk device
        r"\bcurl\b.*\|\s*\bbash\b",    # curl | bash
        r"\bwget\b.*\|\s*\bbash\b",   # wget | bash
        r"\bcurl\b.*\|\s*\bsh\b",     # curl | sh
        r"\bwget\b.*\|\s*\bsh\b",     # wget | sh
        r"\b(sudo|su)\b",              # privilege escalation
        r"\bkill\s+-9\s+1\b",         # kill init
        r":()\{.*\|.*&.*\};:",         # fork bomb
    ])

    def check(self, command: str) -> Tuple[bool, str]:
        """Check if a command is allowed.

        Returns (allowed, reason).
        """
        for pattern in self.blocked_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return False, "Command blocked: matches safety pattern"

        # Also check individual segments for pipe/semicolon chains
        segments = re.split(r"[;|&]", command)
        for segment in segments:
            segment = segment.strip()
            for pattern in self.blocked_patterns:
                if re.search(pattern, segment, re.IGNORECASE):
                    return False, "Command blocked: matches safety pattern"

        return True, "allowed"


# Module-level default policy
_default_policy = ShellPolicy()


def validate_shell_command(command: str) -> Tuple[bool, str]:
    """Validate a shell command against the default policy."""
    return _default_policy.check(command)


# pylint: disable=too-many-branches
async def execute_shell_command(
    command: str,
    timeout: int = 60,
    cwd: Optional[Path] = None,
) -> ToolResponse:
    """Execute given command and return the return code, standard output and
    error within <returncode></returncode>, <stdout></stdout> and
    <stderr></stderr> tags.

    Args:
        command (`str`):
            The shell command to execute.
        timeout (`int`, defaults to `10`):
            The maximum time (in seconds) allowed for the command to run.
            Default is 60 seconds.
        cwd (`Optional[Path]`, defaults to `None`):
            The working directory for the command execution.
            If None, defaults to WORKING_DIR.

    Returns:
        `ToolResponse`:
            The tool response containing the return code, standard output, and
            standard error of the executed command. If timeout occurs, the
            return code will be -1 and stderr will contain timeout information.
    """

    cmd = (command or "").strip()

    # Validate command safety
    allowed, reason = validate_shell_command(cmd)
    if not allowed:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: {reason}",
                ),
            ],
        )

    # Set working directory
    working_dir = cwd if cwd is not None else WORKING_DIR

    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            bufsize=0,
            cwd=str(working_dir),
        )

        try:
            await asyncio.wait_for(proc.wait(), timeout=timeout)
            stdout, stderr = await proc.communicate()
            encoding = locale.getpreferredencoding(False) or "utf-8"
            stdout_str = stdout.decode(encoding, errors="replace").strip("\n")
            stderr_str = stderr.decode(encoding, errors="replace").strip("\n")
            returncode = proc.returncode

        except asyncio.TimeoutError:
            # Handle timeout
            stderr_suffix = (
                f"⚠️ TimeoutError: The command execution exceeded "
                f"the timeout of {timeout} seconds. "
                f"Please consider increasing the timeout value if this command "
                f"requires more time to complete."
            )
            returncode = -1
            try:
                proc.terminate()
                # Wait a bit for graceful termination
                try:
                    await asyncio.wait_for(proc.wait(), timeout=1)
                except asyncio.TimeoutError:
                    # Force kill if graceful termination fails
                    proc.kill()
                    await proc.wait()

                stdout, stderr = await proc.communicate()
                encoding = locale.getpreferredencoding(False) or "utf-8"
                stdout_str = stdout.decode(encoding, errors="replace").strip(
                    "\n",
                )
                stderr_str = stderr.decode(encoding, errors="replace").strip(
                    "\n",
                )
                if stderr_str:
                    stderr_str += f"\n{stderr_suffix}"
                else:
                    stderr_str = stderr_suffix
            except ProcessLookupError:
                stdout_str = ""
                stderr_str = stderr_suffix

        # Format the response in a human-friendly way
        if returncode == 0:
            # Success case: just show the output
            if stdout_str:
                response_text = stdout_str
            else:
                response_text = "Command executed successfully (no output)."
        else:
            # Error case: show detailed information
            response_parts = [f"Command failed with exit code {returncode}."]
            if stdout_str:
                response_parts.append(f"\n[stdout]\n{stdout_str}")
            if stderr_str:
                response_parts.append(f"\n[stderr]\n{stderr_str}")
            response_text = "".join(response_parts)

        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=response_text,
                ),
            ],
        )

    except Exception as e:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: Shell command execution failed due to \n{e}",
                ),
            ],
        )
