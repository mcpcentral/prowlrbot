# -*- coding: utf-8 -*-
"""Tests for prowlrbot.workflows.models — data models, enums, defaults, serialization."""

from __future__ import annotations

import json

import pytest

from prowlrbot.workflows.models import (
    ErrorStrategy,
    StepResult,
    StepStatus,
    StepType,
    TriggerType,
    WorkflowRun,
    WorkflowRunStatus,
    WorkflowSpec,
    WorkflowStep,
    WorkflowTrigger,
)

# ── StepType enum ────────────────────────────────────────────────────────────


class TestStepType:
    def test_all_values(self):
        expected = {
            "agent_query",
            "channel_send",
            "conditional",
            "parallel_group",
            "transform",
        }
        assert {v.value for v in StepType} == expected

    def test_str_representation(self):
        assert str(StepType.agent_query) == "agent_query"
        assert str(StepType.transform) == "transform"


# ── ErrorStrategy enum ───────────────────────────────────────────────────────


class TestErrorStrategy:
    def test_all_values(self):
        expected = {"skip", "retry", "abort", "fallback"}
        assert {v.value for v in ErrorStrategy} == expected


# ── TriggerType enum ─────────────────────────────────────────────────────────


class TestTriggerType:
    def test_all_values(self):
        expected = {"cron", "webhook", "event", "manual"}
        assert {v.value for v in TriggerType} == expected


# ── StepStatus enum ──────────────────────────────────────────────────────────


class TestStepStatus:
    def test_all_values(self):
        expected = {"pending", "running", "completed", "failed", "skipped"}
        assert {v.value for v in StepStatus} == expected


# ── WorkflowRunStatus enum ───────────────────────────────────────────────────


class TestWorkflowRunStatus:
    def test_all_values(self):
        expected = {"pending", "running", "completed", "failed", "cancelled"}
        assert {v.value for v in WorkflowRunStatus} == expected


# ── WorkflowStep model ───────────────────────────────────────────────────────


class TestWorkflowStep:
    def test_defaults(self):
        step = WorkflowStep(id="s1")
        assert step.type == StepType.agent_query
        assert step.prompt == ""
        assert step.tools == []
        assert step.inputs == {}
        assert step.depends_on == []
        assert step.condition == ""
        assert step.on_error == ErrorStrategy.skip
        assert step.timeout_seconds == 120
        assert step.retries == 0
        assert step.channel == ""
        assert step.message_template == ""
        assert step.parallel_steps == []
        assert step.transform_expr == ""

    def test_full_construction(self):
        step = WorkflowStep(
            id="step-1",
            type=StepType.transform,
            prompt="Summarize {{input.output}}",
            tools=["shell", "browser"],
            inputs={"data": "{{prev.output}}"},
            depends_on=["prev"],
            condition="{{config.enabled}}",
            on_error=ErrorStrategy.retry,
            timeout_seconds=60,
            retries=3,
            transform_expr="{{step1.output}} + {{step2.output}}",
        )
        assert step.id == "step-1"
        assert step.type == StepType.transform
        assert step.retries == 3
        assert step.tools == ["shell", "browser"]
        assert step.depends_on == ["prev"]

    def test_channel_send_fields(self):
        step = WorkflowStep(
            id="notify",
            type=StepType.channel_send,
            channel="slack",
            message_template="Done: {{result.output}}",
        )
        assert step.channel == "slack"
        assert step.message_template == "Done: {{result.output}}"

    def test_parallel_group_fields(self):
        step = WorkflowStep(
            id="par",
            type=StepType.parallel_group,
            parallel_steps=["a", "b", "c"],
        )
        assert step.parallel_steps == ["a", "b", "c"]

    def test_serialization_roundtrip(self):
        step = WorkflowStep(
            id="s1",
            type=StepType.agent_query,
            prompt="hello",
            depends_on=["s0"],
        )
        data = json.loads(step.model_dump_json())
        restored = WorkflowStep(**data)
        assert restored.id == step.id
        assert restored.type == step.type
        assert restored.prompt == step.prompt
        assert restored.depends_on == step.depends_on


# ── WorkflowTrigger model ────────────────────────────────────────────────────


class TestWorkflowTrigger:
    def test_defaults(self):
        trigger = WorkflowTrigger()
        assert trigger.type == TriggerType.manual
        assert trigger.schedule == ""
        assert trigger.timezone == "UTC"
        assert trigger.webhook_path == ""
        assert trigger.event_type == ""

    def test_cron_trigger(self):
        trigger = WorkflowTrigger(
            type=TriggerType.cron,
            schedule="0 8 * * *",
            timezone="US/Pacific",
        )
        assert trigger.type == TriggerType.cron
        assert trigger.schedule == "0 8 * * *"
        assert trigger.timezone == "US/Pacific"

    def test_webhook_trigger(self):
        trigger = WorkflowTrigger(
            type=TriggerType.webhook,
            webhook_path="/hooks/deploy",
        )
        assert trigger.webhook_path == "/hooks/deploy"

    def test_event_trigger(self):
        trigger = WorkflowTrigger(
            type=TriggerType.event,
            event_type="monitor.alert",
        )
        assert trigger.event_type == "monitor.alert"

    def test_serialization_roundtrip(self):
        trigger = WorkflowTrigger(
            type=TriggerType.cron,
            schedule="*/5 * * * *",
        )
        data = json.loads(trigger.model_dump_json())
        restored = WorkflowTrigger(**data)
        assert restored.type == trigger.type
        assert restored.schedule == trigger.schedule


