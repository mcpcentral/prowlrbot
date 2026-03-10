# -*- coding: utf-8 -*-
"""Prompt injection guardrails and output filtering."""

import re
from dataclasses import dataclass


@dataclass
class SanitizationResult:
    """Result of input sanitization check."""

    safe: bool
    reason: str = ""


class InputSanitizer:
    """Multi-layer prompt injection detection."""

    INJECTION_PATTERNS = [
        # Role switching attempts
        (r"(?i)ignore\s+(all\s+)?previous\s+instructions", "Possible role-switching injection"),
        (r"(?i)forget\s+(all\s+)?your\s+(previous\s+)?instructions", "Possible role-switching injection"),
        (r"(?i)you\s+are\s+now\s+a\s+different", "Possible role-switching injection"),
        (r"(?i)disregard\s+(all\s+)?(prior|previous|above)", "Possible role-switching injection"),
        # System prompt override
        (r"(?i)^system\s*:\s*you\s+are\s+now", "Possible system prompt override"),
        (r"(?i)^system\s*:\s*ignore", "Possible system prompt override"),
        (r"(?i)\[system\]\s*override", "Possible system prompt override"),
        # Jailbreak patterns
        (r"(?i)DAN\s+mode", "Possible jailbreak attempt"),
        (r"(?i)developer\s+mode\s+enabled", "Possible jailbreak attempt"),
    ]

    def check(self, text: str) -> SanitizationResult:
        """Check user input for prompt injection patterns."""
        for pattern, reason in self.INJECTION_PATTERNS:
            if re.search(pattern, text):
                return SanitizationResult(safe=False, reason=reason)
        return SanitizationResult(safe=True)


class OutputFilter:
    """Filter sensitive data from agent output."""

    SECRET_PATTERNS = [
        # API keys (order matters — more specific patterns first)
        (r"sk-ant-[a-zA-Z0-9\-_]{20,}", "sk-***"),
        (r"sk-proj-[a-zA-Z0-9\-_]{20,}", "sk-***"),
        (r"sk-[a-zA-Z0-9\-_]{20,}", "sk-***"),
        (r"gsk_[a-zA-Z0-9]{20,}", "gsk_***"),
        # Bearer tokens (JWT-like)
        (r"Bearer\s+eyJ[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+", "Bearer [REDACTED]"),
        # Generic key=value secrets
        (r"(?i)(api[_-]?key|secret|token|password)\s*=\s*\S+", r"\1=[REDACTED]"),
    ]

    def filter(self, text: str) -> str:
        """Remove sensitive patterns from agent output."""
        result = text
        for pattern, replacement in self.SECRET_PATTERNS:
            result = re.sub(pattern, replacement, result)
        return result
