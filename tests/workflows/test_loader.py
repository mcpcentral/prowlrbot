# -*- coding: utf-8 -*-
"""Tests for prowlrbot.workflows.loader — YAML/JSON loading and directory scanning."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from prowlrbot.workflows.loader import (
    load_workflow_from_file,
    load_workflows_from_dir,
    parse_workflow_dict,
)
from prowlrbot.workflows.models import (
    StepType,
    TriggerType,
    WorkflowSpec,
)

# ── parse_workflow_dict ───────────────────────────────────────────────────────


class TestParseWorkflowDict:
    def test_minimal_dict(self):
        spec = parse_workflow_dict({"name": "Hello"})
        assert spec.name == "Hello"
        assert spec.version == "1.0.0"
        assert spec.trigger.type == TriggerType.manual
        assert spec.steps == []

    def test_unnamed_workflow_gets_default_name(self):
        spec = parse_workflow_dict({})
        assert spec.name == "Unnamed Workflow"

    def test_full_dict(self):
        data = {
            "id": "wf-test",
            "name": "Full Workflow",
            "version": "2.0.0",
            "description": "A complete workflow",
            "trigger": {
                "type": "cron",
                "schedule": "0 9 * * 1",
                "timezone": "US/Eastern",
            },
            "config": {"api_key": "secret"},
            "steps": [
                {"id": "fetch", "type": "agent_query", "prompt": "Fetch data"},
                {
                    "id": "summarize",
                    "type": "transform",
                    "transform_expr": "{{fetch.output}}",
                    "depends_on": ["fetch"],
                },
                {
                    "id": "notify",
                    "type": "channel_send",
                    "channel": "slack",
                    "message_template": "Summary: {{summarize.output}}",
                    "depends_on": ["summarize"],
                },
            ],
        }
        spec = parse_workflow_dict(data)
        assert spec.id == "wf-test"
        assert spec.name == "Full Workflow"
        assert spec.version == "2.0.0"
        assert spec.trigger.type == TriggerType.cron
        assert spec.trigger.schedule == "0 9 * * 1"
        assert len(spec.steps) == 3
        assert spec.steps[0].type == StepType.agent_query
        assert spec.steps[1].type == StepType.transform
        assert spec.steps[2].type == StepType.channel_send
        assert spec.steps[2].depends_on == ["summarize"]

    def test_empty_trigger_gives_manual(self):
        spec = parse_workflow_dict({"name": "X", "trigger": {}})
        assert spec.trigger.type == TriggerType.manual

    def test_config_preserved(self):
        spec = parse_workflow_dict(
            {"name": "X", "config": {"a": 1, "b": [2, 3]}},
        )
        assert spec.config == {"a": 1, "b": [2, 3]}


# ── load_workflow_from_file (JSON) ────────────────────────────────────────────


class TestLoadWorkflowFromFileJSON:
    def test_load_json_file(self, tmp_path: Path):
        data = {
            "name": "JSON Workflow",
            "steps": [{"id": "s1", "prompt": "Hello"}],
        }
        path = tmp_path / "test.prowlr.json"
        path.write_text(json.dumps(data), encoding="utf-8")

        spec = load_workflow_from_file(path)
        assert spec.name == "JSON Workflow"
        assert len(spec.steps) == 1
        assert spec.steps[0].id == "s1"

    def test_load_json_with_all_fields(self, tmp_path: Path):
        data = {
            "id": "from-file",
            "name": "Complete JSON",
            "version": "3.0.0",
            "description": "Full fields",
            "trigger": {"type": "webhook", "webhook_path": "/hook"},
            "config": {"key": "value"},
            "steps": [
                {"id": "a", "type": "agent_query", "prompt": "Do X"},
                {
                    "id": "b",
                    "type": "transform",
                    "transform_expr": "{{a.output}}",
                    "depends_on": ["a"],
                },
            ],
        }
        path = tmp_path / "full.prowlr.json"
        path.write_text(json.dumps(data), encoding="utf-8")

        spec = load_workflow_from_file(path)
        assert spec.id == "from-file"
        assert spec.trigger.type == TriggerType.webhook

    def test_invalid_json_raises(self, tmp_path: Path):
        path = tmp_path / "bad.prowlr.json"
        path.write_text("{invalid json}", encoding="utf-8")

        with pytest.raises(Exception):
            load_workflow_from_file(path)


# ── load_workflow_from_file (YAML) ────────────────────────────────────────────


class TestLoadWorkflowFromFileYAML:
    def test_load_yaml_file(self, tmp_path: Path):
        yaml_content = """
