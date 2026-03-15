# -*- coding: utf-8 -*-
"""Prompt injection defense, output filtering, and secret redaction.

Provides three layers of protection:

- **InputSanitizer** — detects and strips prompt-injection attempts from
  user-supplied text before it reaches the agent.
- **OutputFilter** — redacts sensitive patterns (API keys, secrets) from
  agent output before it is returned to the user or logged.
- **SecretRedactor** — replaces any string that matches a known environment
  variable value with ``[REDACTED]``.
"""

from __future__ import annotations

import base64
import logging
import os
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Sequence

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# InputSanitizer
# ---------------------------------------------------------------------------

# Layer 1 — known prompt-injection phrases / role-switching patterns.
# Each tuple is (compiled_regex, human-readable label).
_INJECTION_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Direct instruction overrides
    (
        re.compile(
            r"ignore\s+(all\s+)?(previous|prior|above|earlier|preceding)"
            r"\s+(instructions?|prompts?|rules?|guidelines?|directions?)",
            re.IGNORECASE,
        ),
        "instruction-override",
    ),
    (
        re.compile(
            r"disregard\s+(all\s+)?(previous|prior|above|earlier)"
            r"\s+(instructions?|prompts?|rules?|context)",
            re.IGNORECASE,
        ),
        "instruction-override",
    ),
    (
        re.compile(
            r"forget\s+(everything|all|your)\s+(you\s+)?"
            r"(know|were told|instructions?|rules?)",
            re.IGNORECASE,
        ),
        "instruction-override",
    ),
    # Role / identity switching
    (
        re.compile(
            r"you\s+are\s+now\s+(a|an|the|my)?\s*\w+",
            re.IGNORECASE,
        ),
        "role-switch",
    ),
    (
        re.compile(
            r"(pretend|act|behave|respond)\s+(like|as\s+if)\s+you\s+(are|were)",
            re.IGNORECASE,
        ),
        "role-switch",
    ),
    (
        re.compile(
            r"from\s+now\s+on[,.]?\s+you\s+(are|will\s+be|shall\s+be)",
            re.IGNORECASE,
        ),
        "role-switch",
    ),
    (
        re.compile(
            r"switch\s+(to|into)\s+(a\s+)?(\w+\s+)?(mode|persona|role|character)",
            re.IGNORECASE,
        ),
        "role-switch",
    ),
    (
        re.compile(
            r"enter\s+(DAN|dev(eloper)?|god|admin|root|sudo|jailbreak|unrestricted)"
            r"\s*(mode)?",
            re.IGNORECASE,
        ),
        "role-switch",
    ),
    # System prompt extraction
    (
        re.compile(
            r"(show|reveal|display|print|output|repeat|echo|give\s+me)"
            r"\s+(your\s+)?(system\s+prompt|initial\s+prompt|instructions"
            r"|hidden\s+prompt|original\s+prompt|secret\s+instructions?)",
            re.IGNORECASE,
        ),
        "prompt-extraction",
    ),
    (
        re.compile(
            r"what\s+(are|is|were)\s+your\s+(system|initial|original|hidden|secret)"
            r"\s+(prompt|instructions?|rules?|guidelines?)",
            re.IGNORECASE,
        ),
        "prompt-extraction",
    ),
    # Fake system / assistant message injection
    (
        re.compile(
            r"^(system|assistant)\s*:\s*",
            re.IGNORECASE | re.MULTILINE,
        ),
        "role-injection",
    ),
    (
        re.compile(
            r"\[SYSTEM\]|\[INST\]|\[/INST\]|<<SYS>>|<\|system\|>|<\|assistant\|>"
            r"|<\|user\|>|<\|im_start\|>|<\|im_end\|>",
            re.IGNORECASE,
        ),
        "special-token-injection",
    ),
    (
        re.compile(
            r"```\s*(system|prompt|instructions?)\b",
            re.IGNORECASE,
        ),
        "fenced-injection",
    ),
    # Instruction boundary attacks
    (
        re.compile(
            r"(new\s+instructions?|updated?\s+instructions?|revised\s+instructions?)"
            r"\s*[:=]",
            re.IGNORECASE,
        ),
        "instruction-boundary",
    ),
    (
        re.compile(
            r"(override|overwrite|replace|bypass)\s+(the\s+)?"
            r"(system|safety|security|content)\s+(prompt|filter|rules?|policy|guardrails?)",
            re.IGNORECASE,
        ),
        "safety-bypass",
    ),
    # Tool / function abuse
    (
        re.compile(
            r"(execute|run|call|invoke)\s+(this\s+)?(shell|bash|cmd|command|code|script)"
            r"\s*[:=]?\s*(rm\s+-rf|sudo|chmod|curl\s+.*\|\s*(ba)?sh|wget\s+.*\|\s*(ba)?sh)",
            re.IGNORECASE,
        ),
        "dangerous-command",
    ),
    # Markdown / HTML injection for UI rendering
    (
        re.compile(
            r"<script[\s>]|javascript\s*:|on(load|error|click)\s*=",
            re.IGNORECASE,
        ),
        "xss-attempt",
    ),
]

