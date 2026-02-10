"""Webhook endpoints — Jira issue updates."""

from datetime import datetime
from fastapi import APIRouter, Request
from sqlalchemy import select

from app.db.database import async_session
from app.models import Task
from app.services.jira_service import JiraService

router = APIRouter()


@router.post("/jira")
async def jira_webhook(request: Request):
    """Handle Jira webhook events (jira:issue_updated)."""
    body = await request.json()

    event = body.get("webhookEvent", "")
    if event != "jira:issue_updated":
        return {"ok": True, "skipped": True}

    issue = body.get("issue", {})
    issue_key = issue.get("key")
    if not issue_key:
        return {"ok": True, "skipped": True}

    fields = issue.get("fields", {})
    jira_status = fields.get("status", {}).get("name", "")

    async with async_session() as db:
        result = await db.execute(
            select(Task).where(Task.jira_issue_key == issue_key)
        )
        task = result.scalar_one_or_none()
        if not task:
            return {"ok": True, "skipped": True}

        new_status = JiraService.parse_jira_status(jira_status)
        if new_status != task.status:
            task.status = new_status
            task.updated_at = datetime.utcnow()
            await db.commit()

    return {"ok": True, "updated": True, "issue_key": issue_key}
