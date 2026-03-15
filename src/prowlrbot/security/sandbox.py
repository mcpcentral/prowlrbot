# -*- coding: utf-8 -*-
"""Skill sandboxing system for ProwlrBot marketplace skills.

Provides static analysis and trust-level-based sandboxing configuration
for skills installed from the marketplace. This is the static analysis
layer — no Docker or container dependency required.
"""

import ast
import logging
import re
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TrustLevel(str, Enum):
    """Trust level for skills, determines sandbox restrictions."""

    BUILTIN = "builtin"
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    USER_CREATED = "user_created"


class SandboxConfig(BaseModel):
    """Sandbox configuration for a skill based on its trust level."""

    trust_level: TrustLevel
    allow_network: bool = False
    max_memory_mb: int = 256
    timeout_seconds: int = 30
    allowed_paths: list[str] = Field(default_factory=list)
    blocked_imports: list[str] = Field(default_factory=list)


# Default sandbox configurations per trust level.
DEFAULT_CONFIGS: dict[TrustLevel, SandboxConfig] = {
    TrustLevel.BUILTIN: SandboxConfig(
        trust_level=TrustLevel.BUILTIN,
        allow_network=True,
        max_memory_mb=1024,
        timeout_seconds=300,
        allowed_paths=["~/.prowlrbot/"],
        blocked_imports=[],
    ),
    TrustLevel.VERIFIED: SandboxConfig(
        trust_level=TrustLevel.VERIFIED,
        allow_network=True,
        max_memory_mb=512,
        timeout_seconds=120,
        allowed_paths=["~/.prowlrbot/active_skills/"],
        blocked_imports=[
            "ctypes",
            "multiprocessing",
        ],
    ),
    TrustLevel.UNVERIFIED: SandboxConfig(
        trust_level=TrustLevel.UNVERIFIED,
        allow_network=False,
        max_memory_mb=256,
        timeout_seconds=30,
        allowed_paths=["~/.prowlrbot/active_skills/"],
        blocked_imports=[
            "ctypes",
            "multiprocessing",
            "socket",
            "urllib",
            "requests",
            "httpx",
            "aiohttp",
            "subprocess",
            "shutil",
            "signal",
            "importlib",
            "pickle",
            "shelve",
            "marshal",
        ],
    ),
    TrustLevel.USER_CREATED: SandboxConfig(
        trust_level=TrustLevel.USER_CREATED,
        allow_network=True,
        max_memory_mb=512,
        timeout_seconds=120,
        allowed_paths=["~/.prowlrbot/"],
        blocked_imports=[
            "ctypes",
        ],
    ),
}


# ---------------------------------------------------------------------------
# Dangerous patterns for static analysis
# ---------------------------------------------------------------------------

# Module-level dangerous imports — each entry is (pattern, description).
_DANGEROUS_IMPORT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"\bos\.system\b"),
        "os.system allows arbitrary shell command execution",
    ),
    (
        re.compile(r"\bos\.popen\b"),
        "os.popen allows arbitrary shell command execution",
    ),
    (
        re.compile(r"\bos\.exec[lv]p?e?\b"),
        "os.exec* allows arbitrary process execution",
    ),
    (
        re.compile(r"\bos\.spawn[lv]p?e?\b"),
        "os.spawn* allows arbitrary process execution",
    ),
    (
        re.compile(r"\bos\.remove\b"),
        "os.remove can delete arbitrary files",
    ),
    (
        re.compile(r"\bos\.unlink\b"),
        "os.unlink can delete arbitrary files",
    ),
    (
        re.compile(r"\bos\.rmdir\b"),
        "os.rmdir can remove directories",
    ),
    (
        re.compile(r"\bos\.removedirs\b"),
        "os.removedirs can recursively remove directories",
    ),
    (
        re.compile(r"\bshutil\.rmtree\b"),
        "shutil.rmtree can recursively delete directory trees",
    ),
    (
        re.compile(r"\bshutil\.move\b"),
        "shutil.move can relocate files outside allowed paths",
    ),
    (
        re.compile(
            r"\bsubprocess\.(run|call|check_call|check_output|Popen)\b",
        ),
        "subprocess usage allows arbitrary command execution",
    ),
    (
        re.compile(r"\b__import__\s*\("),
        "__import__() can dynamically load blocked modules",
    ),
    (
        re.compile(r"\beval\s*\("),
        "eval() can execute arbitrary Python expressions",
    ),
    (
        re.compile(r"\bexec\s*\("),
        "exec() can execute arbitrary Python code",
    ),
    (
        re.compile(r"\bcompile\s*\("),
        "compile() combined with exec/eval enables code injection",
    ),
    (
        re.compile(r"\bgetattr\s*\("),
        "getattr() can access protected/private attributes dynamically",
    ),
    (
        re.compile(r"\bctypes\b"),
        "ctypes allows calling arbitrary C functions and memory access",
    ),
    (
        re.compile(r"\bpickle\.(loads?|dump)\b"),
        "pickle deserialization can execute arbitrary code",
    ),
    (
        re.compile(r"\bmarshal\.(loads?|dump)\b"),
        "marshal can deserialize arbitrary code objects",
    ),
    (
        re.compile(r"\bshelve\.open\b"),
        "shelve uses pickle internally and can execute arbitrary code",
    ),
    (
        re.compile(r"\bimportlib\.import_module\b"),
        "importlib.import_module can dynamically load blocked modules",
    ),
    (
        re.compile(r"\bsys\.modules\b"),
        "sys.modules manipulation can bypass import restrictions",
    ),
    (
        re.compile(r"\bopen\s*\([^)]*['\"]\/etc\/"),
        "Attempting to read system configuration files",
    ),
    (
        re.compile(r"\bopen\s*\([^)]*['\"]\/proc\/"),
        "Attempting to read /proc filesystem",
    ),
]

