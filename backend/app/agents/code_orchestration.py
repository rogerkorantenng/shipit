"""Agent 3: Code Orchestration - Creates branches, boilerplate, PR templates."""

import logging
import re

from app.agents.base import BaseAgent
from app.agents.event_bus import Event, EventType
from app.services import agent_ai_service

logger = logging.getLogger(__name__)


def _slugify(text: str, max_len: int = 40) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len].rstrip("-")


class CodeOrchestrationAgent(BaseAgent):

    @property
    def name(self) -> str:
        return "code_orchestration"

    @property
    def description(self) -> str:
        return (
            "Creates feature branches, generates boilerplate code, "
            "PR templates, and auto-assigns reviewers"
        )

    @property
    def subscribed_events(self) -> list[EventType]:
        return [
            EventType.GITLAB_ISSUE_ASSIGNED,
            EventType.REQUIREMENTS_ANALYZED,
            EventType.IMPLEMENTATION_NOTES_GENERATED,
        ]

    async def handle_event(self, event: Event) -> None:
        if event.type == EventType.REQUIREMENTS_ANALYZED:
            await self._handle_requirements(event)
        elif event.type == EventType.GITLAB_ISSUE_ASSIGNED:
            await self._handle_issue_assigned(event)
        elif event.type == EventType.IMPLEMENTATION_NOTES_GENERATED:
            await self._handle_impl_notes(event)

    async def _handle_requirements(self, event: Event) -> None:
        data = event.data
        ticket_key = data.get("ticket_key", "unknown")
        analysis = data.get("analysis", {})

        branch_name = f"feature/{ticket_key}-{_slugify(analysis.get('summary', 'task'))}"
        logger.info(f"Creating branch: {branch_name}")

        gitlab = await self._get_gitlab(event.project_id)
        gl_project_id = await self._get_gitlab_project_id(event.project_id)

        # Publish branch created event
        branch_created = False
        if gitlab and gl_project_id:
            try:
                await gitlab.create_branch(gl_project_id, branch_name)
                branch_created = True
            except Exception:
                logger.exception(f"Failed to create branch {branch_name}")

        # Always publish branch event (even without GitLab - shows what agent would do)
        await self.publish(Event(
            type=EventType.BRANCH_CREATED,
            data={"branch": branch_name, "ticket_key": ticket_key},
            source_agent=self.name,
            project_id=event.project_id,
            correlation_id=event.correlation_id,
        ))

        # Generate boilerplate via AI
        boilerplate = await agent_ai_service.generate_boilerplate(analysis, branch_name)
        if boilerplate.get("files"):
            if gitlab and gl_project_id and branch_created:
                for file_info in boilerplate["files"][:10]:
                    try:
                        await gitlab.create_file(
                            gl_project_id,
                            file_info["path"],
                            file_info.get("content", ""),
                            branch_name,
                            f"scaffold: {file_info.get('description', file_info['path'])}",
                        )
                    except Exception:
                        logger.warning(f"Failed to create file: {file_info.get('path')}")

            await self.publish(Event(
                type=EventType.BOILERPLATE_GENERATED,
                data={
                    "branch": branch_name,
                    "files": [f["path"] for f in boilerplate["files"]],
                },
                source_agent=self.name,
                project_id=event.project_id,
                correlation_id=event.correlation_id,
            ))

        # Create MR or publish template event
        mr_iid = None
        if gitlab and gl_project_id and branch_created:
            try:
                members = await gitlab.list_project_members(gl_project_id)
                reviewer_ids = [m["id"] for m in members[:2]] if members else None

                mr = await gitlab.create_merge_request(
                    gl_project_id,
                    source_branch=branch_name,
                    title=f"feat: {ticket_key} - {analysis.get('summary', 'Implementation')}",
                    description=boilerplate.get("pr_description", "Auto-generated PR"),
                    reviewer_ids=reviewer_ids,
                )
                mr_iid = mr.get("iid")
            except Exception:
                logger.exception("Failed to create merge request")

        await self.publish(Event(
            type=EventType.PR_TEMPLATE_CREATED,
            data={
                "mr_iid": mr_iid or 0,
                "branch": branch_name,
                "ticket_key": ticket_key,
            },
            source_agent=self.name,
            project_id=event.project_id,
            correlation_id=event.correlation_id,
        ))

    async def _handle_issue_assigned(self, event: Event) -> None:
        data = event.data
        issue_id = data.get("issue_id", "")
        title = data.get("title", "task")
        branch_name = f"feature/{issue_id}-{_slugify(title)}"

        gitlab = await self._get_gitlab(event.project_id)
        gl_project_id = await self._get_gitlab_project_id(event.project_id)

        if gitlab and gl_project_id:
            try:
                await gitlab.create_branch(gl_project_id, branch_name)
            except Exception:
                logger.exception(f"Failed to create branch for issue {issue_id}")

        # Always publish event (shows what agent would do)
        await self.publish(Event(
            type=EventType.BRANCH_CREATED,
            data={"branch": branch_name, "issue_id": issue_id},
            source_agent=self.name,
            project_id=event.project_id,
            correlation_id=event.correlation_id,
        ))

        # If analysis data is available, also generate boilerplate
        analysis = data.get("analysis", {})
        if analysis:
            boilerplate = await agent_ai_service.generate_boilerplate(analysis, branch_name)
            if boilerplate.get("files"):
                await self.publish(Event(
                    type=EventType.BOILERPLATE_GENERATED,
                    data={
                        "branch": branch_name,
                        "files": [f["path"] for f in boilerplate["files"]],
                    },
                    source_agent=self.name,
                    project_id=event.project_id,
                    correlation_id=event.correlation_id,
                ))

    async def _handle_impl_notes(self, event: Event) -> None:
        # Design sync generated implementation notes - ensure branch exists
        data = event.data
        ticket_key = data.get("ticket_key", "design")
        branch_name = f"feature/{ticket_key}-{_slugify('design-implementation')}"

        gitlab = await self._get_gitlab(event.project_id)
        gl_project_id = await self._get_gitlab_project_id(event.project_id)

        if gitlab and gl_project_id:
            try:
                await gitlab.create_branch(gl_project_id, branch_name)
            except Exception as e:
                error_msg = str(e)
                if "already exists" in error_msg.lower() or "Branch already exists" in error_msg:
                    logger.info(f"Branch {branch_name} already exists, proceeding")
                else:
                    logger.exception(f"Failed to create branch {branch_name}")
                    return

            await self.publish(Event(
                type=EventType.BRANCH_CREATED,
                data={"branch": branch_name, "source": "design_sync"},
                source_agent=self.name,
                project_id=event.project_id,
                correlation_id=event.correlation_id,
            ))

    async def _get_gitlab(self, project_id: int | None):
        if not project_id:
            return None
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
                if conn:
                    return GitLabAdapter(conn.base_url or "https://gitlab.com", conn.api_token)
        except Exception:
            logger.exception("Failed to get GitLab adapter")
        return None

    async def _get_gitlab_project_id(self, project_id: int | None) -> int | None:
        if not project_id:
            return None
        try:
            from sqlalchemy import select
            from app.models.service_connection import ServiceConnection

            async with self.get_db_session() as db:
                result = await db.execute(
                    select(ServiceConnection).where(
                        ServiceConnection.project_id == project_id,
                        ServiceConnection.service_type == "gitlab",
                        ServiceConnection.enabled == True,
                    )
                )
                conn = result.scalars().first()
                if conn:
                    return (conn.config or {}).get("project_id")
        except Exception:
            logger.exception("Failed to get GitLab project ID")
        return None
