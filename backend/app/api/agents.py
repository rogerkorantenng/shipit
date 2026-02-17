"""Agent management API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.models.agent_state import AgentConfig
from app.models.agent_event import AgentEvent
from app.models.service_connection import ServiceConnection

router = APIRouter()

# Will be set by main.py at startup
_registry = None
_event_bus = None


def set_registry(registry):
    global _registry
    _registry = registry


def set_event_bus(bus):
    global _event_bus
    _event_bus = bus


# --- Request/Response schemas ---

class AgentConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    config: Optional[dict] = None


class AgentTrigger(BaseModel):
    event_data: dict = {}


class ServiceConnectionCreate(BaseModel):
    service_type: str
    base_url: Optional[str] = None
    api_token: str
    config: Optional[dict] = None


# --- Global fleet status ---

@router.get("/agents/status")
async def fleet_status(user: User = Depends(get_current_user)):
    if not _registry:
        return {"agents": [], "bus_running": False}
    return {
        "agents": _registry.status(),
        "bus_running": _event_bus.is_running if _event_bus else False,
    }


# --- Per-project agent configs ---

@router.get("/projects/{project_id}/agents")
async def list_project_agents(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AgentConfig).where(AgentConfig.project_id == project_id)
    )
    configs = {c.agent_name: c for c in result.scalars().all()}

    agents = []
    if _registry:
        for agent in _registry.all_agents():
            cfg = configs.get(agent.name)
            agent_data = agent.to_dict()
            agent_data["project_config"] = {
                "enabled": cfg.enabled if cfg else True,
                "config": cfg.config if cfg else {},
                "last_run_at": cfg.last_run_at.isoformat() if cfg and cfg.last_run_at else None,
                "total_events_processed": cfg.total_events_processed if cfg else 0,
            }
            agents.append(agent_data)

    return {"agents": agents}


@router.put("/projects/{project_id}/agents/{agent_name}")
async def update_agent_config(
    project_id: int,
    agent_name: str,
    data: AgentConfigUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AgentConfig).where(
            AgentConfig.project_id == project_id,
            AgentConfig.agent_name == agent_name,
        )
    )
    config = result.scalars().first()

    if not config:
        config = AgentConfig(
            project_id=project_id,
            agent_name=agent_name,
            enabled=data.enabled if data.enabled is not None else True,
            config=data.config or {},
        )
        db.add(config)
    else:
        if data.enabled is not None:
            config.enabled = data.enabled
        if data.config is not None:
            config.config = data.config

    await db.commit()
    return {"status": "updated", "agent_name": agent_name}


@router.post("/projects/{project_id}/agents/{agent_name}/trigger")
async def trigger_agent(
    project_id: int,
    agent_name: str,
    data: AgentTrigger,
    user: User = Depends(get_current_user),
):
    if not _registry:
        raise HTTPException(status_code=503, detail="Agent system not initialized")

    agent = _registry.get(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    from app.agents.event_bus import Event, EventType

    if agent.subscribed_events:
        # Merge user-provided data with rich demo defaults for manual triggers
        event_data = {**_get_demo_data(agent_name), **data.event_data}
        event = Event(
            type=agent.subscribed_events[0],
            data=event_data,
            source_agent="manual_trigger",
            project_id=project_id,
        )
        await _event_bus.publish(event)

    return {"status": "triggered", "agent_name": agent_name}


_SAMPLE_DIFF = """\
diff --git a/src/auth/login.py b/src/auth/login.py
--- a/src/auth/login.py
+++ b/src/auth/login.py
@@ -12,6 +12,28 @@ from app.models.user import User
+import hashlib
+import os
+
+def create_session(user: User, request: Request) -> str:
+    token = hashlib.sha256(os.urandom(32)).hexdigest()
+    session = Session(user_id=user.id, token=token, ip=request.client.host)
+    db.add(session)
+    return token
+
+def verify_token(token: str) -> User | None:
+    session = db.query(Session).filter_by(token=token).first()
+    if not session or session.expired:
+        return None
+    return session.user
+
+@router.post("/login")
+async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
+    user = await db.execute(
+        select(User).where(User.email == credentials.email)
+    )
+    user = user.scalars().first()
+    if not user or not verify_password(credentials.password, user.hashed_password):
+        raise HTTPException(status_code=401, detail="Invalid credentials")
+    token = create_session(user, request)
+    return {"access_token": token, "user": user.to_dict()}

