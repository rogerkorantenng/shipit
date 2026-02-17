"""Agent 2: Design Sync - Syncs Figma designs with Jira tickets and code."""

import logging

from app.agents.base import BaseAgent
from app.agents.event_bus import Event, EventType
from app.services import agent_ai_service

logger = logging.getLogger(__name__)


class DesignSyncAgent(BaseAgent):

    @property
    def name(self) -> str:
        return "design_sync"

    @property
    def description(self) -> str:
        return (
            "Syncs Figma design changes with Jira tickets, generates technical "
            "implementation notes, and creates GitLab issues"
        )

    @property
    def subscribed_events(self) -> list[EventType]:
        return [EventType.FIGMA_DESIGN_CHANGED]

    async def handle_event(self, event: Event) -> None:
        data = event.data
        file_key = data.get("file_key", "")
        project_id = event.project_id

        logger.info(f"Design change detected for Figma file: {file_key}")

        # Fetch design data from Figma, fall back to inline demo data
        design_data = await self._fetch_design_data(project_id, file_key)
        if not design_data:
            design_data = data.get("demo_design_data", {})
        if not design_data:
            logger.info("No design data available")
            return

        # Compare with existing Jira tickets
        ticket_data = await self._get_related_tickets(project_id)

        # Generate implementation notes via AI
        impl_notes = await agent_ai_service.generate_implementation_notes(
            design_data, ticket_data
        )

        # Publish design comparison
        await self.publish(Event(
            type=EventType.DESIGN_COMPARED,
            data={
                "file_key": file_key,
                "alignment": impl_notes.get("design_ticket_alignment", "partial"),
                "component_specs": impl_notes.get("component_specs", []),
            },
            source_agent=self.name,
            project_id=project_id,
            correlation_id=event.correlation_id,
        ))

        # Publish implementation notes
        await self.publish(Event(
            type=EventType.IMPLEMENTATION_NOTES_GENERATED,
            data={
                "file_key": file_key,
                "notes": impl_notes,
                "ticket_key": ticket_data.get("key"),
                "implementation_steps": impl_notes.get("implementation_steps", []),
            },
            source_agent=self.name,
            project_id=project_id,
            correlation_id=event.correlation_id,
        ))

        # Create/update GitLab issues
        await self._sync_gitlab_issues(project_id, file_key, impl_notes)

        # Notify Slack
        alignment = impl_notes.get("design_ticket_alignment", "partial")
        specs_count = len(impl_notes.get("component_specs", []))
        await self.publish(Event(
            type=EventType.SLACK_NOTIFICATION,
            data={
                "message": (
                    f"*Design Update* - Figma file `{file_key}`\n"
                    f"Alignment with tickets: {alignment}\n"
                    f"Component specs generated: {specs_count}"
                ),
            },
            source_agent=self.name,
            project_id=project_id,
            correlation_id=event.correlation_id,
        ))

    async def _fetch_design_data(
        self, project_id: int | None, file_key: str
    ) -> dict:
        if not project_id:
            return {}

        try:
            from sqlalchemy import select
            from app.models.service_connection import ServiceConnection
            from app.adapters.figma_adapter import FigmaAdapter

            async with self.get_db_session() as db:
                result = await db.execute(
                    select(ServiceConnection).where(
                        ServiceConnection.project_id == project_id,
                        ServiceConnection.service_type == "figma",
                        ServiceConnection.enabled == True,
                    )
                )
                conn = result.scalars().first()
                if not conn:
                    return {}

                figma = FigmaAdapter(conn.api_token)
                file_data = await figma.get_file(file_key)
                components = await figma.get_file_components(file_key)

                return {
                    "file_key": file_key,
                    "name": file_data.get("name", ""),
                    "last_modified": file_data.get("lastModified", ""),
                    "components": components.get("meta", {}).get("components", {}),
                }
        except Exception:
            logger.exception("Failed to fetch Figma design data")
            return {}

    async def _get_related_tickets(self, project_id: int | None) -> dict:
        if not project_id:
            return {}

        try:
            from sqlalchemy import select
            from app.models.task import Task

            async with self.get_db_session() as db:
                result = await db.execute(
                    select(Task).where(
                        Task.project_id == project_id,
                        Task.status.in_(["todo", "in_progress"]),
                    ).limit(10)
                )
                tasks = result.scalars().all()
                return {
                    "tickets": [
                        {
                            "key": t.jira_issue_key or f"TASK-{t.id}",
                            "title": t.title,
                            "description": t.description,
                            "status": t.status,
                        }
                        for t in tasks
                    ]
                }
        except Exception:
            logger.exception("Failed to get related tickets")
            return {}

    async def _sync_gitlab_issues(
        self, project_id: int | None, file_key: str, impl_notes: dict
    ) -> None:
        if not project_id:
            return

        steps = impl_notes.get("implementation_steps", [])
        if not steps:
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

                description = f"**From Figma:** {file_key}\n\n"
                description += "## Implementation Steps\n"
                for i, step in enumerate(steps, 1):
                    description += f"{i}. {step}\n"

                specs = impl_notes.get("component_specs", [])
                if specs:
                    description += "\n## Component Specs\n"
                    for spec in specs[:5]:
                        description += f"\n### {spec.get('name', 'Component')}\n"
                        if spec.get("css_changes"):
                            description += f"CSS: {spec['css_changes']}\n"
                        if spec.get("props"):
                            description += f"Props: {spec['props']}\n"

                await gitlab.create_issue(
                    gl_project_id,
                    title=f"Design Implementation: {file_key}",
                    description=description,
                    labels=["design-sync", "auto-generated"],
                )
        except Exception:
            logger.exception("Failed to create GitLab issues from design sync")