# Layer 2 — unicode normalization attack patterns.
# Characters that look like ASCII but are from different unicode blocks.
_CONFUSABLE_RANGES: list[tuple[int, int]] = [
    # Fullwidth Latin
    (0xFF01, 0xFF5E),
    # Mathematical Alphanumeric Symbols (selected)
    (0x1D400, 0x1D7FF),
    # Enclosed Alphanumerics
    (0x2460, 0x24FF),
    # Letterlike Symbols
    (0x2100, 0x214F),
]

# Zero-width and invisible characters (used to smuggle text).
_INVISIBLE_CHARS = re.compile(
    r"[\u200b\u200c\u200d\u200e\u200f\u2060\u2061\u2062\u2063\u2064"
    r"\ufeff\u00ad\u034f\u061c\u180e\u2028\u2029\u202a-\u202e"
    r"\u2066-\u2069\ufff9-\ufffb]",
)

# Homoglyph mapping — common confusable characters → ASCII equivalents.
_HOMOGLYPHS: dict[str, str] = {
    "\u0410": "A",  # Cyrillic А
    "\u0412": "B",  # Cyrillic В
    "\u0421": "C",  # Cyrillic С
    "\u0415": "E",  # Cyrillic Е
    "\u041d": "H",  # Cyrillic Н
    "\u041a": "K",  # Cyrillic К
    "\u041c": "M",  # Cyrillic М
    "\u041e": "O",  # Cyrillic О
    "\u0420": "P",  # Cyrillic Р
    "\u0422": "T",  # Cyrillic Т
    "\u0425": "X",  # Cyrillic Х
    "\u0430": "a",  # Cyrillic а
    "\u0435": "e",  # Cyrillic е
    "\u043e": "o",  # Cyrillic о
    "\u0440": "p",  # Cyrillic р
    "\u0441": "c",  # Cyrillic с
    "\u0443": "y",  # Cyrillic у
    "\u0445": "x",  # Cyrillic х
    "\u0456": "i",  # Cyrillic і
    "\u0458": "j",  # Cyrillic ј
    "\u0455": "s",  # Cyrillic ѕ
    "\u04bb": "h",  # Cyrillic һ
    "\u0501": "d",  # Cyrillic ԁ
    "\u051b": "q",  # Cyrillic ԛ
}

# Base64 content detection — looks for base64 blocks with injection keywords
# when decoded.
_BASE64_BLOCK = re.compile(
    r"(?:^|[\s\"'])([A-Za-z0-9+/]{20,}={0,2})(?:$|[\s\"'])",
    re.MULTILINE,
)

_DECODED_INJECTION_KEYWORDS = re.compile(
    r"ignore\s+previous|system\s*prompt|you\s+are\s+now|new\s+instructions"
    r"|override\s+instructions|disregard|forget\s+everything",
    re.IGNORECASE,
)