diff --git a/src/api/tasks.py b/src/api/tasks.py
--- a/src/api/tasks.py
+++ b/src/api/tasks.py
@@ -45,3 +45,18 @@ async def update_task(task_id: int, data: TaskUpdate):
+@router.delete("/{task_id}")
+async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
+    query = f"DELETE FROM tasks WHERE id = {task_id}"
+    await db.execute(text(query))
+    await db.commit()
+    return {"deleted": True}
"""


def _get_demo_data(agent_name: str) -> dict:
    """Return realistic demo data for manual agent triggers."""
    demos = {
        "product_intelligence": {
            "key": "SHIP-142",
            "title": "Implement real-time WebSocket notifications for task updates",
            "description": (
                "As a project manager, I need real-time notifications when tasks "
                "are updated so the team stays synchronized. Requirements:\n"
                "- WebSocket connection per authenticated user\n"
                "- Notify on task status changes, assignments, comments\n"
                "- Support @mentions with push notifications\n"
                "- Graceful reconnection with exponential backoff\n"
                "- Message queue for offline users"
            ),
            "status": "To Do",
            "priority": "High",
            "reporter": "Roger Koranteng",
            "project_key": "SHIP",
        },
        "design_sync": {
            "file_key": "figma-abc123xyz",
            "file_name": "ShipIt Design System v3",
            "demo_design_data": {
                "file_key": "figma-abc123xyz",
                "name": "ShipIt Design System v3",
                "last_modified": "2025-02-15T14:30:00Z",
                "components": {
                    "TaskCard": {"description": "Kanban task card with priority badge, assignee avatar, and due date", "width": 320, "height": 180},
                    "AgentStatusBadge": {"description": "Pill-shaped status indicator with animated pulse for running agents", "width": 120, "height": 32},
                    "NotificationPanel": {"description": "Slide-out panel with grouped notification items and mark-all-read", "width": 380, "height": 600},
                    "SprintBoard": {"description": "Horizontal scrolling board with column headers showing task counts", "width": 1200, "height": 800},
                },
            },
        },
        "code_orchestration": {
            "issue_id": "42",
            "title": "Implement WebSocket notification system",
            "description": "Real-time push notifications via WebSocket for task updates and agent events.",
            "analysis": {
                "summary": "websocket-notification-system",
                "stories": [
                    {"title": "WebSocket connection manager", "description": "Handle auth, reconnection, heartbeat"},
                    {"title": "Event broadcaster", "description": "Fan-out task events to subscribed clients"},
                ],
            },
        },
        "security_compliance": {
            "mr_iid": 87,
            "title": "feat: Add user authentication and task deletion endpoint",
            "source_branch": "feature/SHIP-142-auth-system",
            "target_branch": "main",
            "diff": _SAMPLE_DIFF,
            "files": ["src/auth/login.py", "src/api/tasks.py"],
        },
        "test_intelligence": {
            "mr_iid": 87,
            "title": "feat: Add user authentication and task deletion endpoint",
            "source_branch": "feature/SHIP-142-auth-system",
            "target_branch": "main",
            "diff": _SAMPLE_DIFF,
            "files": ["src/auth/login.py", "src/api/tasks.py"],
        },
        "review_coordination": {
            "mr_iid": 87,
            "title": "feat: Add user authentication and task deletion endpoint",
            "source_branch": "feature/SHIP-142-auth-system",
            "target_branch": "main",
            "diff": _SAMPLE_DIFF,
            "files": ["src/auth/login.py", "src/api/tasks.py"],
        },
        "deployment_orchestrator": {
            "ref": "main",
            "mr_iid": 87,
            "title": "feat: Add user authentication and task deletion endpoint",
            "commit_messages": [
                "feat: implement session-based auth with token management",
                "feat: add task deletion endpoint with soft-delete",
                "fix: handle expired sessions gracefully",
                "chore: add migration for sessions table",
            ],
        },
        "analytics_insights": {},
    }
    return demos.get(agent_name, {})


# --- Event log ---

@router.get("/projects/{project_id}/agents/events")
async def list_agent_events(
    project_id: int,
    limit: int = 50,
    user: User = Depends(get_current_user),
):
    if not _event_bus:
        return {"events": []}

    events = _event_bus.get_history(limit=limit, project_id=project_id)
    return {
        "events": [
            {
                "event_id": e.event_id,
                "type": e.type.value,
                "source_agent": e.source_agent,
                "project_id": e.project_id,
                "data": e.data,
                "timestamp": e.timestamp.isoformat(),
                "correlation_id": e.correlation_id,
            }
            for e in events
        ]
    }


# --- Service connections ---

@router.post("/projects/{project_id}/connections")
async def create_connection(
    project_id: int,
    data: ServiceConnectionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ServiceConnection).where(
            ServiceConnection.project_id == project_id,
            ServiceConnection.service_type == data.service_type,
        )
    )
    existing = result.scalars().first()

    # Strip whitespace from tokens and config values
    clean_token = data.api_token.strip()
    clean_config = {}
    for k, v in (data.config or {}).items():
        clean_config[k] = v.strip() if isinstance(v, str) else v

    if existing:
        existing.base_url = data.base_url
        existing.api_token = clean_token
        existing.config = clean_config
        existing.enabled = True
    else:
        conn = ServiceConnection(
            project_id=project_id,
            service_type=data.service_type,
            base_url=data.base_url,
            api_token=clean_token,
            config=clean_config,
        )
        db.add(conn)

    await db.commit()
    return {"status": "connected", "service_type": data.service_type}


@router.get("/projects/{project_id}/connections")
async def list_connections(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ServiceConnection).where(ServiceConnection.project_id == project_id)
    )
    connections = result.scalars().all()
    def mask_token(token: str | None) -> str | None:
        if not token:
            return None
        if len(token) <= 8:
            return "****" + token[-2:]
        return token[:4] + "****" + token[-4:]

    def mask_config(config: dict | None) -> dict | None:
        if not config:
            return config
        masked = {}
        for k, v in config.items():
            if isinstance(v, str) and k in ("app_key", "api_key", "secret"):
                masked[k] = mask_token(v)
            else:
                masked[k] = v
        return masked

    return {
        "connections": [
            {
                "id": c.id,
                "service_type": c.service_type,
                "base_url": c.base_url,
                "enabled": c.enabled,
                "config": c.config,
                "masked_config": mask_config(c.config),
                "last_sync_at": c.last_sync_at.isoformat() if c.last_sync_at else None,
                "has_token": bool(c.api_token),
                "masked_token": mask_token(c.api_token),
            }
            for c in connections
        ]
    }


@router.get("/projects/{project_id}/connections/{service_type}/reveal")
async def reveal_connection(
    project_id: int,
    service_type: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ServiceConnection).where(
            ServiceConnection.project_id == project_id,
            ServiceConnection.service_type == service_type,
        )
    )
    conn = result.scalars().first()
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")

    return {
        "service_type": conn.service_type,
        "base_url": conn.base_url,
        "api_token": conn.api_token or "",
        "config": conn.config or {},
    }


@router.delete("/projects/{project_id}/connections/{service_type}")
async def delete_connection(
    project_id: int,
    service_type: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(ServiceConnection).where(
            ServiceConnection.project_id == project_id,
            ServiceConnection.service_type == service_type,
        )
    )
    await db.commit()
    return {"status": "disconnected", "service_type": service_type}


@router.post("/projects/{project_id}/connections/{service_type}/test")
async def test_connection(
    project_id: int,
    service_type: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ServiceConnection).where(
            ServiceConnection.project_id == project_id,
            ServiceConnection.service_type == service_type,
        )
    )
    conn = result.scalars().first()
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")

    try:
        if service_type == "gitlab":
            from app.adapters.gitlab_adapter import GitLabAdapter
            adapter = GitLabAdapter(conn.base_url or "https://gitlab.com", conn.api_token)
            await adapter.test_connection()
        elif service_type == "figma":
            from app.adapters.figma_adapter import FigmaAdapter
            adapter = FigmaAdapter(conn.api_token)
            await adapter.test_connection()
        elif service_type == "slack":
            from app.adapters.slack_adapter import SlackAdapter
            adapter = SlackAdapter(conn.api_token)
            await adapter.test_connection()
        elif service_type == "datadog":
            from app.adapters.monitoring_adapter import DatadogAdapter
            adapter = DatadogAdapter(
                conn.api_token,
                (conn.config or {}).get("app_key", ""),
            )
            await adapter.test_connection()
        elif service_type == "sentry":
            from app.adapters.monitoring_adapter import SentryAdapter
            adapter = SentryAdapter(conn.api_token)
            await adapter.test_connection()
        else:
            raise HTTPException(status_code=400, detail=f"Unknown service type: {service_type}")

        return {"status": "ok", "service_type": service_type}
    except HTTPException:
        raise
    except Exception as e:
        return {"status": "error", "service_type": service_type, "error": str(e)}
