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
    """Policy for shell command validation.

    Uses a layered approach:
    1. Reject any command containing shell metacharacters that enable
       injection ($(...), backticks, process substitution, etc.)
    2. Reject commands matching known dangerous patterns (denylist)
    3. Only allow commands whose base executable is in the allowlist
    """

    allowed_commands: List[str] = field(
        default_factory=lambda: [
            # Navigation & inspection
            "ls", "pwd", "cat", "head", "tail", "wc", "file", "stat",
            "find", "grep", "rg", "awk", "sed", "sort", "uniq", "diff",
            "tree", "which", "whereis", "echo", "printf", "date",
            # Development (python/python3 excluded — use pip for installs,
            # agent tools for code execution)
            "pip", "pip3",
            "git", "gh", "make", "cmake", "cargo", "go", "rustc",
            "pytest", "black", "ruff", "mypy", "flake8", "isort",
            "pre-commit", "tox",
            # Network (read-only diagnostics — curl/wget excluded for security)
            "ping", "dig", "nslookup", "host",
            # File manipulation (safe)
            "cp", "mv", "mkdir", "touch", "ln", "tar", "zip", "unzip",
            "gzip", "gunzip", "xz",
            # System info
            "uname", "whoami", "hostname", "df", "du", "free", "top",
            "ps", "uptime", "id", "groups",
            # Text processing
            "jq", "yq", "cut", "tr", "tee", "xargs", "less", "more",
            # ProwlrBot
            "prowlr",
        ]
    )

    blocked_patterns: List[str] = field(
        default_factory=lambda: [
            r"\brm\b.*-[rRfF]",  # rm with force/recursive flags
            r"\brm\b\s+-rf\b",  # rm -rf
            r"\bdd\b.*\bof=/dev/",  # dd to device
            r"\bmkfs\b",  # format filesystem
            r"\bchmod\b.*\b777\b",  # chmod 777
            r"\bchmod\b.*\+s\b",  # setuid
            r"\bchown\b.*root",  # chown to root
            r">\s*/dev/[sh]d",  # write to disk device
            r"\b(sudo|su)\b",  # privilege escalation
            r"\bkill\s+-9\s+1\b",  # kill init
            r":()\{.*\|.*&.*\};:",  # fork bomb
            r"\bnc\b.*-[lep]",  # netcat listeners/reverse shells
            r"\bpython[23]?\b.*-c\b",  # python -c (inline code execution)
            r"\bnode\b.*-e\b",  # node -e (inline JS execution)
            r"\bnpx\b",  # npx (downloads and runs arbitrary packages)
            r"\bperl\b.*-e\b",  # perl -e
            r"\bruby\b.*-e\b",  # ruby -e
            r"\beval\b",  # eval
            r"\bexec\b",  # exec
            r"\bsource\b",  # source
        ]
    )

    # Shell metacharacters that enable injection bypasses
    _INJECTION_PATTERNS: List[str] = field(
        default_factory=lambda: [
            r"\$\(",  # $(command substitution)
            r"`",  # backtick substitution
            r"\$\{",  # ${variable expansion}
            r"<\(",  # <(process substitution input)
            r">\(",  # >(process substitution output)
            r"\$'",  # $'...' ANSI-C quoting (hex/octal escapes)
            r"\s+>{1,2}\s*/",  # redirect to absolute path (> /path, >> /path)
            r"\s+2>\s*/",  # stderr redirect to absolute path
        ]
    )

    def check(self, command: str) -> Tuple[bool, str]:
        """Check if a command is allowed.

        Returns (allowed, reason).
        """
        # Layer 0: Reject newlines — prevents multi-line injection bypasses
        if "\n" in command or "\r" in command:
            return False, "Command blocked: newlines are not allowed"

        # Layer 1: Reject injection metacharacters
        for pattern in self._INJECTION_PATTERNS:
            if re.search(pattern, command):
                return False, "Command blocked: contains shell injection metacharacters"

        # Layer 2: Check denylist patterns
        for pattern in self.blocked_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return False, "Command blocked: matches safety pattern"

        # Layer 3: Check allowlist — every segment's base command must be allowed
        # Split on pipes, semicolons, and && / ||
        segments = re.split(r"\s*[;|]\s*|\s*&&\s*|\s*\|\|\s*", command)
        for segment in segments:
            segment = segment.strip()
            if not segment:
                continue

            # Extract the base command (first word, ignoring env vars like FOO=bar)
            parts = segment.split()
            base_cmd = None
            for part in parts:
                if "=" in part and not part.startswith("-"):
                    continue  # Skip env var assignments
                base_cmd = Path(part).name  # Handle /usr/bin/python -> python
                break

            if base_cmd and base_cmd not in self.allowed_commands:
                return False, f"Command blocked: '{base_cmd}' is not in the allowed commands list"

            # Also check denylist on each segment
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
MAX_OUTPUT_BYTES = 1_000_000  # 1 MB cap per stream (stdout/stderr)


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
            stdout_truncated = len(stdout) > MAX_OUTPUT_BYTES
            stderr_truncated = len(stderr) > MAX_OUTPUT_BYTES
            stdout_str = stdout[:MAX_OUTPUT_BYTES].decode(encoding, errors="replace").strip("\n")
            stderr_str = stderr[:MAX_OUTPUT_BYTES].decode(encoding, errors="replace").strip("\n")
            if stdout_truncated:
                stdout_str += f"\n\n[output truncated — {len(stdout):,} bytes total, showing first {MAX_OUTPUT_BYTES:,}]"
            if stderr_truncated:
                stderr_str += f"\n\n[stderr truncated — {len(stderr):,} bytes total, showing first {MAX_OUTPUT_BYTES:,}]"
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
