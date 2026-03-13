# -*- coding: utf-8 -*-
from fastapi import APIRouter

from .agent import router as agent_router
from .auth import router as auth_router
from .agents import router as agents_config_router
from .audit import router as audit_router
from .autonomy import router as autonomy_router
from .config import router as config_router
from .local_models import router as local_models_router
from .providers import router as providers_router
from .skills import router as skills_router
from .workspace import router as workspace_router
from .envs import router as envs_router
from .ollama_models import router as ollama_models_router
from .mcp import router as mcp_router
from ..crons.api import router as cron_router
from ..runner.api import router as runner_router
from .console import router as console_router
from .analytics import router as analytics_router
from .gamification import router as gamification_router
from .health import router as health_router
from .leaderboard import router as leaderboard_router
from .marketplace import router as marketplace_router
from .model_registry import router as model_registry_router
from .teams import router as teams_router
from .timeline import router as timeline_router
from .voice import router as voice_router
from .webhooks import router as webhooks_router
from .agentverse import router as agentverse_router
from .external_agents import router as external_agents_router
from .ide import router as ide_router
from .notifications import router as notifications_router
from .onboarding import router as onboarding_router
from .rag import router as rag_router
from .replay import router as replay_router
from .research import router as research_router
from .templates import router as templates_router
from .privacy import router as privacy_router
from .settings_api import router as settings_api_router
from .studio import router as studio_router
from .memory import router as memory_router
from .monitoring import router as monitoring_router
from .swarm_api import router as swarm_router
from .warroom_api import router as warroom_router
from .oauth import router as oauth_router
from .hardware import router as hardware_router

router = APIRouter()

router.include_router(agentverse_router)
router.include_router(auth_router)
router.include_router(oauth_router)
router.include_router(agent_router)
router.include_router(agents_config_router)
router.include_router(analytics_router)
router.include_router(audit_router)
router.include_router(autonomy_router)
router.include_router(config_router)
router.include_router(console_router)
router.include_router(cron_router)
router.include_router(gamification_router)
router.include_router(health_router)
router.include_router(leaderboard_router)
router.include_router(local_models_router)
router.include_router(marketplace_router)
router.include_router(model_registry_router)
router.include_router(mcp_router)
router.include_router(ollama_models_router)
router.include_router(providers_router)
router.include_router(rag_router)
router.include_router(runner_router)
router.include_router(skills_router)
router.include_router(teams_router)
router.include_router(timeline_router)
router.include_router(voice_router)
router.include_router(webhooks_router)
router.include_router(workspace_router)
router.include_router(envs_router)
router.include_router(external_agents_router)
router.include_router(ide_router)
router.include_router(notifications_router)
router.include_router(onboarding_router)
router.include_router(replay_router)
router.include_router(research_router)
router.include_router(templates_router)
router.include_router(privacy_router)
router.include_router(settings_api_router)
router.include_router(studio_router)
router.include_router(memory_router)
router.include_router(monitoring_router)
router.include_router(swarm_router)
router.include_router(warroom_router)
router.include_router(hardware_router)

__all__ = ["router"]