@dataclass
class InputSanitizer:
    """Multi-layer prompt injection defense.

    Parameters
    ----------
    max_length:
        Maximum allowed input length in characters. Inputs exceeding this
        are truncated and a warning is emitted.
    strip_injections:
        If True, matched injection patterns are removed from the text.
        If False, they are left in place but still reported as warnings.
    """

    max_length: int = 50_000
    strip_injections: bool = True

    def sanitize(self, user_input: str) -> tuple[str, list[str]]:
        """Sanitize *user_input* and return ``(cleaned_text, warnings)``.

        The warnings list contains human-readable descriptions of every
        suspicious pattern that was detected (and optionally stripped).
        """
        warnings: list[str] = []
        text = user_input

        # --- Layer 3: length validation (run first so later layers
        #     don't process absurdly long inputs) ---
        if len(text) > self.max_length:
            warnings.append(
                f"Input truncated from {len(text)} to {self.max_length} characters",
            )
            text = text[: self.max_length]

        # --- Layer 2: unicode normalization / encoded attacks ---
        text, unicode_warnings = self._normalize_unicode(text)
        warnings.extend(unicode_warnings)

        text, b64_warnings = self._detect_base64_injections(text)
        warnings.extend(b64_warnings)

        # --- Layer 1: known injection patterns ---
        text, pattern_warnings = self._scan_injection_patterns(text)
        warnings.extend(pattern_warnings)

        if warnings:
            logger.warning(
                "InputSanitizer detected %d issue(s): %s",
                len(warnings),
                "; ".join(warnings),
            )

        return text, warnings

    def is_suspicious(self, text: str) -> bool:
        """Quick boolean check — does *text* contain any injection signal?"""
        # Fast-path: check injection patterns.
        for pattern, _label in _INJECTION_PATTERNS:
            if pattern.search(text):
                return True
        # Check for invisible characters.
        if _INVISIBLE_CHARS.search(text):
            return True
        # Check for homoglyphs in ASCII-dominant text.
        if self._has_suspicious_homoglyphs(text):
            return True
        return False

    # -- internal helpers --------------------------------------------------

    def _scan_injection_patterns(self, text: str) -> tuple[str, list[str]]:
        warnings: list[str] = []
        for pattern, label in _INJECTION_PATTERNS:
            matches = pattern.findall(text)
            if matches:
                warnings.append(
                    f"Injection pattern [{label}] detected ({len(matches)} match(es))",
                )
                if self.strip_injections:
                    text = pattern.sub("", text)
        return text, warnings

    def _normalize_unicode(self, text: str) -> tuple[str, list[str]]:
        warnings: list[str] = []

        # Strip invisible / zero-width characters.
        invisible_count = len(_INVISIBLE_CHARS.findall(text))
        if invisible_count:
            warnings.append(
                f"Removed {invisible_count} invisible/zero-width character(s)",
            )
            text = _INVISIBLE_CHARS.sub("", text)

        # Normalize homoglyphs to ASCII equivalents.
        replaced = 0
        chars: list[str] = []
        for ch in text:
            if ch in _HOMOGLYPHS:
                chars.append(_HOMOGLYPHS[ch])
                replaced += 1
            else:
                chars.append(ch)
        if replaced:
            warnings.append(
                f"Normalized {replaced} homoglyph character(s) to ASCII",
            )
            text = "".join(chars)

        # Apply NFC normalization to collapse combining sequences.
        nfc = unicodedata.normalize("NFC", text)
        if nfc != text:
            warnings.append("Applied NFC unicode normalization")
            text = nfc

        return text, warnings

    def _detect_base64_injections(self, text: str) -> tuple[str, list[str]]:
        warnings: list[str] = []
        for m in _BASE64_BLOCK.finditer(text):
            candidate = m.group(1)
            try:
                decoded = base64.b64decode(candidate, validate=True).decode(
                    "utf-8",
                    errors="ignore",
                )
            except Exception:
                continue
            if _DECODED_INJECTION_KEYWORDS.search(decoded):
                warnings.append(
                    f"Base64-encoded injection detected (decoded: "
                    f"{decoded[:80]!r}...)",
                )
                if self.strip_injections:
                    text = text.replace(
                        candidate,
                        "[BASE64_INJECTION_REMOVED]",
                    )
        return text, warnings

    @staticmethod
    def _has_suspicious_homoglyphs(text: str) -> bool:
        """Return True if text contains characters from known confusable ranges."""
        for ch in text:
            if ch in _HOMOGLYPHS:
                return True
            cp = ord(ch)
            for lo, hi in _CONFUSABLE_RANGES:
                if lo <= cp <= hi:
                    return True
        return False


# ---------------------------------------------------------------------------
# OutputFilter
# ---------------------------------------------------------------------------

