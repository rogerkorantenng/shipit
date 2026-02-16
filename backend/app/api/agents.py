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
        event = Event(
            type=agent.subscribed_events[0],
            data=data.event_data,
            source_agent="manual_trigger",
            project_id=project_id,
        )
        await _event_bus.publish(event)

    return {"status": "triggered", "agent_name": agent_name}


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

    if existing:
        existing.base_url = data.base_url
        existing.api_token = data.api_token
        existing.config = data.config or {}
        existing.enabled = True
    else:
        conn = ServiceConnection(
            project_id=project_id,
            service_type=data.service_type,
            base_url=data.base_url,
            api_token=data.api_token,
            config=data.config or {},
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
    return {
        "connections": [
            {
                "id": c.id,
                "service_type": c.service_type,
                "base_url": c.base_url,
                "enabled": c.enabled,
                "config": c.config,
                "last_sync_at": c.last_sync_at.isoformat() if c.last_sync_at else None,
                "has_token": bool(c.api_token),
            }
            for c in connections
        ]
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
