"""Slack Notifier — listens for SLACK_NOTIFICATION events and posts to Slack."""

import logging

from app.agents.base import BaseAgent
from app.agents.event_bus import Event, EventType

logger = logging.getLogger(__name__)


class SlackNotifierAgent(BaseAgent):

    @property
    def name(self) -> str:
        return "slack_notifier"

    @property
    def description(self) -> str:
        return "Delivers Slack notifications from all agents to connected workspaces"

    @property
    def subscribed_events(self) -> list[EventType]:
        return [EventType.SLACK_NOTIFICATION]

    async def handle_event(self, event: Event) -> None:
        data = event.data
        message = data.get("message", "")
        channel = data.get("channel")
        project_id = event.project_id

        logger.warning(f"[SlackNotifier] Received event project_id={project_id} message_len={len(message)}")

        if not message:
            logger.warning("[SlackNotifier] Empty message, skipping")
            return

        # Look up Slack connection for this project
        conn = await self._get_slack_connection(project_id)
        if not conn:
            logger.warning(f"[SlackNotifier] No Slack connection for project {project_id}")
            return

        try:
            from app.adapters.slack_adapter import SlackAdapter
            from app.config import get_settings

            settings = get_settings()
            token = conn.api_token
            slack = SlackAdapter(token)

            target_channel = channel or (conn.config or {}).get("default_channel") or settings.slack_default_channel or "general"

            logger.warning(f"[SlackNotifier] Sending to #{target_channel}")
            await slack.post_message(
                channel=target_channel,
                text=message,
            )
            logger.warning(f"[SlackNotifier] Message sent to #{target_channel} for project {project_id}")
        except Exception:
            logger.exception(f"[SlackNotifier] Failed to send for project {project_id}")

    async def _get_slack_connection(self, project_id: int | None):
        if not project_id:
            # Try to find any enabled Slack connection
            try:
                from sqlalchemy import select
                from app.models.service_connection import ServiceConnection

                async with self.get_db_session() as db:
                    result = await db.execute(
                        select(ServiceConnection).where(
                            ServiceConnection.service_type == "slack",
                            ServiceConnection.enabled == True,
                        )
                    )
                    return result.scalars().first()
            except Exception:
                logger.exception("Failed to look up Slack connection")
            return None

        try:
            from sqlalchemy import select
            from app.models.service_connection import ServiceConnection

            async with self.get_db_session() as db:
                result = await db.execute(
                    select(ServiceConnection).where(
                        ServiceConnection.project_id == project_id,
                        ServiceConnection.service_type == "slack",
                        ServiceConnection.enabled == True,
                    )
                )
                return result.scalars().first()
        except Exception:
            logger.exception("Failed to look up Slack connection")
        return None
