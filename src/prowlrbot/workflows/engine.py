# -*- coding: utf-8 -*-
"""Workflow execution engine — runs multi-step agent DAGs."""

from __future__ import annotations

import asyncio
import logging
import re
import time
from datetime import datetime, timezone
from typing import Any, Optional

from .models import (
    ErrorStrategy,
    StepResult,
    StepStatus,
    StepType,
    WorkflowRun,
    WorkflowRunStatus,
    WorkflowSpec,
    WorkflowStep,
)

logger = logging.getLogger(__name__)


def _resolve_template(template: str, context: dict[str, Any]) -> str:
    """Replace {{var.path}} placeholders with values from context."""

    def _replace(match: re.Match) -> str:
        path = match.group(1).strip()
        parts = path.split(".")
        val: Any = context
        for part in parts:
            if isinstance(val, dict):
                val = val.get(part, "")
            else:
                return match.group(0)
        return str(val) if val is not None else ""

    return re.sub(r"\{\{(.+?)\}\}", _replace, template)


def _build_step_graph(steps: list[WorkflowStep]) -> dict[str, list[str]]:
    """Build adjacency list of step dependencies."""
    graph: dict[str, list[str]] = {s.id: list(s.depends_on) for s in steps}
    return graph


def _topological_order(steps: list[WorkflowStep]) -> list[list[str]]:
    """Return steps grouped into execution tiers (parallel within each tier)."""
    graph = _build_step_graph(steps)
    step_ids = {s.id for s in steps}
    completed: set[str] = set()
    tiers: list[list[str]] = []

    while completed != step_ids:
        ready = [
            sid
            for sid in step_ids - completed
            if all(dep in completed for dep in graph.get(sid, []))
        ]
        if not ready:
            remaining = step_ids - completed
            logger.warning("Cycle detected in workflow steps: %s", remaining)
            tiers.append(list(remaining))
            break
        tiers.append(ready)
        completed.update(ready)

    return tiers


