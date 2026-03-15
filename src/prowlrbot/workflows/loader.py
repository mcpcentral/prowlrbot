# -*- coding: utf-8 -*-
"""Load workflow specs from YAML files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .models import WorkflowSpec, WorkflowStep, WorkflowTrigger

logger = logging.getLogger(__name__)


def _safe_yaml_load(text: str) -> dict[str, Any]:
    """Load YAML safely, falling back to JSON if PyYAML not available."""
    try:
        import yaml

        return yaml.safe_load(text) or {}
    except ImportError:
        import json

        return json.loads(text)


def load_workflow_from_file(path: Path) -> WorkflowSpec:
    """Load a workflow spec from a .prowlr.yaml or .prowlr.json file."""
    raw = path.read_text(encoding="utf-8")

    if path.suffix in (".yaml", ".yml"):
        data = _safe_yaml_load(raw)
    else:
        import json

        data = json.loads(raw)

    return parse_workflow_dict(data)


def parse_workflow_dict(data: dict[str, Any]) -> WorkflowSpec:
    """Parse a workflow dict into a WorkflowSpec model."""
    trigger_data = data.get("trigger", {})
    trigger = WorkflowTrigger(**trigger_data) if trigger_data else WorkflowTrigger()

    steps = []
    for step_data in data.get("steps", []):
        steps.append(WorkflowStep(**step_data))

    return WorkflowSpec(
        id=data.get("id", ""),
        name=data.get("name", "Unnamed Workflow"),
        version=data.get("version", "1.0.0"),
        description=data.get("description", ""),
        trigger=trigger,
        config=data.get("config", {}),
        steps=steps,
    )


def load_workflows_from_dir(directory: Path) -> list[WorkflowSpec]:
    """Load all workflow specs from a directory."""
    specs = []
    if not directory.exists():
        return specs

    for path in sorted(directory.iterdir()):
        if path.name.endswith((".prowlr.yaml", ".prowlr.yml", ".prowlr.json")):
            try:
                spec = load_workflow_from_file(path)
                specs.append(spec)
                logger.info(
                    "Loaded workflow: %s from %s",
                    spec.name,
                    path.name,
                )
            except Exception as exc:
                logger.warning(
                    "Failed to load workflow %s: %s",
                    path.name,
                    exc,
                )

    return specs
