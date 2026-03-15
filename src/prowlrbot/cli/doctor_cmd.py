# -*- coding: utf-8 -*-
"""prowlr doctor — environment health check via prowlr-doctor."""
from __future__ import annotations

import click


@click.command("doctor")
@click.option(
    "--profile",
    default="developer",
    show_default=True,
    type=click.Choice(
        ["developer", "security", "minimal", "agent-builder", "research"],
    ),
    help="Recommendation profile.",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output JSON instead of text.",
)
@click.option(
    "--write-plan",
    is_flag=True,
    help="Write fix plan to ~/.claude/doctor-plan.json.",
)
@click.option(
    "--diff",
    is_flag=True,
    help="Show settings.json diff from plan on disk.",
)
@click.option(
    "--apply",
    is_flag=True,
    help="Apply plan at ~/.claude/doctor-plan.json.",
)
@click.option(
    "--tui",
    is_flag=True,
    help="Launch interactive TUI (requires prowlr-doctor[tui]).",
)
@click.option(
    "--no-tui",
    is_flag=True,
    help="Rich report only (skip TUI even if installed).",
)
@click.pass_context
def doctor_cmd(
    ctx: click.Context,
    profile: str,
    as_json: bool,
    write_plan: bool,
    diff: bool,
    apply: bool,
    tui: bool,
    no_tui: bool,
) -> None:
    """Check your Claude Code environment for token waste, broken hooks, and misconfig."""
    try:
        from prowlr_doctor import paths, telemetry
        from prowlr_doctor.scanner import load_snapshot, run_audit
        from prowlr_doctor.recommender import recommend
        from prowlr_doctor.patch_planner import build_plan, apply_plan
        from prowlr_doctor.reporter import render
    except ImportError:
        raise click.ClickException(
            "prowlr-doctor not installed. Run: pip install prowlr-doctor",
        )

    if apply:
        import json

        plan_path = paths.doctor_plan_path()
        if not plan_path.exists():
            raise click.ClickException(
                f"No plan found at {plan_path}.\n"
                "Run: prowlr doctor --write-plan  to generate one first.",
            )
        from prowlr_doctor.models import FixAction, PatchPlan

        data = json.loads(plan_path.read_text())
        actions = [
            FixAction(
                action_type=a["action_type"],
                target=a["target"],
                settings_path=a.get("settings_path"),
                before=a["before"],
                after=a["after"],
                reversible=a.get("reversible", True),
                requires_restart=a.get("requires_restart", False),
            )
            for a in data.get("actions", [])
            if a.get("action_type") != "condense"
        ]
        plan = PatchPlan(
            version=data["version"],
            generated_at=data["generated_at"],
            profile=data["profile"],
            findings_count=data["findings_count"],
            actions=actions,
            estimated_savings=data["estimated_savings"],
            settings_diff=data["settings_diff"],
            plan_path=plan_path,
        )
        apply_plan(plan)
        click.echo(f"Applied {len(actions)} changes to settings.json.")
        click.echo("Backup saved. Restart Claude Code to pick up changes.")
        return

    if diff:
        import json, difflib
        from rich.console import Console
        from rich.syntax import Syntax

        plan_path = paths.doctor_plan_path()
        if not plan_path.exists():
            raise click.ClickException(
                f"No plan found at {plan_path}. Run --write-plan first.",
            )
        data = json.loads(plan_path.read_text())
        before = json.dumps(
            data["settings_diff"]["before"],
            indent=2,
        ).splitlines()
        after = json.dumps(
            data["settings_diff"]["after"],
            indent=2,
        ).splitlines()
        diff_text = "\n".join(
            difflib.unified_diff(
                before,
                after,
                fromfile="before",
                tofile="after",
                lineterm="",
            ),
        )
        Console().print(Syntax(diff_text, "diff", theme="monokai"))
        return

    env = load_snapshot()
    findings, budget = run_audit(env)
    rec = recommend(findings, profile)
    telemetry.maybe_send(env, findings, budget, profile)

    if tui:
        try:
            from prowlr_doctor.tui.app import EnvDoctorApp

            plan = build_plan(env, rec)
            EnvDoctorApp(
                findings=findings,
                budget=budget,
                rec=rec,
                plan=plan,
            ).run()
        except ImportError:
            raise click.ClickException(
                "Textual not installed. Install with: pip install prowlr-doctor[tui]",
            )
        return

    if as_json or write_plan:
        import json

        plan = build_plan(env, rec)
        output = {
            "version": "1",
            "generated_at": plan.generated_at,
            "profile": rec.profile,
            "environment": {
                "plugins_enabled": sum(1 for v in env.enabled_plugins.values() if v),
                "hooks_count": len(env.hooks),
                "mcp_servers": len(env.mcp_servers),
            },
            "token_budget": {
                "per_session_fixed": budget.per_session_fixed,
                "per_turn_recurring": budget.per_turn_recurring,
                "on_demand": budget.on_demand,
                "wasted": budget.wasted,
                "savings_if_cleaned": budget.savings_if_cleaned,
                "session_estimate_20turn": budget.session_estimate_20turn,
            },
            "findings": [
                {
                    "id": f.id,
                    "severity": f.severity.name.lower(),
                    "category": f.category,
                    "title": f.title,
                    "tokens_wasted": f.tokens_wasted,
                    "fix_action": {
                        "action_type": f.fix_action.action_type,
                        "target": f.fix_action.target,
                        "settings_path": f.fix_action.settings_path,
                        "before": f.fix_action.before,
                        "after": f.fix_action.after,
                        "reversible": f.fix_action.reversible,
                        "requires_restart": f.fix_action.requires_restart,
                    }
                    if f.fix_action
                    else None,
                }
                for f in findings
            ],
            "recommendations": {
                "disable": [f.id for f in rec.disable],
                "review": [f.id for f in rec.review],
                "keep": [f.id for f in rec.keep],
                "condense": [f.id for f in rec.condense],
            },
        }
        if as_json:
            click.echo(json.dumps(output, indent=2))
            cache = paths.doctor_cache_path()
            cache.write_text(json.dumps(output, indent=2))
        if write_plan:
            plan_path = paths.doctor_plan_path()
            plan_path.write_text(plan.to_json())
            click.echo(f"Plan written to {plan_path}")
            click.echo(
                f"  {len(plan.actions)} actions  ·  "
                f"saves {budget.savings_if_cleaned:,} tokens/session",
            )
            click.echo("Run: prowlr doctor --diff   to preview")
            click.echo("Run: prowlr doctor --apply  to apply")
        return

    if no_tui:
        render(findings, budget, rec)
        return

    # Default: try TUI, fall back to Rich report
    try:
        from prowlr_doctor.tui.app import EnvDoctorApp

        plan = build_plan(env, rec)
        EnvDoctorApp(
            findings=findings,
            budget=budget,
            rec=rec,
            plan=plan,
        ).run()
    except ImportError:
        click.echo(
            "[dim]Textual not installed — falling back to Rich report. "
            "Install with: pip install prowlr-doctor[tui][/dim]",
        )
        render(findings, budget, rec)