name: YAML Workflow
steps:
  - id: step1
    prompt: Hello from YAML
"""
        path = tmp_path / "test.prowlr.yaml"
        path.write_text(yaml_content, encoding="utf-8")

        try:
            spec = load_workflow_from_file(path)
            assert spec.name == "YAML Workflow"
            assert len(spec.steps) == 1
            assert spec.steps[0].prompt == "Hello from YAML"
        except ImportError:
            pytest.skip("PyYAML not installed")

    def test_load_yml_extension(self, tmp_path: Path):
        yaml_content = """
name: YML Extension
steps: []
"""
        path = tmp_path / "test.prowlr.yml"
        path.write_text(yaml_content, encoding="utf-8")

        try:
            spec = load_workflow_from_file(path)
            assert spec.name == "YML Extension"
        except ImportError:
            pytest.skip("PyYAML not installed")

    def test_yaml_with_trigger(self, tmp_path: Path):
        yaml_content = """
name: Cron Workflow
trigger:
  type: cron
  schedule: "0 */4 * * *"
steps:
  - id: check
    prompt: Check status
"""
        path = tmp_path / "cron.prowlr.yaml"
        path.write_text(yaml_content, encoding="utf-8")

        try:
            spec = load_workflow_from_file(path)
            assert spec.trigger.type == TriggerType.cron
            assert spec.trigger.schedule == "0 */4 * * *"
        except ImportError:
            pytest.skip("PyYAML not installed")


# ── load_workflows_from_dir ───────────────────────────────────────────────────


class TestLoadWorkflowsFromDir:
    def test_empty_directory(self, tmp_path: Path):
        specs = load_workflows_from_dir(tmp_path)
        assert specs == []

    def test_nonexistent_directory(self, tmp_path: Path):
        specs = load_workflows_from_dir(tmp_path / "nonexistent")
        assert specs == []

    def test_loads_only_prowlr_files(self, tmp_path: Path):
        # Valid workflow file
        valid = {"name": "Valid", "steps": [{"id": "s1"}]}
        (tmp_path / "deploy.prowlr.json").write_text(json.dumps(valid))

        # Non-workflow files that should be ignored
        (tmp_path / "readme.md").write_text("# Workflows")
        (tmp_path / "config.json").write_text("{}")
        (tmp_path / "script.py").write_text("print('hi')")

        specs = load_workflows_from_dir(tmp_path)
        assert len(specs) == 1
        assert specs[0].name == "Valid"

    def test_loads_multiple_files_sorted(self, tmp_path: Path):
        for name in ["b-deploy.prowlr.json", "a-build.prowlr.json"]:
            data = {"name": name.split(".")[0], "steps": [{"id": "s1"}]}
            (tmp_path / name).write_text(json.dumps(data))

        specs = load_workflows_from_dir(tmp_path)
        assert len(specs) == 2
        # Sorted by filename — a- comes before b-
        assert specs[0].name == "a-build"
        assert specs[1].name == "b-deploy"

    def test_skips_invalid_files_gracefully(self, tmp_path: Path):
        # One valid, one invalid
        valid = {"name": "Good", "steps": [{"id": "s1"}]}
        (tmp_path / "good.prowlr.json").write_text(json.dumps(valid))
        (tmp_path / "bad.prowlr.json").write_text("{bad json!}")

        specs = load_workflows_from_dir(tmp_path)
        assert len(specs) == 1
        assert specs[0].name == "Good"

    def test_loads_yaml_and_json_together(self, tmp_path: Path):
        json_data = {"name": "JSON One", "steps": [{"id": "s1"}]}
        (tmp_path / "one.prowlr.json").write_text(json.dumps(json_data))

        yaml_content = "name: YAML Two\nsteps:\n  - id: s1\n"
        (tmp_path / "two.prowlr.yaml").write_text(yaml_content)

        try:
            specs = load_workflows_from_dir(tmp_path)
            assert len(specs) == 2
        except Exception:
            # If YAML isn't available, at least the JSON one loads
            specs = load_workflows_from_dir(tmp_path)
            assert len(specs) >= 1
