"""Webhook endpoints — Jira, GitLab, Figma."""

import hashlib
import hmac
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy import select

from app.db.database import async_session
from app.models import Task
from app.models.service_connection import ServiceConnection
from app.services.jira_service import JiraService
from app.agents.event_bus import Event, EventType, event_bus
from app.config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)


async def _resolve_project_id(service_type: str, external_project_id: int | str | None) -> Optional[int]:
    """Look up the ShipIt project_id for an external service's project ID."""
    if not external_project_id:
        return None
    try:
        async with async_session() as db:
            result = await db.execute(
                select(ServiceConnection).where(
                    ServiceConnection.service_type == service_type,
                    ServiceConnection.enabled == True,
                )
            )
            for conn in result.scalars().all():
                config = conn.config or {}
                if str(config.get("project_id", "")) == str(external_project_id):
                    return conn.project_id
                # Also check file_key for Figma
                if service_type == "figma" and config.get("file_key") == str(external_project_id):
                    return conn.project_id
    except Exception:
        logger.exception(f"Failed to resolve {service_type} project_id")
    return None


# ─── Jira Webhook ───────────────────────────────────────────

@router.post("/jira")
async def jira_webhook(request: Request):
    """Handle Jira webhook events (jira:issue_updated, jira:issue_created)."""
    body = await request.json()

    event_name = body.get("webhookEvent", "")
    issue = body.get("issue", {})
    issue_key = issue.get("key")
    if not issue_key:
        return {"ok": True, "skipped": True}

    fields = issue.get("fields", {})
    jira_status = fields.get("status", {}).get("name", "")
    project_id = None

    async with async_session() as db:
        result = await db.execute(
            select(Task).where(Task.jira_issue_key == issue_key)
        )
        task = result.scalar_one_or_none()

        if task:
            project_id = task.project_id
            if event_name == "jira:issue_updated":
                new_status = JiraService.parse_jira_status(jira_status)
                if new_status != task.status:
                    task.status = new_status
                    task.updated_at = datetime.utcnow()
                    await db.commit()

    # Publish events to agent bus
    ticket_data = {
        "key": issue_key,
        "title": fields.get("summary", ""),
        "description": fields.get("description", ""),
        "status": jira_status,
        "priority": fields.get("priority", {}).get("name", ""),
        "assignee": fields.get("assignee", {}).get("displayName", "") if fields.get("assignee") else "",
        "labels": fields.get("labels", []),
    }

    if event_name == "jira:issue_created":
        await event_bus.publish(Event(
            type=EventType.JIRA_TICKET_CREATED,
            data=ticket_data,
            source_agent="jira_webhook",
            project_id=project_id,
        ))
    elif event_name == "jira:issue_updated":
        await event_bus.publish(Event(
            type=EventType.JIRA_TICKET_UPDATED,
            data=ticket_data,
            source_agent="jira_webhook",
            project_id=project_id,
        ))

    return {"ok": True, "updated": True, "issue_key": issue_key}


# ─── GitLab Webhook ─────────────────────────────────────────