# Network-related patterns (checked when allow_network is False).
_NETWORK_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"\bsocket\.(socket|create_connection|getaddrinfo)\b"),
        "Direct socket usage for network access",
    ),
    (
        re.compile(r"\burllib\.request\.(urlopen|Request|urlretrieve)\b"),
        "urllib network access",
    ),
    (
        re.compile(
            r"\brequests\.(get|post|put|patch|delete|head|options|Session)\b",
        ),
        "requests library network access",
    ),
    (
        re.compile(
            r"\bhttpx\."
            r"(get|post|put|patch|delete|head|options|Client|AsyncClient)\b",
        ),
        "httpx library network access",
    ),
    (
        re.compile(r"\baiohttp\.(ClientSession|request)\b"),
        "aiohttp network access",
    ),
    (
        re.compile(r"\bhttp\.client\.(HTTPConnection|HTTPSConnection)\b"),
        "http.client network access",
    ),
    (
        re.compile(r"\bftplib\.FTP\b"),
        "FTP network access",
    ),
    (
        re.compile(r"\bsmtplib\.SMTP\b"),
        "SMTP network access",
    ),
    (
        re.compile(r"\btelnetlib\.Telnet\b"),
        "Telnet network access",
    ),
    (
        re.compile(r"\bxmlrpc\.client\b"),
        "XML-RPC network access",
    ),
    (
        re.compile(r"\basyncio\.(open_connection|start_server)\b"),
        "asyncio network access",
    ),
]


class StaticAnalyzer:
    """Performs static analysis on Python source code to detect dangerous
    patterns.

    Checks for:
    - Dangerous function calls (os.system, subprocess, eval, exec, etc.)
    - Network access (socket, urllib, requests, httpx, aiohttp)
    - Blocked imports per sandbox configuration
    - File system access outside allowed paths
    """

    def __init__(self, config: SandboxConfig | None = None) -> None:
        self._config = config

    def analyze(self, code: str) -> list[str]:
        """Analyze Python source code and return a list of warnings.

        Args:
            code: Python source code to analyze.

        Returns:
            List of human-readable warning strings. Empty if nothing
            suspicious is found.
        """
        warnings: list[str] = []

        # 1. Regex-based pattern matching for dangerous calls.
        warnings.extend(self._check_dangerous_patterns(code))

        # 2. Network access checks (when disallowed).
        if self._config and not self._config.allow_network:
            warnings.extend(self._check_network_patterns(code))

        # 3. AST-based import analysis for blocked imports.
        if self._config and self._config.blocked_imports:
            warnings.extend(
                self._check_blocked_imports(
                    code,
                    self._config.blocked_imports,
                ),
            )

        # 4. AST-based checks for additional dangerous constructs.
        warnings.extend(self._check_ast_patterns(code))

        return warnings

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _check_dangerous_patterns(code: str) -> list[str]:
        """Run regex-based checks for dangerous function calls."""
        warnings: list[str] = []
        for pattern, description in _DANGEROUS_IMPORT_PATTERNS:
            matches = pattern.findall(code)
            if matches:
                warnings.append(
                    f"DANGEROUS: {description} (found: {matches[0]})",
                )
        return warnings

    @staticmethod
    def _check_network_patterns(code: str) -> list[str]:
        """Run regex-based checks for network access."""
        warnings: list[str] = []
        for pattern, description in _NETWORK_PATTERNS:
            matches = pattern.findall(code)
            if matches:
                warnings.append(
                    f"NETWORK: {description} (found: {matches[0]})",
                )
        return warnings

    @staticmethod
    def _check_blocked_imports(code: str, blocked: list[str]) -> list[str]:
        """Use the AST to detect imports of blocked modules."""
        warnings: list[str] = []
        try:
            tree = ast.parse(code)
        except SyntaxError:
            warnings.append("SYNTAX: Failed to parse Python source code")
            return warnings

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top_module = alias.name.split(".")[0]
                    if top_module in blocked:
                        warnings.append(
                            f"BLOCKED_IMPORT: import of '{alias.name}' "
                            f"is not allowed "
                            f"(blocked module: {top_module})",
                        )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top_module = node.module.split(".")[0]
                    if top_module in blocked:
                        warnings.append(
                            f"BLOCKED_IMPORT: from-import of "
                            f"'{node.module}' is not allowed "
                            f"(blocked module: {top_module})",
                        )

        return warnings

    @staticmethod
    def _check_ast_patterns(code: str) -> list[str]:
        """Use the AST to detect additional dangerous constructs."""
        warnings: list[str] = []
        try:
            tree = ast.parse(code)
        except SyntaxError:
            # Already reported by _check_blocked_imports if called.
            return warnings

        for node in ast.walk(tree):
            # Detect attribute access on dunder attributes that can
            # be used to escape sandboxes.
            if isinstance(node, ast.Attribute):
                if node.attr in (
                    "__subclasses__",
                    "__bases__",
                    "__mro__",
                    "__globals__",
                    "__builtins__",
                    "__code__",
                    "__reduce__",
                    "__reduce_ex__",
                ):
                    warnings.append(
                        f"DANGEROUS: Access to '{node.attr}' can be "
                        f"used to escape sandbox restrictions",
                    )

            # Detect open() calls with absolute paths outside
            # working dir.
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id == "open":
                    if node.args:
                        first_arg = node.args[0]
                        if isinstance(first_arg, ast.Constant) and isinstance(
                            first_arg.value,
                            str,
                        ):
                            path_val = first_arg.value
                            if path_val.startswith(
                                "/",
                            ) and not path_val.startswith(
                                "/tmp",
                            ):
                                warnings.append(
                                    f"FILESYSTEM: open() with absolute "
                                    f"path '{path_val}' may access "
                                    f"files outside allowed directories",
                                )

        return warnings


