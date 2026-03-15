# -*- coding: utf-8 -*-
# pylint: disable=unused-argument too-many-branches too-many-statements
import asyncio
import functools
import json
import logging
from pathlib import Path

try:
    import sentry_sdk
except ImportError:
    sentry_sdk = None


async def _award_xp_background(
    entity_id: str,
    category: str,
    reason: str,
    amount: int = 10,
) -> None:
    """Fire-and-forget XP award via internal HTTP. Never raises."""
    try:
        import httpx  # noqa: PLC0415

        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.post(
                "http://localhost:8088/api/gamification/xp",
                json={
                    "entity_id": entity_id,
                    "entity_type": "agent",
                    "amount": amount,
                    "category": category,
                    "reason": reason,
                },
            )
    except Exception:
        pass  # XP is best-effort, never block the agent


from agentscope.pipeline import stream_printing_messages
from agentscope_runtime.engine.runner import Runner
from agentscope_runtime.engine.schemas.agent_schemas import AgentRequest
from dotenv import load_dotenv

from .query_error_dump import write_query_error_dump
from .session import SafeJSONSession
from .utils import build_env_context
from ..channels.schema import DEFAULT_CHANNEL
from ...agents.memory import MemoryManager
from ...agents.react_agent import ProwlrBotAgent
from ...config import load_config
from ...constant import WORKING_DIR
from ...replay.recorder import SessionRecorder, EventType as ReplayEventType

logger = logging.getLogger(__name__)

_replay_recorder = SessionRecorder(db_path=WORKING_DIR / "replay.db")