# ── WorkflowSpec model ───────────────────────────────────────────────────────


class TestWorkflowSpec:
    def test_defaults(self):
        spec = WorkflowSpec(name="Test Workflow")
        assert spec.name == "Test Workflow"
        assert spec.version == "1.0.0"
        assert spec.description == ""
        assert spec.trigger.type == TriggerType.manual
        assert spec.config == {}
        assert spec.steps == []
        assert len(spec.id) == 12  # uuid hex[:12]
        assert spec.created_at  # non-empty ISO timestamp

    def test_auto_generated_id_is_unique(self):
        spec1 = WorkflowSpec(name="A")
        spec2 = WorkflowSpec(name="B")
        assert spec1.id != spec2.id

    def test_full_construction(self):
        spec = WorkflowSpec(
            id="wf-123",
            name="Deploy Pipeline",
            version="2.0.0",
            description="Deploys the app",
            trigger=WorkflowTrigger(
                type=TriggerType.webhook,
                webhook_path="/deploy",
            ),
            config={"env": "prod"},
            steps=[
                WorkflowStep(id="build", prompt="Build the project"),
                WorkflowStep(
                    id="test",
                    prompt="Run tests",
                    depends_on=["build"],
                ),
            ],
        )
        assert spec.id == "wf-123"
        assert len(spec.steps) == 2
        assert spec.steps[1].depends_on == ["build"]
        assert spec.config["env"] == "prod"

    def test_serialization_roundtrip(self):
        spec = WorkflowSpec(
            name="Roundtrip",
            steps=[
                WorkflowStep(id="a"),
                WorkflowStep(id="b", depends_on=["a"]),
            ],
        )
        data = json.loads(spec.model_dump_json())
        restored = WorkflowSpec(**data)
        assert restored.name == spec.name
        assert len(restored.steps) == 2
        assert restored.steps[1].depends_on == ["a"]


# ── StepResult model ─────────────────────────────────────────────────────────


class TestStepResult:
    def test_defaults(self):
        result = StepResult(step_id="s1")
        assert result.status == StepStatus.pending
        assert result.output == ""
        assert result.error == ""
        assert result.started_at is None
        assert result.completed_at is None
        assert result.duration_ms == 0

    def test_completed_result(self):
        result = StepResult(
            step_id="s1",
            status=StepStatus.completed,
            output="hello world",
            duration_ms=150,
            started_at="2026-01-01T00:00:00+00:00",
            completed_at="2026-01-01T00:00:01+00:00",
        )
        assert result.status == StepStatus.completed
        assert result.output == "hello world"
        assert result.duration_ms == 150

    def test_failed_result(self):
        result = StepResult(
            step_id="s1",
            status=StepStatus.failed,
            error="timeout",
        )
        assert result.status == StepStatus.failed
        assert result.error == "timeout"


# ── WorkflowRun model ────────────────────────────────────────────────────────


class TestWorkflowRun:
    def test_defaults(self):
        run = WorkflowRun(workflow_id="wf-1")
        assert run.workflow_id == "wf-1"
        assert run.status == WorkflowRunStatus.pending
        assert run.step_results == {}
        assert run.config == {}
        assert run.started_at is None
        assert run.completed_at is None
        assert run.error == ""
        assert len(run.id) == 12

    def test_auto_generated_id_is_unique(self):
        r1 = WorkflowRun(workflow_id="wf")
        r2 = WorkflowRun(workflow_id="wf")
        assert r1.id != r2.id

    def test_with_step_results(self):
        run = WorkflowRun(
            workflow_id="wf-1",
            status=WorkflowRunStatus.completed,
            step_results={
                "s1": StepResult(
                    step_id="s1",
                    status=StepStatus.completed,
                    output="ok",
                ),
                "s2": StepResult(step_id="s2", status=StepStatus.skipped),
            },
        )
        assert len(run.step_results) == 2
        assert run.step_results["s1"].output == "ok"
        assert run.step_results["s2"].status == StepStatus.skipped

    def test_serialization_roundtrip(self):
        run = WorkflowRun(
            workflow_id="wf-1",
            config={"key": "val"},
            step_results={
                "s1": StepResult(step_id="s1", status=StepStatus.completed),
            },
        )
        data = json.loads(run.model_dump_json())
        restored = WorkflowRun(**data)
        assert restored.workflow_id == run.workflow_id
        assert "s1" in restored.step_results
        assert restored.config == {"key": "val"}