# Compiled regex patterns for common secret / credential formats.
_REDACTED_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # OpenAI
    (re.compile(r"sk-[A-Za-z0-9_-]{20,}"), "openai-key"),
    # OpenAI project keys
    (re.compile(r"sk-proj-[A-Za-z0-9_-]{20,}"), "openai-project-key"),
    # Anthropic
    (re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"), "anthropic-key"),
    # xAI / Grok
    (re.compile(r"xai-[A-Za-z0-9_-]{20,}"), "xai-key"),
    # Groq
    (re.compile(r"gsk_[A-Za-z0-9_-]{20,}"), "groq-key"),
    # Google AI
    (re.compile(r"AIza[A-Za-z0-9_-]{30,}"), "google-api-key"),
    # AWS access key
    (re.compile(r"AKIA[A-Z0-9]{16}"), "aws-access-key"),
    # AWS secret key (40 chars, base64-ish)
    (
        re.compile(r"(?<![A-Za-z0-9/+])[A-Za-z0-9/+=]{40}(?![A-Za-z0-9/+=])"),
        "possible-aws-secret",
    ),
    # GitHub tokens
    (re.compile(r"gh[pousr]_[A-Za-z0-9_]{36,}"), "github-token"),
    (re.compile(r"github_pat_[A-Za-z0-9_]{22,}"), "github-pat"),
    # Slack tokens
    (re.compile(r"xox[bporas]-[A-Za-z0-9-]{10,}"), "slack-token"),
    # Discord bot token
    (
        re.compile(
            r"[MN][A-Za-z0-9]{23,}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{27,}",
        ),
        "discord-token",
    ),
    # Stripe
    (re.compile(r"sk_live_[A-Za-z0-9]{20,}"), "stripe-secret-key"),
    (re.compile(r"sk_test_[A-Za-z0-9]{20,}"), "stripe-test-key"),
    (re.compile(r"rk_live_[A-Za-z0-9]{20,}"), "stripe-restricted-key"),
    # Twilio
    (re.compile(r"SK[a-f0-9]{32}"), "twilio-api-key"),
    # SendGrid
    (
        re.compile(r"SG\.[A-Za-z0-9_-]{22,}\.[A-Za-z0-9_-]{20,}"),
        "sendgrid-key",
    ),
    # Mailgun
    (re.compile(r"key-[A-Za-z0-9]{32}"), "mailgun-key"),
    # Private keys in PEM format
    (
        re.compile(
            r"-----BEGIN\s+(RSA\s+|EC\s+|DSA\s+|OPENSSH\s+)?PRIVATE\s+KEY-----",
        ),
        "private-key",
    ),
    # Bearer tokens in output
    (
        re.compile(r"[Bb]earer\s+[A-Za-z0-9_\-.]{20,}"),
        "bearer-token",
    ),
    # Generic long hex secrets (64+ hex chars, like SHA-256 hashes used as keys)
    (
        re.compile(r"(?<![A-Fa-f0-9])[A-Fa-f0-9]{64}(?![A-Fa-f0-9])"),
        "hex-secret",
    ),
    # JWT tokens
    (
        re.compile(
            r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
        ),
        "jwt-token",
    ),
    # HuggingFace
    (re.compile(r"hf_[A-Za-z0-9]{30,}"), "huggingface-token"),
    # Databricks
    (re.compile(r"dapi[a-f0-9]{32}"), "databricks-token"),
    # Supabase
    (re.compile(r"sbp_[A-Za-z0-9]{40,}"), "supabase-key"),
]


@dataclass
class OutputFilter:
    """Redact sensitive data from agent output before returning to the user.

    Parameters
    ----------
    allowlist:
        A set of pattern labels (e.g. ``{"bearer-token"}``) that should
        *not* be redacted. Useful when a workflow legitimately needs to
        output certain token formats.
    workspace_root:
        If set, file paths outside this directory tree are redacted in the
        output. Paths inside the workspace are left alone.
    """

    allowlist: set[str] = field(default_factory=set)
    workspace_root: str | None = None

    def filter(self, agent_output: str) -> str:
        """Return *agent_output* with sensitive patterns replaced by
        ``[REDACTED:<label>]``.
        """
        text = agent_output

        # Redact known secret patterns.
        for pattern, label in _REDACTED_PATTERNS:
            if label in self.allowlist:
                continue
            text = pattern.sub(f"[REDACTED:{label}]", text)

        # Redact file paths outside the workspace.
        if self.workspace_root:
            text = self._redact_external_paths(text)

        return text

    def _redact_external_paths(self, text: str) -> str:
        """Replace absolute file paths that fall outside the workspace."""
        assert self.workspace_root is not None
        ws = os.path.realpath(self.workspace_root)

        # Match Unix-style absolute paths.
        path_pattern = re.compile(
            r"(?<!\w)(/(?:[\w.+@-]+/)*[\w.+@-]+(?:\.\w+)?)",
        )
        # Match Windows-style absolute paths.
        win_pattern = re.compile(
            r"(?<!\w)([A-Za-z]:\\(?:[\w.+@\s-]+\\)*[\w.+@\s-]+(?:\.\w+)?)",
        )

        def _maybe_redact(m: re.Match[str]) -> str:
            p = m.group(1)
            try:
                real = os.path.realpath(p)
            except (OSError, ValueError):
                return p
            # Keep paths inside workspace or common safe prefixes.
            if real.startswith(ws):
                return p
            # Keep very short paths (likely not secrets, e.g. /tmp).
            if len(p) < 6:
                return p
            return "[REDACTED:external-path]"

        text = path_pattern.sub(_maybe_redact, text)
        text = win_pattern.sub(_maybe_redact, text)
        return text