class AgentRunner(Runner):
    def __init__(self) -> None:
        super().__init__()
        self.framework_type = "agentscope"
        self._chat_manager = None  # Store chat_manager reference
        self._mcp_manager = None  # MCP client manager for hot-reload

        self.memory_manager: MemoryManager | None = None

    def set_chat_manager(self, chat_manager):
        """Set chat manager for auto-registration.

        Args:
            chat_manager: ChatManager instance
        """
        self._chat_manager = chat_manager

    def set_mcp_manager(self, mcp_manager):
        """Set MCP client manager for hot-reload support.

        Args:
            mcp_manager: MCPClientManager instance
        """
        self._mcp_manager = mcp_manager

    async def query_handler(
        self,
        msgs,
        request: AgentRequest = None,
        **kwargs,
    ):
        """
        Handle agent query.
        """

        agent = None
        chat = None
        session_state_loaded = False
        _query_succeeded = False
        replay_sess = None

        try:
            session_id = request.session_id
            user_id = request.user_id
            channel = getattr(request, "channel", DEFAULT_CHANNEL)

            logger.info(
                "Handle agent query:\n%s",
                json.dumps(
                    {
                        "session_id": session_id,
                        "user_id": user_id,
                        "channel": channel,
                        "msgs_len": len(msgs) if msgs else 0,
                        "msgs_str": str(msgs)[:300] + "...",
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )

            env_context = build_env_context(
                session_id=session_id,
                user_id=user_id,
                channel=channel,
                working_dir=str(WORKING_DIR),
            )

            # Get MCP clients from manager (hot-reloadable)
            mcp_clients = []
            if self._mcp_manager is not None:
                mcp_clients = await self._mcp_manager.get_clients()

            config = load_config()
            max_iters = config.agents.running.max_iters
            max_input_length = config.agents.running.max_input_length

            agent = ProwlrBotAgent(
                env_context=env_context,
                mcp_clients=mcp_clients,
                memory_manager=self.memory_manager,
                max_iters=max_iters,
                max_input_length=max_input_length,
            )
            await agent.register_mcp_clients()
            agent.set_console_output_enabled(enabled=False)

            logger.debug(
                f"Agent Query msgs {msgs}",
            )

            name = "New Chat"
            if len(msgs) > 0:
                content = msgs[0].get_text_content()
                if content:
                    name = msgs[0].get_text_content()[:10]
                else:
                    name = "Media Message"

            try:
                loop = asyncio.get_running_loop()
                replay_sess = await loop.run_in_executor(
                    None,
                    functools.partial(
                        _replay_recorder.start_recording,
                        session_id,
                        agent_id="default",
                        title=name or session_id[:8],
                    ),
                )
            except Exception:
                pass  # replay is best-effort, never block a query

            if self._chat_manager is not None:
                chat = await self._chat_manager.get_or_create_chat(
                    session_id,
                    user_id,
                    channel,
                    name=name,
                )

            await self.session.load_session_state(
                session_id=session_id,
                user_id=user_id,
                agent=agent,
            )
            session_state_loaded = True

            # Rebuild system prompt so it always reflects the latest
            # AGENTS.md / SOUL.md / PROFILE.md, not the stale one saved
            # in the session state.
            agent.rebuild_sys_prompt()

            # Inject autonomy policy into agent system prompt (best-effort)
            try:
                from ...autonomy.controller import AutonomyController

                controller = AutonomyController()
                try:
                    policy = controller.get_policy(session_id or "default")
                    if policy:
                        policy_note = (
                            f"\n\n## Autonomy Policy\n"
                            f"Level: {policy.level.value}\n"
                            f"Blocked tools: {', '.join(policy.blocked_tools) or 'none'}\n"
                            f"Require approval for: {', '.join(policy.require_approval_for) or 'none'}\n"
                            f"You must respect these constraints."
                        )
                        agent.sys_prompt = agent.sys_prompt + policy_note
                        logger.debug(
                            "Injected autonomy policy (level=%s) for session %s",
                            policy.level.value,
                            session_id,
                        )
                finally:
                    controller.close()
            except Exception:  # pylint: disable=broad-except
                pass  # autonomy is best-effort; never block a query

            # Record the user message before streaming starts
            if replay_sess is not None and msgs:
                try:
                    _loop = asyncio.get_running_loop()
                    user_content = (
                        msgs[0].get_text_content()
                        if hasattr(msgs[0], "get_text_content")
                        else str(msgs[0])
                    )
                    await _loop.run_in_executor(
                        None,
                        functools.partial(
                            _replay_recorder.record_event,
                            replay_sess.id,
                            ReplayEventType.USER_MESSAGE,
                            content=(user_content or "")[:500],
                        ),
                    )
                except Exception:
                    pass  # replay is best-effort

            async for msg, last in stream_printing_messages(
                agents=[agent],
                coroutine_task=agent(msgs),
            ):
                yield msg, last
                if replay_sess is not None:
                    try:
                        _loop = asyncio.get_running_loop()
                        await _loop.run_in_executor(
                            None,
                            functools.partial(
                                _replay_recorder.record_event,
                                replay_sess.id,
                                ReplayEventType.AGENT_RESPONSE,
                                content=str(msg)[:500],
                            ),
                        )
                    except Exception:
                        pass  # replay is best-effort

            _query_succeeded = True
            asyncio.create_task(
                _award_xp_background(
                    entity_id=session_id or "default",
                    category="task_complete",
                    reason="Completed agent task",
                    amount=10,
                ),
            )

        except asyncio.CancelledError:
            if agent is not None:
                await agent.interrupt()
            raise
        except Exception as e:
            if sentry_sdk is not None:
                sentry_sdk.capture_exception(e)
            debug_dump_path = write_query_error_dump(
                request=request,
                exc=e,
                locals_=locals(),
            )
            path_hint = f"\n(Details:  {debug_dump_path})" if debug_dump_path else ""
            logger.exception(f"Error in query handler: {e}{path_hint}")
            if debug_dump_path:
                setattr(e, "debug_dump_path", debug_dump_path)
                if hasattr(e, "add_note"):
                    e.add_note(
                        f"(Details:  {debug_dump_path})",
                    )
                suffix = f"\n(Details:  {debug_dump_path})"
                e.args = (
                    (f"{e.args[0]}{suffix}" if e.args else suffix.strip()),
                ) + e.args[1:]
            raise
        finally:
            if agent is not None and session_state_loaded:
                await self.session.save_session_state(
                    session_id=session_id,
                    user_id=user_id,
                    agent=agent,
                )

            if self._chat_manager is not None and chat is not None:
                await self._chat_manager.update_chat(chat)

            if replay_sess is not None:
                try:
                    _loop = asyncio.get_running_loop()
                    await _loop.run_in_executor(
                        None,
                        functools.partial(
                            _replay_recorder.stop_recording,
                            replay_sess.id,
                        ),
                    )
                except Exception:
                    pass  # replay is best-effort

    async def init_handler(self, *args, **kwargs):
        """
        Init handler.
        """
        # Load .env only when not in container (production uses Fly secrets / env, no .env file)
        from prowlrbot.constant import RUNNING_IN_CONTAINER

        in_container = RUNNING_IN_CONTAINER and str(
            RUNNING_IN_CONTAINER,
        ).lower() in (
            "1",
            "true",
            "yes",
        )
        if not in_container:
            env_path = Path(__file__).resolve().parents[4] / ".env"
            if env_path.exists():
                load_dotenv(env_path)
                logger.debug("Loaded environment variables from .env")
            else:
                logger.debug(
                    "No .env file; using existing environment variables",
                )

        session_dir = str(WORKING_DIR / "sessions")
        self.session = SafeJSONSession(save_dir=session_dir)

        try:
            if self.memory_manager is None:
                self.memory_manager = MemoryManager(
                    working_dir=str(WORKING_DIR),
                )
            await self.memory_manager.start()
        except Exception as e:
            logger.exception(f"MemoryManager start failed: {e}")

    async def shutdown_handler(self, *args, **kwargs):
        """
        Shutdown handler.
        """
        try:
            await self.memory_manager.close()
        except Exception as e:
            logger.warning(f"MemoryManager stop failed: {e}")
