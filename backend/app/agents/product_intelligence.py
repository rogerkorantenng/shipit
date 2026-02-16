"""Agent 1: Product Intelligence - Analyzes Jira tickets, extracts requirements."""

import json
import logging

from app.agents.base import BaseAgent
from app.agents.event_bus import Event, EventType
from app.services import agent_ai_service

logger = logging.getLogger(__name__)


class ProductIntelligenceAgent(BaseAgent):

    @property
    def name(self) -> str:
        return "product_intelligence"

    @property
    def description(self) -> str:
        return (
            "Analyzes Jira tickets to extract requirements, stories, "
            "acceptance criteria, and complexity estimates"
        )

    @property
    def subscribed_events(self) -> list[EventType]:
        return [EventType.JIRA_TICKET_CREATED, EventType.JIRA_TICKET_UPDATED]

    async def handle_event(self, event: Event) -> None:
        ticket = event.data
        logger.info(f"Analyzing ticket: {ticket.get('key', 'unknown')}")

        analysis = await agent_ai_service.analyze_requirements(ticket)

        # Publish requirements analyzed
        await self.publish(Event(
            type=EventType.REQUIREMENTS_ANALYZED,
            data={
                "ticket_key": ticket.get("key"),
                "analysis": analysis,
                "stories": analysis.get("stories", []),
            },
            source_agent=self.name,
            project_id=event.project_id,
            correlation_id=event.correlation_id or event.event_id,
        ))

        # Tag complexity
        await self.publish(Event(
            type=EventType.COMPLEXITY_TAGGED,
            data={
                "ticket_key": ticket.get("key"),
                "complexity": analysis.get("complexity", "medium"),
                "estimated_effort_hours": analysis.get("estimated_effort_hours", 4),
                "tags": analysis.get("tags", []),
            },
            source_agent=self.name,
            project_id=event.project_id,
            correlation_id=event.correlation_id or event.event_id,
        ))

        # Extract stories if any
        stories = analysis.get("stories", [])
        if stories:
            await self.publish(Event(
                type=EventType.STORIES_EXTRACTED,
                data={
                    "ticket_key": ticket.get("key"),
                    "stories": stories,
                },
                source_agent=self.name,
                project_id=event.project_id,
                correlation_id=event.correlation_id or event.event_id,
            ))

        # Create GitLab issues if connection exists
        await self._create_gitlab_issues(event.project_id, ticket, stories)

        # Notify Slack
        await self.publish(Event(
            type=EventType.SLACK_NOTIFICATION,
            data={
                "message": (
                    f"*Requirements Analyzed* for `{ticket.get('key', 'N/A')}`\n"
                    f"Complexity: {analysis.get('complexity', 'medium')} | "
                    f"Effort: {analysis.get('estimated_effort_hours', '?')}h | "
                    f"Stories: {len(stories)}"
                ),
            },
            source_agent=self.name,
            project_id=event.project_id,
            correlation_id=event.correlation_id or event.event_id,
        ))

    async def _create_gitlab_issues(
        self, project_id: int | None, ticket: dict, stories: list[dict]
    ) -> None:
        if not project_id or not stories:
            return

        try:
            from sqlalchemy import select
            from app.models.service_connection import ServiceConnection
            from app.adapters.gitlab_adapter import GitLabAdapter

            async with self.get_db_session() as db:
                result = await db.execute(
                    select(ServiceConnection).where(
                        ServiceConnection.project_id == project_id,
                        ServiceConnection.service_type == "gitlab",
                        ServiceConnection.enabled == True,
                    )
                )
                conn = result.scalars().first()
                if not conn:
                    return

                gitlab = GitLabAdapter(conn.base_url or "https://gitlab.com", conn.api_token)
                gl_project_id = (conn.config or {}).get("project_id")
                if not gl_project_id:
                    return

                for story in stories[:5]:
                    await gitlab.create_issue(
                        gl_project_id,
                        title=story.get("title", "Untitled"),
                        description=(
                            f"**From Jira:** {ticket.get('key', '')}\n\n"
                            f"{story.get('description', '')}\n\n"
                            f"**Acceptance Criteria:**\n{story.get('acceptance_criteria', 'N/A')}"
                        ),
                        labels=["auto-generated", "from-jira"],
                    )
        except Exception:
            logger.exception("Failed to create GitLab issues")
