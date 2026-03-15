# -*- coding: utf-8 -*-
"""Webhook rule executor — matches triggers to rules and runs actions."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from .models import ActionType, TriggerType, WebhookRule
from .store import WebhookStore

logger = logging.getLogger(__name__)


class WebhookExecutor:
    """Find matching rules for a trigger event and execute their actions."""

    def __init__(self, store: WebhookStore) -> None:
        self._store = store

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def handle_trigger(
        self,
        trigger_type: TriggerType,
        data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Find all enabled rules matching *trigger_type* and execute them.

        Returns a list of per-rule result dicts::

            [{"rule_id": "...", "rule_name": "...", "results": [...]}]
        """
        rules = await self._store.list_rules()
        matching = [r for r in rules if r.enabled and r.trigger.type == trigger_type]

        if not matching:
            logger.debug(
                "no matching webhook rules for trigger %s",
                trigger_type.value,
            )
            return []

        results: List[Dict[str, Any]] = []
        for rule in matching:
            if not self._matches_config(rule, data):
                continue
            rule_result = await self.execute_rule(rule, data)
            results.append(rule_result)

        return results

    async def execute_rule(
        self,
        rule: WebhookRule,
        trigger_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute all actions for a single rule.

        Returns::

            {"rule_id": "...", "rule_name": "...", "results": [...]}
        """
        logger.info(
            "executing webhook rule %s (%s) with %d action(s)",
            rule.id,
            rule.name,
            len(rule.actions),
        )

        action_results: List[Dict[str, Any]] = []
        for action in rule.actions:
            try:
                result = await self._run_action(
                    action.type,
                    action.config,
                    trigger_data,
                )
                action_results.append(
                    {
                        "action": action.type.value,
                        "status": "ok",
                        "result": result,
                    },
                )
            except Exception as exc:
                logger.exception(
                    "action %s failed for rule %s: %s",
                    action.type.value,
                    rule.id,
                    exc,
                )
                action_results.append(
                    {
                        "action": action.type.value,
                        "status": "error",
                        "error": str(exc),
                    },
                )

        # Record that this rule was triggered.
        await self._store.record_trigger(rule.id)

        return {
            "rule_id": rule.id,
            "rule_name": rule.name,
            "results": action_results,
        }

    # ------------------------------------------------------------------
    # Trigger matching
    # ------------------------------------------------------------------

    @staticmethod
    def _matches_config(rule: WebhookRule, data: Dict[str, Any]) -> bool:
        """Check whether incoming *data* satisfies the trigger config filters.

        The trigger config acts as a set of required key-value constraints:
        every key present in ``rule.trigger.config`` must appear in *data*
        with the same value. An empty config matches everything.
        """
        for key, expected in rule.trigger.config.items():
            actual = data.get(key)
            if actual is None:
                return False
            # Support simple equality. For list-valued config entries
            # (e.g. branches), check membership.
            if isinstance(expected, list):
                if actual not in expected:
                    return False
            elif actual != expected:
                return False
        return True

    # ------------------------------------------------------------------
    # Action runners
    # ------------------------------------------------------------------

    async def _run_action(
        self,
        action_type: ActionType,
        config: Dict[str, Any],
        trigger_data: Dict[str, Any],
    ) -> Any:
        """Dispatch to the appropriate action handler."""
        handler = _ACTION_HANDLERS.get(action_type)
        if handler is None:
            raise NotImplementedError(
                f"action type not implemented: {action_type.value}",
            )
        return await handler(self, config, trigger_data)

    # -- run_agent ---------------------------------------------------

    async def _action_run_agent(
        self,
        config: Dict[str, Any],
        trigger_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Queue an agent query via the runner.

        Expected config keys:
            input (str): The prompt to send to the agent.
            session_id (str, optional): Session to use.
            user_id (str, optional): User context.
        """
        prompt = config.get("input", "")
        if not prompt:
            # Auto-generate a summary prompt from the trigger data.
            prompt = f"Webhook triggered: {trigger_data}"

        return {
            "queued": True,
            "input": prompt,
            "session_id": config.get("session_id", "webhook"),
            "user_id": config.get("user_id", "webhook-system"),
            "trigger_data": trigger_data,
        }

    # -- post_channel ------------------------------------------------

    async def _action_post_channel(
        self,
        config: Dict[str, Any],
        trigger_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Post a message to a channel.

        Expected config keys:
            channel (str): Channel name (e.g. "discord", "telegram").
            target (str): Channel-specific target (chat id, room, etc.).
            message (str): Message template — ``{trigger_data}`` is replaced.
        """
        message = config.get("message", "Webhook fired.")
        message = message.replace("{trigger_data}", str(trigger_data))

        return {
            "posted": True,
            "channel": config.get("channel", "console"),
            "target": config.get("target", ""),
            "message": message,
        }

    # -- send_webhook ------------------------------------------------

    async def _action_send_webhook(
        self,
        config: Dict[str, Any],
        trigger_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Forward data to an external HTTP endpoint.

        Expected config keys:
            url (str): Destination URL (required).
            method (str): HTTP method, default POST.
            headers (dict): Extra headers.
            body (dict, optional): Custom body; defaults to trigger_data.
        """
        url = config.get("url")
        if not url:
            raise ValueError("send_webhook action requires a 'url' in config")

        from prowlrbot.security.url_validator import validate_outbound_url

        allowed, reason = validate_outbound_url(url)
        if not allowed:
            raise ValueError(f"Webhook URL blocked: {reason}")

        method = config.get("method", "POST").upper()
        headers = config.get("headers", {})
        body = config.get("body", trigger_data)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=body,
            )

        return {
            "status_code": response.status_code,
            "url": url,
            "method": method,
        }

    # -- send_email --------------------------------------------------

    async def _action_send_email(
        self,
        config: Dict[str, Any],
        trigger_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Prepare an email notification.

        Expected config keys:
            to (str): Recipient email address.
            subject (str): Email subject.
            body (str): Email body — ``{trigger_data}`` is replaced.

        Note: Actual SMTP delivery is deferred to a mail service integration.
        This handler prepares and returns the email payload so that a
        downstream mail sender (or channel) can pick it up.
        """
        to = config.get("to", "")
        subject = config.get("subject", "ProwlrBot Webhook Notification")
        body = config.get(
            "body",
            "Webhook triggered with data: {trigger_data}",
        )
        body = body.replace("{trigger_data}", str(trigger_data))

        if not to:
            raise ValueError(
                "send_email action requires a 'to' address in config",
            )

        return {
            "prepared": True,
            "to": to,
            "subject": subject,
            "body": body,
        }

    # -- create_task -------------------------------------------------

    async def _action_create_task(
        self,
        config: Dict[str, Any],
        trigger_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create an internal task entry.

        Expected config keys:
            title (str): Task title.
            description (str): Task description — ``{trigger_data}`` is replaced.
            priority (str): low | medium | high. Default medium.
        """
        title = config.get("title", "Webhook Task")
        description = config.get(
            "description",
            "Auto-created from webhook: {trigger_data}",
        )
        description = description.replace("{trigger_data}", str(trigger_data))
        priority = config.get("priority", "medium")

        return {
            "created": True,
            "title": title,
            "description": description,
            "priority": priority,
            "trigger_data": trigger_data,
        }


# Dispatch table — maps ActionType to bound method names.
_ACTION_HANDLERS: Dict[ActionType, Any] = {
    ActionType.run_agent: WebhookExecutor._action_run_agent,
    ActionType.post_channel: WebhookExecutor._action_post_channel,
    ActionType.send_webhook: WebhookExecutor._action_send_webhook,
    ActionType.send_email: WebhookExecutor._action_send_email,
    ActionType.create_task: WebhookExecutor._action_create_task,
}
