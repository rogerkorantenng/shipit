from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.database import init_db
from app.api import auth, projects, tasks, ai, activity, jira, webhooks, sprints, pulse, gamification

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


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


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": settings.app_name}