class SkillSandbox:
    """Sandbox manager for skill validation and configuration.

    Validates skill scripts via static analysis and provides
    trust-level-appropriate sandbox configurations.

    Example::

        sandbox = SkillSandbox(
            SkillSandbox.get_config_for_trust(TrustLevel.UNVERIFIED)
        )
        passed, warnings = sandbox.validate_skill(
            Path("~/.prowlrbot/active_skills/my_skill")
        )
        if not passed:
            for w in warnings:
                print(f"  - {w}")
    """

    def __init__(self, config: SandboxConfig) -> None:
        self._config = config
        self._analyzer = StaticAnalyzer(config)

    @property
    def config(self) -> SandboxConfig:
        """Return the current sandbox configuration."""
        return self._config

    @staticmethod
    def get_config_for_trust(trust_level: TrustLevel) -> SandboxConfig:
        """Get the default SandboxConfig for a given trust level.

        Args:
            trust_level: The trust level to retrieve config for.

        Returns:
            A SandboxConfig with appropriate defaults.
        """
        return DEFAULT_CONFIGS[trust_level].model_copy()

    def validate_skill(self, skill_path: Path) -> tuple[bool, list[str]]:
        """Run static analysis on all Python files in a skill directory.

        Scans the ``scripts/`` subdirectory (and any nested Python
        files at the skill root) for dangerous patterns based on the
        current sandbox configuration.

        Args:
            skill_path: Path to the skill directory (must contain
                SKILL.md).

        Returns:
            A tuple of (passed, warnings).  ``passed`` is True when
            no warnings were generated; ``warnings`` is a list of
            human-readable strings describing each issue found.
        """
        skill_path = Path(skill_path).expanduser().resolve()
        all_warnings: list[str] = []

        if not skill_path.is_dir():
            return False, [f"Skill path is not a directory: {skill_path}"]

        skill_md = skill_path / "SKILL.md"
        if not skill_md.exists():
            return False, [f"Missing SKILL.md in {skill_path}"]

        # Collect all Python files to analyze.
        python_files = list(skill_path.rglob("*.py"))

        if not python_files:
            # No Python code to analyze — passes by default.
            logger.debug(
                "No Python files found in skill '%s'.",
                skill_path.name,
            )
            return True, []

        for py_file in python_files:
            try:
                code = py_file.read_text(encoding="utf-8")
            except Exception as exc:
                all_warnings.append(
                    f"Could not read " f"{py_file.relative_to(skill_path)}: {exc}",
                )
                continue

            rel_path = py_file.relative_to(skill_path)
            file_warnings = self._analyzer.analyze(code)

            for warning in file_warnings:
                all_warnings.append(f"[{rel_path}] {warning}")

        passed = len(all_warnings) == 0

        if passed:
            logger.debug(
                "Skill '%s' passed sandbox validation.",
                skill_path.name,
            )
        else:
            logger.warning(
                "Skill '%s' failed sandbox validation " "with %d warning(s).",
                skill_path.name,
                len(all_warnings),
            )

        return passed, all_warnings
