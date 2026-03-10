# -*- coding: utf-8 -*-
"""Content diffing engine."""
from __future__ import annotations

import difflib
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DiffResult:
    """Result of comparing two content strings."""

    changed: bool
    summary: str
    unified_diff: str


def has_changed(old: Optional[str], new: Optional[str]) -> bool:
    """Return True if content has changed. First run (old=None) counts as changed."""
    if old is None:
        return True
    return old != new


def diff_text(old: Optional[str], new: Optional[str]) -> DiffResult:
    """Produce a structured diff between old and new content.

    If *old* is None this is treated as the first observation (always changed).
    """
    if old is None:
        return DiffResult(
            changed=True,
            summary="Initial content captured",
            unified_diff="",
        )

    if old == new:
        return DiffResult(changed=False, summary="No changes", unified_diff="")

    old_lines = old.splitlines(keepends=True)
    new_lines = (new or "").splitlines(keepends=True)
    unified = "".join(
        difflib.unified_diff(old_lines, new_lines, fromfile="before", tofile="after")
    )

    # Build a short human-readable summary.
    added = sum(1 for l in unified.splitlines() if l.startswith("+") and not l.startswith("+++"))
    removed = sum(1 for l in unified.splitlines() if l.startswith("-") and not l.startswith("---"))
    summary = f"{added} line(s) added, {removed} line(s) removed"

    return DiffResult(changed=True, summary=summary, unified_diff=unified)