# ---------------------------------------------------------------------------
# SecretRedactor
# ---------------------------------------------------------------------------


class SecretRedactor:
    """Replace any string matching a known environment variable value with
    ``[REDACTED]``.

    At initialisation the redactor snapshots all current environment variable
    values that look like secrets (length >= *min_value_length*) and
    optionally those whose keys match *secret_key_patterns*.

    Parameters
    ----------
    min_value_length:
        Minimum length of an env var value for it to be considered
        a candidate secret. Very short values (like "1" or "true") are
        excluded to avoid false-positive redaction.
    secret_key_patterns:
        Regex patterns matched against env var *names*. Only variables
        whose names match at least one pattern are included. Defaults to
        common secret-related key names.
    additional_secrets:
        Extra literal strings to redact (e.g. loaded from a vault).
    """

    # Default patterns for env var names that are likely secrets.
    DEFAULT_KEY_PATTERNS: list[re.Pattern[str]] = [
        re.compile(
            r"(SECRET|TOKEN|KEY|PASSWORD|PASSWD|PWD|CREDENTIAL)",
            re.IGNORECASE,
        ),
        re.compile(r"(API_KEY|ACCESS_KEY|AUTH|PRIVATE)", re.IGNORECASE),
        re.compile(
            r"(DATABASE_URL|DB_URL|REDIS_URL|MONGO_URI)",
            re.IGNORECASE,
        ),
        re.compile(r"(WEBHOOK|SIGNING|ENCRYPTION|HMAC)", re.IGNORECASE),
        re.compile(
            r"^(AWS_|OPENAI_|ANTHROPIC_|GROQ_|XAI_|HF_)",
            re.IGNORECASE,
        ),
        re.compile(r"^PROWLRBOT_(API_TOKEN|SECRET)", re.IGNORECASE),
    ]

    def __init__(
        self,
        min_value_length: int = 8,
        secret_key_patterns: Sequence[re.Pattern[str]] | None = None,
        additional_secrets: Sequence[str] | None = None,
    ) -> None:
        self._min_len = min_value_length
        self._key_patterns = (
            list(secret_key_patterns)
            if secret_key_patterns is not None
            else self.DEFAULT_KEY_PATTERNS
        )
        self._secrets: list[str] = []
        self._load_from_env()
        if additional_secrets:
            for s in additional_secrets:
                if len(s) >= self._min_len and s not in self._secrets:
                    self._secrets.append(s)
        # Sort longest-first so that longer secrets are redacted before
        # any shorter substrings.
        self._secrets.sort(key=len, reverse=True)

    def _load_from_env(self) -> None:
        """Snapshot env vars whose keys match secret patterns."""
        for key, value in os.environ.items():
            if not value or len(value) < self._min_len:
                continue
            for kp in self._key_patterns:
                if kp.search(key):
                    if value not in self._secrets:
                        self._secrets.append(value)
                    break

    def redact(self, text: str) -> str:
        """Replace occurrences of known secret values with ``[REDACTED]``."""
        for secret in self._secrets:
            if secret in text:
                text = text.replace(secret, "[REDACTED]")
        return text

    def add_secret(self, value: str) -> None:
        """Register an additional secret value at runtime."""
        if value and len(value) >= self._min_len and value not in self._secrets:
            self._secrets.append(value)
            # Re-sort longest-first.
            self._secrets.sort(key=len, reverse=True)

    @property
    def secret_count(self) -> int:
        """Number of secret values currently tracked."""
        return len(self._secrets)

    def reload(self) -> None:
        """Re-scan the environment for secret values."""
        self._secrets.clear()
        self._load_from_env()
        self._secrets.sort(key=len, reverse=True)
