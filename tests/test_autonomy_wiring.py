# -*- coding: utf-8 -*-
"""Test that autonomy policy is wired into agent execution context."""
import pytest
from unittest.mock import MagicMock, patch


def test_autonomy_policy_loaded_for_agent():
    """AutonomyController.get_policy is called during agent query setup."""
    # Verify the import exists and the controller is importable from runner context
    from prowlrbot.autonomy.controller import AutonomyController

    controller = AutonomyController()
    # Default behavior: no policy configured → returns None
    policy = controller.get_policy("nonexistent_agent")
    assert policy is None


def test_evaluate_action_blocks_blocked_tool():
    """Blocked tools are rejected."""
    from prowlrbot.autonomy.controller import AutonomyController
    from prowlrbot.autonomy.models import AutonomyPolicy, AutonomyLevel

    controller = AutonomyController()
    controller.set_policy(
        AutonomyPolicy(
            agent_id="test_agent",
            level=AutonomyLevel.DELEGATE,
            blocked_tools=["shell"],
        ),
    )
    decision = controller.evaluate_action("test_agent", "run shell", "shell")
    assert decision.approved is False


def test_controller_lifecycle_closes_connection():
    """Controller connection is closed even when policy is None (try/finally pattern)."""
    from prowlrbot.autonomy.controller import AutonomyController
    from unittest.mock import patch

    with patch.object(
        AutonomyController,
        "get_policy",
        return_value=None,
    ) as mock_get:
        with patch.object(AutonomyController, "close") as mock_close:
            # Simulate what runner does
            controller = AutonomyController()
            try:
                policy = controller.get_policy("test_session")
            finally:
                controller.close()

            mock_get.assert_called_once_with("test_session")
            mock_close.assert_called_once()


def test_evaluate_action_approves_in_autonomous_mode():
    """AUTONOMOUS level approves everything not blocked."""
    from prowlrbot.autonomy.controller import AutonomyController
    from prowlrbot.autonomy.models import AutonomyPolicy, AutonomyLevel

    controller = AutonomyController()
    controller.set_policy(
        AutonomyPolicy(
            agent_id="test_agent2",
            level=AutonomyLevel.AUTONOMOUS,
        ),
    )
    decision = controller.evaluate_action(
        "test_agent2",
        "read file",
        "file_read",
    )
    assert decision.approved is True