class WorkflowEngine:
    """Executes workflow specs as multi-step DAGs.

    Integrates with the existing agent runner for agent_query steps
    and the channel system for channel_send steps.
    """

    def __init__(
        self,
        runner: Any = None,
        channel_manager: Any = None,
    ) -> None:
        self._runner = runner
        self._channel_manager = channel_manager
        self._workflows: dict[str, WorkflowSpec] = {}
        self._runs: dict[str, WorkflowRun] = {}

    def register(self, spec: WorkflowSpec) -> None:
        """Register a workflow spec for execution."""
        self._workflows[spec.id] = spec
        logger.info("Registered workflow: %s (%s)", spec.name, spec.id)

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowSpec]:
        return self._workflows.get(workflow_id)

    def list_workflows(self) -> list[WorkflowSpec]:
        return list(self._workflows.values())

    def get_run(self, run_id: str) -> Optional[WorkflowRun]:
        return self._runs.get(run_id)

    async def execute(
        self,
        workflow_id: str,
        config_overrides: Optional[dict[str, Any]] = None,
    ) -> WorkflowRun:
        """Execute a registered workflow and return the run result."""
        spec = self._workflows.get(workflow_id)
        if spec is None:
            raise ValueError(f"Workflow not found: {workflow_id}")

        run = WorkflowRun(
            workflow_id=workflow_id,
            status=WorkflowRunStatus.running,
            config={**spec.config, **(config_overrides or {})},
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        self._runs[run.id] = run

        # Initialize step results
        for step in spec.steps:
            run.step_results[step.id] = StepResult(step_id=step.id)

        # Build execution tiers
        tiers = _topological_order(spec.steps)
        step_map = {s.id: s for s in spec.steps}

        # Context accumulates step outputs for template resolution
        context: dict[str, Any] = {
            "config": run.config,
            "user": run.config.get("user", {}),
        }

        try:
            for tier in tiers:
                tasks = []
                for step_id in tier:
                    step = step_map[step_id]
                    tasks.append(self._execute_step(step, run, context))
                await asyncio.gather(*tasks)

                # Check for abort conditions
                for step_id in tier:
                    result = run.step_results[step_id]
                    step = step_map[step_id]
                    if (
                        result.status == StepStatus.failed
                        and step.on_error == ErrorStrategy.abort
                    ):
                        run.status = WorkflowRunStatus.failed
                        run.error = f"Step '{step_id}' failed: {result.error}"
                        run.completed_at = datetime.now(
                            timezone.utc,
                        ).isoformat()
                        return run

            run.status = WorkflowRunStatus.completed
        except Exception as exc:
            run.status = WorkflowRunStatus.failed
            run.error = str(exc)
            logger.exception("Workflow %s failed", workflow_id)
        finally:
            run.completed_at = datetime.now(timezone.utc).isoformat()

        return run

    async def _execute_step(
        self,
        step: WorkflowStep,
        run: WorkflowRun,
        context: dict[str, Any],
    ) -> None:
        """Execute a single workflow step."""
        result = run.step_results[step.id]
        result.status = StepStatus.running
        result.started_at = datetime.now(timezone.utc).isoformat()
        t0 = time.monotonic()

        # Check condition
        if step.condition:
            resolved = _resolve_template(step.condition, context)
            if not resolved or resolved.lower() in ("false", "0", "none", ""):
                result.status = StepStatus.skipped
                result.completed_at = datetime.now(timezone.utc).isoformat()
                return

        try:
            if step.type == StepType.agent_query:
                output = await self._run_agent_step(step, context)
            elif step.type == StepType.channel_send:
                output = await self._run_channel_step(step, context)
            elif step.type == StepType.transform:
                output = _resolve_template(step.transform_expr, context)
            elif step.type == StepType.parallel_group:
                output = f"parallel group [{', '.join(step.parallel_steps)}]"
            else:
                output = ""

            result.status = StepStatus.completed
            result.output = output
            context[step.id] = {"output": output, "status": "completed"}

        except Exception as exc:
            result.status = StepStatus.failed
            result.error = str(exc)
            context[step.id] = {
                "output": "",
                "status": "failed",
                "error": str(exc),
            }
            logger.warning("Step %s failed: %s", step.id, exc)

            if step.on_error == ErrorStrategy.retry and step.retries > 0:
                for attempt in range(step.retries):
                    try:
                        output = await self._run_agent_step(step, context)
                        result.status = StepStatus.completed
                        result.output = output
                        result.error = ""
                        context[step.id] = {
                            "output": output,
                            "status": "completed",
                        }
                        break
                    except Exception:
                        if attempt == step.retries - 1:
                            logger.warning(
                                "Step %s failed after %d retries",
                                step.id,
                                step.retries,
                            )

        finally:
            result.duration_ms = int((time.monotonic() - t0) * 1000)
            result.completed_at = datetime.now(timezone.utc).isoformat()

    async def _run_agent_step(
        self,
        step: WorkflowStep,
        context: dict[str, Any],
    ) -> str:
        """Run an agent query step."""
        prompt = _resolve_template(step.prompt, context)

        # Resolve input variables
        for var_name, var_ref in step.inputs.items():
            resolved = _resolve_template(var_ref, context)
            prompt = prompt.replace(f"{{{{{var_name}}}}}", resolved)

        if self._runner is None:
            logger.warning(
                "No agent runner configured; returning prompt as output for step %s",
                step.id,
            )
            return f"[dry-run] {prompt}"

        try:
            result = await asyncio.wait_for(
                self._runner.process_query(prompt),
                timeout=step.timeout_seconds,
            )
            return str(result) if result else ""
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"Step '{step.id}' timed out after {step.timeout_seconds}s",
            )

    async def _run_channel_step(
        self,
        step: WorkflowStep,
        context: dict[str, Any],
    ) -> str:
        """Send a message to a channel."""
        channel = _resolve_template(step.channel, context)
        message = _resolve_template(step.message_template, context)

        if not message and step.prompt:
            message = _resolve_template(step.prompt, context)

        if self._channel_manager is None:
            logger.warning(
                "No channel manager configured; message for step %s: %s",
                step.id,
                message[:200],
            )
            return f"[dry-run] sent to {channel}: {message[:200]}"

        # Delegate to the channel manager
        await self._channel_manager.send_text(channel, message)
        return f"Sent to {channel}"
