# -*- coding: utf-8 -*-
# flake8: noqa: E501
# pylint: disable=line-too-long
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

from agentscope.message import TextBlock
from agentscope.tool import ToolResponse

from ...constant import WORKING_DIR

# Legacy secret path — emit deprecation warning on first access
_LEGACY_SECRET_DIR = Path.home() / ".copaw.secret"
if _LEGACY_SECRET_DIR.exists():
    logger.warning(
        "Deprecated: ~/.copaw.secret detected. "
        "Migrate secrets to ~/.prowlrbot.secret/ and remove the old directory. "
        "Legacy path support will be removed in v1.0.",
    )

# Directories that are always blocked
_BLOCKED_PREFIXES = [
    Path.home() / ".ssh",
    Path.home() / ".prowlrbot.secret",
    _LEGACY_SECRET_DIR,
    Path.home() / ".aws",
    Path.home() / ".gnupg",
    Path.home() / ".kube",
    Path.home() / ".docker",
    Path.home() / ".config",
    Path.home() / ".npmrc",
    Path.home() / ".pypirc",
    Path.home() / ".git-credentials",
    Path.home() / ".bash_history",
    Path.home() / ".zsh_history",
    Path.home() / ".netrc",
    Path("/etc"),
    Path("/dev"),
    Path("/proc"),
    Path("/sys"),
]

# Directories that are always allowed
_ALLOWED_PREFIXES = [
    Path("/tmp"),
]


def validate_file_path(file_path: str) -> bool:
    """Validate that a file path is safe to access.

    Returns True if the path is within allowed directories
    and not in any blocked directory. Rejects symlinks whose
    targets fall outside allowed directories (TOCTOU mitigation).
    """
    try:
        p = Path(file_path)
        resolved = p.resolve()

        # If the path is a symlink, verify the target is also allowed
        if p.is_symlink():
            target = p.resolve(strict=False)
            if str(target) != str(resolved):
                return False
    except (ValueError, OSError):
        return False

    # Check blocked paths first (component-level matching, not string prefix)
    for blocked in _BLOCKED_PREFIXES:
        try:
            blocked_resolved = blocked.resolve()
            if resolved == blocked_resolved or resolved.is_relative_to(
                blocked_resolved,
            ):
                return False
        except (ValueError, OSError):
            continue

    # Always allow /tmp
    for allowed in _ALLOWED_PREFIXES:
        try:
            allowed_resolved = allowed.resolve()
            if resolved == allowed_resolved or resolved.is_relative_to(
                allowed_resolved,
            ):
                return True
        except (ValueError, OSError):
            continue

    # Allow WORKING_DIR
    try:
        wd = WORKING_DIR.resolve()
        if resolved == wd or resolved.is_relative_to(wd):
            return True
    except (ValueError, OSError):
        pass

    return False


def _resolve_file_path(file_path: str) -> str:
    """Resolve file path: use absolute path as-is,
    resolve relative path from WORKING_DIR.

    Args:
        file_path: The input file path (absolute or relative).

    Returns:
        The resolved absolute file path as string.
    """
    path = Path(file_path)
    if path.is_absolute():
        return str(path)
    else:
        return str(WORKING_DIR / file_path)


