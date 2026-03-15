# -*- coding: utf-8 -*-
"""ROAR Protocol SDK — Server for receiving and handling ROAR messages."""

from __future__ import annotations

import logging
from typing import Any, Callable, Coroutine, Dict, List, Optional, Union

from ..roar import (
    AgentCard,
    AgentDirectory,
    AgentIdentity,
    DiscoveryEntry,
    MessageIntent,
    ROARMessage,
    StreamEvent,
)
from .streaming import EventBus, StreamFilter

logger = logging.getLogger(__name__)

# Type alias for handler functions (sync or async).
HandlerFunc = Callable[
    [ROARMessage],
    Union[ROARMessage, Coroutine[Any, Any, ROARMessage]],
]


class ROARServer:
    """Server that dispatches incoming ROAR messages to registered handlers.

    Usage::

        identity = AgentIdentity(display_name="code-reviewer")
        server = ROARServer(identity)

        @server.on(MessageIntent.DELEGATE)
        async def handle_delegate(msg: ROARMessage) -> ROARMessage:
            result = await review_code(msg.payload)
            return ROARMessage(
                **{"from": server.identity, "to": msg.from_identity},
                intent=MessageIntent.RESPOND,
                payload={"review": result},
            )

        # In a full implementation you would call server.serve() to start
        # listening on host:port. For now, dispatch manually:
        response = await server.handle_message(incoming_msg)
    """

    def __init__(
        self,
        identity: AgentIdentity,
        host: str = "127.0.0.1",
        port: int = 8089,
        *,
        description: str = "",
        skills: Optional[List[str]] = None,
        channels: Optional[List[str]] = None,
        signing_secret: str = "",
    ) -> None:
        self._identity = identity
        self._host = host
        self._port = port
        self._description = description
        self._skills = skills or []
        self._channels = channels or []
        self._signing_secret = signing_secret
        self._handlers: Dict[MessageIntent, HandlerFunc] = {}
        self._event_bus = EventBus()

    # -- public API -----------------------------------------------------------

    @property
    def identity(self) -> AgentIdentity:
        """Return the server's agent identity."""
        return self._identity

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    @property
    def event_bus(self) -> EventBus:
        """Return the server's event bus for pub/sub streaming."""
        return self._event_bus

    async def emit(self, event: StreamEvent) -> int:
        """Publish a stream event to all subscribers.

        Args:
            event: The event to broadcast.

        Returns:
            Number of subscribers that received the event.
        """
        return await self._event_bus.publish(event)

    def on(
        self,
        intent: MessageIntent,
    ) -> Callable[[HandlerFunc], HandlerFunc]:
        """Register a handler for a specific message intent.

        Can be used as a decorator::

            @server.on(MessageIntent.EXECUTE)
            async def handle_execute(msg):
                ...

        Or called directly::

            server.on(MessageIntent.EXECUTE)(my_handler)

        Args:
            intent: The ``MessageIntent`` this handler responds to.

        Returns:
            A decorator that registers the handler function.
        """

        def decorator(handler: HandlerFunc) -> HandlerFunc:
            self._handlers[intent] = handler
            return handler

        return decorator

    async def handle_message(self, msg: ROARMessage) -> ROARMessage:
        """Dispatch an incoming message to the appropriate handler.

        If no handler is registered for the message's intent, a default
        error response is returned.

        Args:
            msg: The incoming ``ROARMessage``.

        Returns:
            A ``ROARMessage`` response from the handler (or an error response).
        """
        handler = self._handlers.get(msg.intent)
        if handler is None:
            logger.warning(
                "No handler for intent %s from %s",
                msg.intent,
                msg.from_identity.did,
            )
            return ROARMessage(
                **{"from": self._identity, "to": msg.from_identity},
                intent=MessageIntent.RESPOND,
                payload={
                    "error": "unhandled_intent",
                    "message": f"No handler registered for intent '{msg.intent}'",
                },
                context={"in_reply_to": msg.id},
            )

        import inspect

        if inspect.iscoroutinefunction(handler):
            return await handler(msg)
        return handler(msg)  # type: ignore[return-value]

    def get_card(self) -> AgentCard:
        """Return an ``AgentCard`` describing this server.

        The card includes the server's identity, description, skills,
        channels, and HTTP endpoint.

        Returns:
            An ``AgentCard`` for directory registration or external queries.
        """
        return AgentCard(
            identity=self._identity,
            description=self._description,
            skills=self._skills,
            channels=self._channels,
            endpoints={"http": f"http://{self._host}:{self._port}"},
        )

    def register_with_directory(
        self,
        directory: AgentDirectory,
    ) -> DiscoveryEntry:
        """Register this server's agent card with a directory.

        Args:
            directory: The ``AgentDirectory`` to register with.

        Returns:
            The ``DiscoveryEntry`` created by the directory.
        """
        return directory.register(self.get_card())
