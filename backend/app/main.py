import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.database import init_db
from app.api import auth, projects, tasks, ai, activity, jira, webhooks, sprints, pulse, gamification
from app.api import agents as agents_api

settings = get_settings()
logger = logging.getLogger(__name__)

_registry = None
_scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _registry, _scheduler
    await init_db()

    # Start agent system if enabled
    if settings.agents_enabled:
        from app.agents.event_bus import event_bus
        from app.agents.registry import create_registry
        from app.agents.scheduler import Scheduler
        from app.agents.analytics_insights import AnalyticsInsightsAgent

        _registry = create_registry()
        agents_api.set_registry(_registry)
        agents_api.set_event_bus(event_bus)

        await _registry.start_all()

        # Set up scheduler for analytics agent
        _scheduler = Scheduler()
        analytics_agent = _registry.get("analytics_insights")
        if analytics_agent and isinstance(analytics_agent, AnalyticsInsightsAgent):
            _scheduler.add_job(
                "analytics_daily",
                analytics_agent.run_scheduled_report,
                interval_seconds=settings.agent_analytics_schedule_hours * 3600,
            )
        await _scheduler.start()
        logger.info("Agent fleet started")

    yield

    # Shutdown
    if _scheduler:
        await _scheduler.stop()
    if _registry:
        await _registry.stop_all()
        logger.info("Agent fleet stopped")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"^chrome-extension://.*$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(tasks.router, prefix="/api/projects", tags=["tasks"])
app.include_router(ai.router, prefix="/api/projects", tags=["ai"])
app.include_router(activity.router, prefix="/api/projects", tags=["activity"])
app.include_router(jira.router, prefix="/api/projects", tags=["jira"])
app.include_router(sprints.router, prefix="/api/projects", tags=["sprints"])
app.include_router(pulse.router, prefix="/api/projects", tags=["pulse"])
app.include_router(gamification.router, prefix="/api/projects", tags=["gamification"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])
app.include_router(agents_api.router, prefix="/api", tags=["agents"])


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": settings.app_name}
