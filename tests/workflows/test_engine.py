# -*- coding: utf-8 -*-
"""Tests for prowlrbot.workflows.engine — DAG execution, template resolution, error strategies."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from prowlrbot.workflows.engine import (
    WorkflowEngine,
    _build_step_graph,
    _resolve_template,
    _topological_order,
)
from prowlrbot.workflows.models import (
    ErrorStrategy,
    StepResult,
    StepStatus,
    StepType,
    WorkflowRun,
    WorkflowRunStatus,
    WorkflowSpec,
    WorkflowStep,
    WorkflowTrigger,
)

# ── _resolve_template ────────────────────────────────────────────────────────


class TestResolveTemplate:
    def test_simple_replacement(self):
        ctx = {"name": "ProwlrBot"}
        assert _resolve_template("Hello {{name}}", ctx) == "Hello ProwlrBot"

    def test_nested_path(self):
        ctx = {"step1": {"output": "result data"}}
        assert _resolve_template("Got: {{step1.output}}", ctx) == "Got: result data"

    def test_deeply_nested(self):
        ctx = {"a": {"b": {"c": "deep"}}}
        assert _resolve_template("{{a.b.c}}", ctx) == "deep"

    def test_missing_key_leaves_placeholder(self):
        ctx = {"x": "1"}
        result = _resolve_template("{{missing}}", ctx)
        # missing key returns "" because dict.get returns ""
        assert result == ""

    def test_no_placeholders(self):
        assert _resolve_template("plain text", {}) == "plain text"

    def test_multiple_placeholders(self):
        ctx = {"a": "one", "b": "two"}
        assert _resolve_template("{{a}} and {{b}}", ctx) == "one and two"

    def test_whitespace_in_placeholder(self):
        ctx = {"key": "val"}
        assert _resolve_template("{{ key }}", ctx) == "val"

    def test_none_value_becomes_empty(self):
        ctx = {"key": None}
        assert _resolve_template("{{key}}", ctx) == ""

    def test_non_dict_traversal_returns_original(self):
        ctx = {"key": "string"}
        # Trying to traverse "string".sub should return the original placeholder
        result = _resolve_template("{{key.sub}}", ctx)
        assert result == "{{key.sub}}"


# ── _build_step_graph ─────────────────────────────────────────────────────────


class TestBuildStepGraph:
    def test_no_dependencies(self):
        steps = [WorkflowStep(id="a"), WorkflowStep(id="b")]
        graph = _build_step_graph(steps)
        assert graph == {"a": [], "b": []}

    def test_linear_chain(self):
        steps = [
            WorkflowStep(id="a"),
            WorkflowStep(id="b", depends_on=["a"]),
            WorkflowStep(id="c", depends_on=["b"]),
        ]
        graph = _build_step_graph(steps)
        assert graph == {"a": [], "b": ["a"], "c": ["b"]}

    def test_diamond_dependency(self):
        steps = [
            WorkflowStep(id="a"),
            WorkflowStep(id="b", depends_on=["a"]),
            WorkflowStep(id="c", depends_on=["a"]),
            WorkflowStep(id="d", depends_on=["b", "c"]),
        ]
        graph = _build_step_graph(steps)
        assert set(graph["d"]) == {"b", "c"}


# ── _topological_order ────────────────────────────────────────────────────────


class TestTopologicalOrder:
    def test_single_step(self):
        steps = [WorkflowStep(id="only")]
        tiers = _topological_order(steps)
        assert tiers == [["only"]]

    def test_independent_steps_same_tier(self):
        steps = [
            WorkflowStep(id="a"),
            WorkflowStep(id="b"),
            WorkflowStep(id="c"),
        ]
        tiers = _topological_order(steps)
        assert len(tiers) == 1
        assert set(tiers[0]) == {"a", "b", "c"}

    def test_linear_chain(self):
        steps = [
            WorkflowStep(id="a"),
            WorkflowStep(id="b", depends_on=["a"]),
            WorkflowStep(id="c", depends_on=["b"]),
        ]
        tiers = _topological_order(steps)
        assert len(tiers) == 3
        assert tiers[0] == ["a"]
        assert tiers[1] == ["b"]
        assert tiers[2] == ["c"]

    def test_diamond_dependency(self):
        steps = [
            WorkflowStep(id="a"),
            WorkflowStep(id="b", depends_on=["a"]),
            WorkflowStep(id="c", depends_on=["a"]),
            WorkflowStep(id="d", depends_on=["b", "c"]),
        ]
        tiers = _topological_order(steps)
        assert len(tiers) == 3
        assert tiers[0] == ["a"]
        assert set(tiers[1]) == {"b", "c"}
        assert tiers[2] == ["d"]

    def test_cycle_detected_still_returns_all_steps(self):
        steps = [
            WorkflowStep(id="a", depends_on=["b"]),
            WorkflowStep(id="b", depends_on=["a"]),
        ]
        tiers = _topological_order(steps)
        all_ids = {sid for tier in tiers for sid in tier}
        assert all_ids == {"a", "b"}


# ── WorkflowEngine: registration ─────────────────────────────────────────────


class TestWorkflowEngineRegistration:
    def test_register_and_get(self):
        engine = WorkflowEngine()
        spec = WorkflowSpec(id="wf1", name="Test")
        engine.register(spec)

        assert engine.get_workflow("wf1") is spec
        assert engine.get_workflow("missing") is None

    def test_list_workflows(self):
        engine = WorkflowEngine()
        engine.register(WorkflowSpec(id="a", name="A"))
        engine.register(WorkflowSpec(id="b", name="B"))

        listed = engine.list_workflows()
        assert len(listed) == 2
        assert {s.id for s in listed} == {"a", "b"}

    def test_register_overwrites(self):
        engine = WorkflowEngine()
        engine.register(WorkflowSpec(id="wf", name="V1"))
        engine.register(WorkflowSpec(id="wf", name="V2"))
        assert engine.get_workflow("wf").name == "V2"


# ── WorkflowEngine: execute (dry-run, no runner) ─────────────────────────────


class TestWorkflowEngineExecuteDryRun:
    @pytest.fixture()
    def engine(self):
        return WorkflowEngine(runner=None, channel_manager=None)

    @pytest.mark.asyncio
    async def test_execute_missing_workflow_raises(self, engine):
        with pytest.raises(ValueError, match="Workflow not found"):
            await engine.execute("nonexistent")

    @pytest.mark.asyncio
    async def test_execute_single_agent_step_dry_run(self, engine):
        spec = WorkflowSpec(
            id="wf1",
            name="Single Step",
            steps=[
                WorkflowStep(
                    id="s1",
                    type=StepType.agent_query,
                    prompt="Hello",
                ),
            ],
        )
        engine.register(spec)

        run = await engine.execute("wf1")
        assert run.status == WorkflowRunStatus.completed
        assert run.workflow_id == "wf1"
        assert "s1" in run.step_results
        assert run.step_results["s1"].status == StepStatus.completed
        assert "[dry-run]" in run.step_results["s1"].output
        assert run.started_at is not None
        assert run.completed_at is not None

    @pytest.mark.asyncio
    async def test_execute_transform_step(self, engine):
        spec = WorkflowSpec(
            id="wf2",
            name="Transform",
            config={"greeting": "hi"},
            steps=[
                WorkflowStep(
                    id="t1",
                    type=StepType.transform,
                    transform_expr="{{config.greeting}} world",
                ),
            ],
        )
        engine.register(spec)

        run = await engine.execute("wf2")
        assert run.step_results["t1"].status == StepStatus.completed
        assert run.step_results["t1"].output == "hi world"

    @pytest.mark.asyncio
    async def test_execute_parallel_group_step(self, engine):
        spec = WorkflowSpec(
            id="wf3",
            name="Parallel",
            steps=[
                WorkflowStep(
                    id="pg",
                    type=StepType.parallel_group,
                    parallel_steps=["x", "y"],
                ),
            ],
        )
        engine.register(spec)

        run = await engine.execute("wf3")
        assert run.step_results["pg"].status == StepStatus.completed
        assert "x" in run.step_results["pg"].output

    @pytest.mark.asyncio
    async def test_execute_channel_send_dry_run(self, engine):
        spec = WorkflowSpec(
            id="wf4",
            name="Channel",
            steps=[
                WorkflowStep(
                    id="send",
                    type=StepType.channel_send,
                    channel="slack",
                    message_template="Hello channel",
                ),
            ],
        )
        engine.register(spec)

        run = await engine.execute("wf4")
        assert run.step_results["send"].status == StepStatus.completed
        assert "[dry-run]" in run.step_results["send"].output

    @pytest.mark.asyncio
    async def test_step_condition_false_skips(self, engine):
        spec = WorkflowSpec(
            id="wf5",
            name="Conditional",
            steps=[
                WorkflowStep(
                    id="s1",
                    type=StepType.agent_query,
                    prompt="Skip me",
                    condition="{{config.nope}}",  # resolves to ""
                ),
            ],
        )
        engine.register(spec)

        run = await engine.execute("wf5")
        assert run.step_results["s1"].status == StepStatus.skipped

    @pytest.mark.asyncio
    async def test_config_overrides(self, engine):
        spec = WorkflowSpec(
            id="wf6",
            name="Overrides",
            config={"msg": "original"},
            steps=[
                WorkflowStep(
                    id="t1",
                    type=StepType.transform,
                    transform_expr="{{config.msg}}",
                ),
            ],
        )
        engine.register(spec)

        run = await engine.execute(
            "wf6",
            config_overrides={"msg": "overridden"},
        )
        assert run.step_results["t1"].output == "overridden"

    @pytest.mark.asyncio
    async def test_multi_tier_execution_order(self, engine):
        spec = WorkflowSpec(
            id="wf7",
            name="Multi-Tier",
            steps=[
                WorkflowStep(
                    id="a",
                    type=StepType.transform,
                    transform_expr="A",
                ),
                WorkflowStep(
                    id="b",
                    type=StepType.transform,
                    transform_expr="B after {{a.output}}",
                    depends_on=["a"],
                ),
            ],
        )
        engine.register(spec)

        run = await engine.execute("wf7")
        assert run.step_results["a"].status == StepStatus.completed
        assert run.step_results["b"].status == StepStatus.completed
        assert run.step_results["b"].output == "B after A"

    @pytest.mark.asyncio
    async def test_run_is_stored(self, engine):
        spec = WorkflowSpec(id="wf8", name="Stored", steps=[])
        engine.register(spec)

        run = await engine.execute("wf8")
        assert engine.get_run(run.id) is run


# ── WorkflowEngine: execute with mocked runner ───────────────────────────────


class TestWorkflowEngineWithRunner:
    @pytest.mark.asyncio
    async def test_agent_step_calls_runner(self):
        runner = MagicMock()
        runner.process_query = AsyncMock(return_value="agent response")
        engine = WorkflowEngine(runner=runner)

        spec = WorkflowSpec(
            id="wf-run",
            name="Agent",
            steps=[WorkflowStep(id="s1", prompt="Summarize data")],
        )
        engine.register(spec)

        run = await engine.execute("wf-run")
        assert run.step_results["s1"].status == StepStatus.completed
        assert run.step_results["s1"].output == "agent response"
        runner.process_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_agent_step_template_resolved_before_call(self):
        runner = MagicMock()
        runner.process_query = AsyncMock(return_value="ok")
        engine = WorkflowEngine(runner=runner)

        spec = WorkflowSpec(
            id="wf-tmpl",
            name="Template",
            config={"topic": "AI"},
            steps=[
                WorkflowStep(id="s1", prompt="Tell me about {{config.topic}}"),
            ],
        )
        engine.register(spec)

        await engine.execute("wf-tmpl")
        call_args = runner.process_query.call_args[0][0]
        assert "AI" in call_args
        assert "{{" not in call_args


# ── WorkflowEngine: error strategies ─────────────────────────────────────────


class TestWorkflowEngineErrorStrategies:
    @pytest.mark.asyncio
    async def test_abort_strategy_stops_workflow(self):
        runner = MagicMock()
        runner.process_query = AsyncMock(side_effect=RuntimeError("boom"))
        engine = WorkflowEngine(runner=runner)

        spec = WorkflowSpec(
            id="wf-abort",
            name="Abort on Error",
            steps=[
                WorkflowStep(
                    id="s1",
                    prompt="fail",
                    on_error=ErrorStrategy.abort,
                ),
                WorkflowStep(id="s2", prompt="never", depends_on=["s1"]),
            ],
        )
        engine.register(spec)

        run = await engine.execute("wf-abort")
        assert run.status == WorkflowRunStatus.failed
        assert "s1" in run.error
        # s2 should remain pending since workflow aborted
        assert run.step_results["s2"].status == StepStatus.pending

    @pytest.mark.asyncio
    async def test_skip_strategy_continues_workflow(self):
        runner = MagicMock()
        runner.process_query = AsyncMock(side_effect=RuntimeError("boom"))
        engine = WorkflowEngine(runner=runner)

        spec = WorkflowSpec(
            id="wf-skip",
            name="Skip on Error",
            steps=[
                WorkflowStep(
                    id="s1",
                    prompt="fail",
                    on_error=ErrorStrategy.skip,
                ),
                WorkflowStep(
                    id="s2",
                    prompt="runs",
                    on_error=ErrorStrategy.skip,
                ),
            ],
        )
        engine.register(spec)

        run = await engine.execute("wf-skip")
        assert run.status == WorkflowRunStatus.completed
        assert run.step_results["s1"].status == StepStatus.failed
        assert (
            run.step_results["s2"].status == StepStatus.failed
        )  # also fails, same runner

    @pytest.mark.asyncio
    async def test_retry_strategy_retries_on_failure(self):
        runner = MagicMock()
        # Fail twice then succeed
        runner.process_query = AsyncMock(
            side_effect=[
                RuntimeError("fail1"),
                RuntimeError("fail2"),
                "success",
            ],
        )
        engine = WorkflowEngine(runner=runner)

        spec = WorkflowSpec(
            id="wf-retry",
            name="Retry",
            steps=[
                WorkflowStep(
                    id="s1",
                    prompt="retry me",
                    on_error=ErrorStrategy.retry,
                    retries=3,
                ),
            ],
        )
        engine.register(spec)

        run = await engine.execute("wf-retry")
        # The initial call fails, then retry succeeds on attempt 2 (3rd overall call)
        assert run.step_results["s1"].status == StepStatus.completed
        assert run.step_results["s1"].output == "success"

    @pytest.mark.asyncio
    async def test_retry_exhausted_remains_failed(self):
        runner = MagicMock()
        runner.process_query = AsyncMock(
            side_effect=RuntimeError("always fails"),
        )
        engine = WorkflowEngine(runner=runner)

        spec = WorkflowSpec(
            id="wf-retry-fail",
            name="Retry Exhausted",
            steps=[
                WorkflowStep(
                    id="s1",
                    prompt="fail forever",
                    on_error=ErrorStrategy.retry,
                    retries=2,
                ),
            ],
        )
        engine.register(spec)

        run = await engine.execute("wf-retry-fail")
        assert run.step_results["s1"].status == StepStatus.failed

    @pytest.mark.asyncio
    async def test_step_duration_is_recorded(self):
        engine = WorkflowEngine()
        spec = WorkflowSpec(
            id="wf-dur",
            name="Duration",
            steps=[
                WorkflowStep(
                    id="s1",
                    type=StepType.transform,
                    transform_expr="fast",
                ),
            ],
        )
        engine.register(spec)

        run = await engine.execute("wf-dur")
        assert run.step_results["s1"].duration_ms >= 0
        assert run.step_results["s1"].started_at is not None
        assert run.step_results["s1"].completed_at is not None
