# -*- coding: utf-8 -*-
"""ROAR stdio Transport — local process communication via stdin/stdout.

Uses asyncio subprocess for non-blocking I/O. The parent process spawns
the tool, writes JSON messages to stdin, and reads responses from stdout.

Ref: MCP's primary transport is stdio for local tools. ROAR stdio transport
is wire-compatible with MCP stdio (newline-delimited JSON).

Security: Uses create_subprocess_exec (not shell=True) to prevent injection.
Commands are split into argv list, never passed through a shell.
"""
from __future__ import annotations

import asyncio
import json
import logging
import shlex
from typing import Optional

from ...roar import ConnectionConfig, ROARMessage

logger = logging.getLogger(__name__)


async def stdio_send(
    config: ConnectionConfig,
    message: ROARMessage,
) -> ROARMessage:
    """Send a ROAR message via stdio to a subprocess and return the response.

    The ``config.url`` field is interpreted as the command to execute.
    Format: ``"command arg1 arg2"`` or just ``"command"``.

    Args:
        config: Connection config where ``url`` is the subprocess command.
        message: The message to send.

    Returns:
        The response ROARMessage read from the subprocess's stdout.

    Raises:
        ConnectionError: If the subprocess fails or times out.
    """
    command = config.url
    if not command:
        raise ConnectionError("stdio transport requires a command in config.url")

    # Use shlex.split for safe argument parsing (no shell injection)
    parts = shlex.split(command)
    payload = json.dumps(message.model_dump(by_alias=True))
    timeout = config.timeout_ms / 1000

    try:
        # create_subprocess_exec avoids shell injection (argv, not shell)
        proc = await asyncio.create_subprocess_exec(
            *parts,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout_data, stderr_data = await asyncio.wait_for(
            proc.communicate(input=(payload + "\n").encode()),
            timeout=timeout,
        )

        if proc.returncode != 0:
            stderr_text = stderr_data.decode(errors="replace")[:200]
            raise ConnectionError(
                f"stdio subprocess exited with code {proc.returncode}: {stderr_text}"
            )

        # Read the first complete JSON line from stdout
        for line in stdout_data.decode(errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                return ROARMessage.model_validate(data)
            except (json.JSONDecodeError, Exception):
                continue

        raise ConnectionError("No valid JSON response from stdio subprocess")

    except asyncio.TimeoutError:
        raise ConnectionError(
            f"stdio subprocess timed out after {timeout}s"
        ) from None


class StdioConnection:
    """Persistent stdio connection to a subprocess.

    Keeps the subprocess alive for multiple message exchanges.
    Useful for MCP-compatible tool servers that maintain state.

    Usage::

        conn = StdioConnection("python tool_server.py")
        await conn.start()
        response = await conn.send(message)
        await conn.stop()
    """

    def __init__(self, command: str, timeout_ms: int = 30000) -> None:
        self._command = command
        self._timeout = timeout_ms / 1000
        self._proc: Optional[asyncio.subprocess.Process] = None

    @property
    def running(self) -> bool:
        return self._proc is not None and self._proc.returncode is None

    async def start(self) -> None:
        """Start the subprocess."""
        parts = shlex.split(self._command)
        self._proc = await asyncio.create_subprocess_exec(
            *parts,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        logger.info(
            "stdio subprocess started: %s (pid %d)",
            self._command,
            self._proc.pid,
        )

    async def send(self, message: ROARMessage) -> ROARMessage:
        """Send a message and read the response line."""
        if not self._proc or not self._proc.stdin or not self._proc.stdout:
            raise ConnectionError("stdio subprocess not running")

        payload = json.dumps(message.model_dump(by_alias=True)) + "\n"
        self._proc.stdin.write(payload.encode())
        await self._proc.stdin.drain()

        line = await asyncio.wait_for(
            self._proc.stdout.readline(),
            timeout=self._timeout,
        )
        if not line:
            raise ConnectionError("stdio subprocess closed stdout")

        data = json.loads(line.decode())
        return ROARMessage.model_validate(data)

    async def stop(self) -> None:
        """Terminate the subprocess."""
        if self._proc:
            self._proc.terminate()
            await self._proc.wait()
            logger.info("stdio subprocess stopped")
            self._proc = None
