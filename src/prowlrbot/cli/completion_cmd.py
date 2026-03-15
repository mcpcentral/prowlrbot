# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from pathlib import Path

import click

_SHELL_SCRIPTS = {
    "bash": "_PROWLR_COMPLETE=bash_source prowlr",
    "zsh": "_PROWLR_COMPLETE=zsh_source prowlr",
    "fish": "_PROWLR_COMPLETE=fish_source prowlr",
}

_SHELL_RC_FILES = {
    "bash": Path.home() / ".bashrc",
    "zsh": Path.home() / ".zshrc",
}

_COMPLETION_MARKER = "# prowlr shell completion"

_BASH_SNIPPET = (
    f"\n{_COMPLETION_MARKER}\n" 'eval "$(_PROWLR_COMPLETE=bash_source prowlr)"\n'
)

_ZSH_SNIPPET = (
    f"\n{_COMPLETION_MARKER}\n" 'eval "$(_PROWLR_COMPLETE=zsh_source prowlr)"\n'
)

_FISH_SNIPPET = (
    f"{_COMPLETION_MARKER}\n" "_PROWLR_COMPLETE=fish_source prowlr | source\n"
)


def _detect_shell() -> str | None:
    """Detect the current shell from $SHELL environment variable."""
    shell_path = os.environ.get("SHELL", "")
    if not shell_path:
        return None
    shell_name = Path(shell_path).name
    if shell_name in ("bash", "zsh", "fish"):
        return shell_name
    return None


def _is_already_installed(rc_path: Path) -> bool:
    """Check if completion is already installed in the given rc file."""
    if not rc_path.exists():
        return False
    return _COMPLETION_MARKER in rc_path.read_text(encoding="utf-8")


@click.group("completion", invoke_without_command=True)
@click.pass_context
def completion_group(ctx: click.Context) -> None:
    """Shell completion scripts for prowlr."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@completion_group.command("bash")
def completion_bash() -> None:
    """Output bash completion script to stdout."""
    click.echo(f'eval "$({_SHELL_SCRIPTS["bash"]})"')


@completion_group.command("zsh")
def completion_zsh() -> None:
    """Output zsh completion script to stdout."""
    click.echo(f'eval "$({_SHELL_SCRIPTS["zsh"]})"')


@completion_group.command("fish")
def completion_fish() -> None:
    """Output fish completion script to stdout."""
    click.echo(f'{_SHELL_SCRIPTS["fish"]} | source')


@completion_group.command("install")
@click.option(
    "--shell",
    "shell_name",
    type=click.Choice(["bash", "zsh", "fish"]),
    default=None,
    help="Shell to install completion for (auto-detected if omitted).",
)
def completion_install(shell_name: str | None) -> None:
    """Auto-detect shell and install completion."""
    if shell_name is None:
        shell_name = _detect_shell()
        if shell_name is None:
            click.echo(
                "Error: Could not detect shell. "
                "Use --shell to specify bash, zsh, or fish.",
                err=True,
            )
            raise SystemExit(1)

    if shell_name == "fish":
        fish_dir = Path.home() / ".config" / "fish" / "completions"
        fish_file = fish_dir / "prowlr.fish"

        if fish_file.exists() and _COMPLETION_MARKER in fish_file.read_text(
            encoding="utf-8",
        ):
            click.echo("Fish completion for prowlr is already installed.")
            return

        fish_dir.mkdir(parents=True, exist_ok=True)
        with fish_file.open("a", encoding="utf-8") as f:
            f.write(_FISH_SNIPPET)
        click.echo(f"Installed fish completion to {fish_file}")
    else:
        rc_path = _SHELL_RC_FILES[shell_name]
        if _is_already_installed(rc_path):
            click.echo(
                f"Completion for prowlr is already installed in {rc_path}.",
            )
            return

        snippet = _BASH_SNIPPET if shell_name == "bash" else _ZSH_SNIPPET
        with rc_path.open("a", encoding="utf-8") as f:
            f.write(snippet)
        click.echo(f"Installed {shell_name} completion to {rc_path}")

    click.echo("Restart your shell or source the file to activate.")