async def read_file(  # pylint: disable=too-many-return-statements
    file_path: str,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
) -> ToolResponse:
    """Read a file. Relative paths resolve from WORKING_DIR.

    Use start_line/end_line to read a specific line range (output includes
    line numbers). Omit both to read the full file.

    Args:
        file_path (`str`):
            Path to the file.
        start_line (`int`, optional):
            First line to read (1-based, inclusive).
        end_line (`int`, optional):
            Last line to read (1-based, inclusive).
    """

    file_path = _resolve_file_path(file_path)

    if not validate_file_path(file_path):
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: Access denied — path '{file_path}' is outside allowed directories.",
                ),
            ],
        )

    if not os.path.exists(file_path):
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: The file {file_path} does not exist.",
                ),
            ],
        )

    if not os.path.isfile(file_path):
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: The path {file_path} is not a file.",
                ),
            ],
        )

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            all_lines = f.readlines()

        range_requested = start_line is not None or end_line is not None

        if range_requested:
            total = len(all_lines)
            s = max(1, start_line if start_line is not None else 1)
            e = min(total, end_line if end_line is not None else total)

            if s > total:
                return ToolResponse(
                    content=[
                        TextBlock(
                            type="text",
                            text=(
                                f"Error: start_line {s} exceeds file length "
                                f"({total} lines) in {file_path}."
                            ),
                        ),
                    ],
                )

            if s > e:
                return ToolResponse(
                    content=[
                        TextBlock(
                            type="text",
                            text=(
                                f"Error: start_line ({s}) is greater than "
                                f"end_line ({e}) in {file_path}."
                            ),
                        ),
                    ],
                )

            selected = all_lines[s - 1 : e]
            content = "".join(selected)
            header = f"{file_path}  (lines {s}-{e} of {total})\n"
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=header + content,
                    ),
                ],
            )
        else:
            content = "".join(all_lines)
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=content,
                    ),
                ],
            )

    except Exception as e:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: Read file failed due to \n{e}",
                ),
            ],
        )


async def write_file(
    file_path: str,
    content: str,
) -> ToolResponse:
    """Create or overwrite a file. Relative paths resolve from WORKING_DIR.

    Args:
        file_path (`str`):
            Path to the file.
        content (`str`):
            Content to write.
    """

    if not file_path:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text="Error: No `file_path` provide.",
                ),
            ],
        )

    file_path = _resolve_file_path(file_path)

    if not validate_file_path(file_path):
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: Access denied — path '{file_path}' is outside allowed directories.",
                ),
            ],
        )

    try:
        parent = Path(file_path).parent
        # Validate parent directory is also within allowed paths
        if not validate_file_path(str(parent)):
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"Error: Access denied — parent directory is outside allowed directories.",
                    ),
                ],
            )
        parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Wrote {len(content)} bytes to {file_path}.",
                ),
            ],
        )
    except Exception as e:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: Write file failed due to \n{e}",
                ),
            ],
        )


async def edit_file(
    file_path: str,
    old_text: str,
    new_text: str,
) -> ToolResponse:
    """Find-and-replace text in a file. All occurrences of old_text are
    replaced with new_text. Relative paths resolve from WORKING_DIR.

    Args:
        file_path (`str`):
            Path to the file.
        old_text (`str`):
            Exact text to find.
        new_text (`str`):
            Replacement text.
    """

    response = await read_file(file_path=file_path)
    if response.content and len(response.content) > 0:
        error_text = response.content[0].get("text", "")
        if error_text.startswith("Error:"):
            return response
    if not response.content or len(response.content) == 0:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: Failed to read file {file_path}.",
                ),
            ],
        )

    content = response.content[0].get("text", "")
    if old_text not in content:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: The text to replace was not found in {file_path}.",
                ),
            ],
        )

    new_content = content.replace(old_text, new_text)
    write_response = await write_file(file_path=file_path, content=new_content)

    if write_response.content and len(write_response.content) > 0:
        write_text = write_response.content[0].get("text", "")
        if write_text.startswith("Error:"):
            return write_response

    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=f"Successfully replaced text in {file_path}.",
            ),
        ],
    )


async def append_file(
    file_path: str,
    content: str,
) -> ToolResponse:
    """Append content to the end of a file. Relative paths resolve from
    WORKING_DIR.

    Args:
        file_path (`str`):
            Path to the file.
        content (`str`):
            Content to append.
    """

    if not file_path:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text="Error: No `file_path` provide.",
                ),
            ],
        )

    file_path = _resolve_file_path(file_path)

    if not validate_file_path(file_path):
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: Access denied — path '{file_path}' is outside allowed directories.",
                ),
            ],
        )

    try:
        parent = Path(file_path).parent
        if not validate_file_path(str(parent)):
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"Error: Access denied — parent directory is outside allowed directories.",
                    ),
                ],
            )
        parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "a", encoding="utf-8") as file:
            file.write(content)
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Appended {len(content)} bytes to {file_path}.",
                ),
            ],
        )
    except Exception as e:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: Append file failed due to \n{e}",
                ),
            ],
        )
