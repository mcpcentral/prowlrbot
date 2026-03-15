# -*- coding: utf-8 -*-
"""WebSocket terminal — PTY subprocess pipe over WebSocket.

Only available on Unix/Linux where the ``pty`` module is present.
On Windows this module raises ``ImportError`` and the router is skipped.
"""

from __future__ import annotations

import asyncio
import fcntl
import json
import logging
import os
import pty
import struct
import termios
import uuid
from typing import Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(prefix="/ws/terminal", tags=["terminal"])
logger = logging.getLogger(__name__)

_sessions: Dict[str, dict] = {}


def _set_window_size(fd: int, rows: int, cols: int) -> None:
    winsize = struct.pack("HHHH", rows, cols, 0, 0)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)


@router.websocket("/{session_id}")
async def terminal_ws(websocket: WebSocket, session_id: str) -> None:
    """Expose a PTY bash session over WebSocket."""
    await websocket.accept()
    master_fd, slave_fd = pty.openpty()
    pid = os.fork()

    if pid == 0:  # child process
        os.close(master_fd)
        os.setsid()
        fcntl.ioctl(slave_fd, termios.TIOCSCTTY, 0)
        os.dup2(slave_fd, 0)
        os.dup2(slave_fd, 1)
        os.dup2(slave_fd, 2)
        if slave_fd > 2:
            os.close(slave_fd)
        env = {**os.environ, "TERM": "xterm-256color"}
        os.execvpe("bash", ["bash", "--login"], env)
        os._exit(1)

    # parent process
    os.close(slave_fd)
    _sessions[session_id] = {"pid": pid, "fd": master_fd}
    loop = asyncio.get_running_loop()

    async def pty_to_ws() -> None:
        while True:
            try:
                data = await loop.run_in_executor(
                    None,
                    lambda: os.read(master_fd, 4096),
                )
                await websocket.send_bytes(data)
            except (OSError, WebSocketDisconnect, RuntimeError):
                break

    async def ws_to_pty() -> None:
        while True:
            try:
                msg = await websocket.receive()
                if "bytes" in msg and msg["bytes"]:
                    os.write(master_fd, msg["bytes"])
                elif "text" in msg and msg["text"]:
                    text = msg["text"]
                    try:
                        payload = json.loads(text)
                        if payload.get("type") == "resize":
                            _set_window_size(
                                master_fd,
                                int(payload.get("rows", 24)),
                                int(payload.get("cols", 80)),
                            )
                    except (json.JSONDecodeError, TypeError):
                        os.write(master_fd, text.encode())
            except (WebSocketDisconnect, RuntimeError):
                break

    try:
        await asyncio.gather(pty_to_ws(), ws_to_pty())
    finally:
        os.close(master_fd)
        try:
            os.kill(pid, 9)
            os.waitpid(pid, os.WNOHANG)
        except OSError:
            pass
        _sessions.pop(session_id, None)
        logger.debug("Terminal session %s closed", session_id)