@router.post("/gitlab")
async def gitlab_webhook(request: Request):
    """Handle GitLab webhook events (Push, MR, Pipeline)."""
    body = await request.json()
    event_type = request.headers.get("X-Gitlab-Event", "")

    logger.info(f"GitLab webhook: {event_type}")

    # Resolve GitLab project ID → ShipIt project ID
    gl_project_id = body.get("project", {}).get("id")
    if not gl_project_id and event_type == "Merge Request Hook":
        gl_project_id = body.get("object_attributes", {}).get("target_project_id")
    shipit_project_id = await _resolve_project_id("gitlab", gl_project_id)

    if event_type == "Push Hook":
        ref = body.get("ref", "")
        project = body.get("project", {})
        commits = body.get("commits", [])

        event = Event(
            type=EventType.MERGE_TO_MAIN if ref.endswith("/main") or ref.endswith("/master") else EventType.CODE_PUSHED,
            data={
                "ref": ref,
                "project_name": project.get("name", ""),
                "gitlab_project_id": project.get("id"),
                "commits": [
                    {"message": c.get("message", ""), "author": c.get("author", {}).get("name", "")}
                    for c in commits[:10]
                ],
                "total_commits": body.get("total_commits_count", 0),
            },
            source_agent="gitlab_webhook",
            project_id=shipit_project_id,
        )
        await event_bus.publish(event)

    elif event_type == "Merge Request Hook":
        mr = body.get("object_attributes", {})
        action = mr.get("action", "")

        mr_data = {
            "mr_iid": mr.get("iid"),
            "title": mr.get("title", ""),
            "source_branch": mr.get("source_branch", ""),
            "target_branch": mr.get("target_branch", ""),
            "author": mr.get("author_id"),
            "gitlab_project_id": mr.get("target_project_id"),
            "url": mr.get("url", ""),
        }

        if action == "open":
            await event_bus.publish(Event(
                type=EventType.PR_OPENED,
                data=mr_data,
                source_agent="gitlab_webhook",
                project_id=shipit_project_id,
            ))
        elif action == "merge":
            target = mr.get("target_branch", "")
            etype = EventType.MERGE_TO_MAIN if target in ("main", "master") else EventType.PR_APPROVED
            await event_bus.publish(Event(
                type=etype,
                data={**mr_data, "ref": target},
                source_agent="gitlab_webhook",
                project_id=shipit_project_id,
            ))
        elif action == "update" and mr.get("work_in_progress") is False:
            await event_bus.publish(Event(
                type=EventType.PR_READY_FOR_REVIEW,
                data=mr_data,
                source_agent="gitlab_webhook",
                project_id=shipit_project_id,
            ))
        elif action == "approved":
            await event_bus.publish(Event(
                type=EventType.PR_APPROVED,
                data=mr_data,
                source_agent="gitlab_webhook",
                project_id=shipit_project_id,
            ))

    elif event_type == "Pipeline Hook":
        pipeline = body.get("object_attributes", {})
        status = pipeline.get("status", "")

        pipeline_data = {
            "pipeline_id": pipeline.get("id"),
            "ref": pipeline.get("ref", ""),
            "status": status,
            "gitlab_project_id": body.get("project", {}).get("id"),
        }

        if status == "running":
            await event_bus.publish(Event(
                type=EventType.PIPELINE_STARTED,
                data=pipeline_data,
                source_agent="gitlab_webhook",
                project_id=shipit_project_id,
            ))
        elif status == "success":
            await event_bus.publish(Event(
                type=EventType.PIPELINE_COMPLETED,
                data=pipeline_data,
                source_agent="gitlab_webhook",
                project_id=shipit_project_id,
            ))
        elif status == "failed":
            await event_bus.publish(Event(
                type=EventType.PIPELINE_FAILED,
                data=pipeline_data,
                source_agent="gitlab_webhook",
                project_id=shipit_project_id,
            ))

    return {"ok": True}


# ─── Figma Webhook ──────────────────────────────────────────

@router.post("/figma")
async def figma_webhook(request: Request):
    """Handle Figma webhook events (file_update)."""
    body = await request.json()

    # Verify webhook signature if configured
    settings = get_settings()
    figma_secret = getattr(settings, "figma_webhook_secret", "")
    if figma_secret:
        signature = request.headers.get("X-Figma-Signature", "")
        raw_body = await request.body()
        expected = hmac.new(
            figma_secret.encode(), raw_body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=401, detail="Invalid signature")

    event_type = body.get("event_type", "")
    logger.info(f"Figma webhook: {event_type}")

    if event_type == "FILE_UPDATE":
        file_key = body.get("file_key", "")
        file_name = body.get("file_name", "")
        timestamp = body.get("timestamp", "")

        # Resolve Figma file_key → ShipIt project_id
        shipit_project_id = await _resolve_project_id("figma", file_key)

        await event_bus.publish(Event(
            type=EventType.FIGMA_DESIGN_CHANGED,
            data={
                "file_key": file_key,
                "file_name": file_name,
                "timestamp": timestamp,
                "triggered_by": body.get("triggered_by", {}),
            },
            source_agent="figma_webhook",
            project_id=shipit_project_id,
        ))

    return {"ok": True}
