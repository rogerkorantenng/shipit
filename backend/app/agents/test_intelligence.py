"""Agent 5: Test Intelligence - Generates test suggestions, coverage reports."""

import logging

from app.agents.base import BaseAgent
from app.agents.event_bus import Event, EventType
from app.services import agent_ai_service

logger = logging.getLogger(__name__)


class TestIntelligenceAgent(BaseAgent):

    @property
    def name(self) -> str:
        return "test_intelligence"

    @property
    def description(self) -> str:
        return (
            "Analyzes code changes to generate test suggestions, identify "
            "coverage gaps, and suggest edge cases"
        )

    @property
    def subscribed_events(self) -> list[EventType]:
        return [
            EventType.PR_OPENED,
            EventType.CODE_PUSHED,
            EventType.SECURITY_SCAN_COMPLETE,
        ]

    async def handle_event(self, event: Event) -> None:
        data = event.data
        mr_iid = data.get("mr_iid")
        project_id = event.project_id

        logger.info(f"Test analysis for MR {mr_iid} in project {project_id}")

        # Get diff content
        diff_content, file_paths = await self._get_diff(project_id, mr_iid, data)

        if not diff_content:
            logger.info("No diff available for test analysis")
            return

        # Generate test suggestions via AI
        suggestions = await agent_ai_service.generate_test_suggestions(diff_content, file_paths)

        unit_tests = suggestions.get("unit_tests", [])
        integration_tests = suggestions.get("integration_tests", [])
        edge_cases = suggestions.get("edge_cases", [])

        # Post suggestions as MR comment
        if mr_iid:
            await self._post_suggestions(project_id, mr_iid, suggestions)

        # Publish test suggestions
        await self.publish(Event(
            type=EventType.TEST_SUGGESTIONS_GENERATED,
            data={
                "mr_iid": mr_iid,
                "unit_tests_count": len(unit_tests),
                "integration_tests_count": len(integration_tests),
                "edge_cases": edge_cases,
                "suggestions": suggestions,
            },
            source_agent=self.name,
            project_id=project_id,
            correlation_id=event.correlation_id,
        ))

        # Create test report
        await self.publish(Event(
            type=EventType.TEST_REPORT_CREATED,
            data={
                "mr_iid": mr_iid,
                "total_suggested": len(unit_tests) + len(integration_tests),
                "coverage_gaps": suggestions.get("coverage_gaps", []),
                "priority_order": suggestions.get("priority_order", []),
            },
            source_agent=self.name,
            project_id=project_id,
            correlation_id=event.correlation_id,
        ))

    async def _get_diff(
        self, project_id: int | None, mr_iid: int | None, data: dict
    ) -> tuple[str, list[str]]:
        if data.get("diff"):
            return data["diff"], data.get("files", [])

        if not project_id or not mr_iid:
            return "", []

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
                    return "", []

                gitlab = GitLabAdapter(conn.base_url or "https://gitlab.com", conn.api_token)
                gl_project_id = (conn.config or {}).get("project_id")
                if not gl_project_id:
                    return "", []

                diffs = await gitlab.get_mr_diff(gl_project_id, mr_iid)
                file_paths = [d.get("new_path", "") for d in diffs]
                diff_text = "\n".join(d.get("diff", "") for d in diffs)
                return diff_text, file_paths
        except Exception:
            logger.exception("Failed to fetch diff from GitLab")
            return "", []

    async def _post_suggestions(
        self, project_id: int | None, mr_iid: int, suggestions: dict
    ) -> None:
        if not project_id:
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

                comment = "## Test Suggestions\n\n"

                unit_tests = suggestions.get("unit_tests", [])
                if unit_tests:
                    comment += "### Unit Tests\n"
                    for t in unit_tests[:5]:
                        comment += f"- **{t.get('name', 'Test')}**: {t.get('description', '')}\n"
                        if t.get("code_hint"):
                            comment += f"  ```\n  {t['code_hint']}\n  ```\n"
                    comment += "\n"

                integration_tests = suggestions.get("integration_tests", [])
                if integration_tests:
                    comment += "### Integration Tests\n"
                    for t in integration_tests[:3]:
                        comment += f"- **{t.get('name', 'Test')}**: {t.get('description', '')}\n"
                    comment += "\n"

                edge_cases = suggestions.get("edge_cases", [])
                if edge_cases:
                    comment += "### Edge Cases to Consider\n"
                    for ec in edge_cases[:5]:
                        comment += f"- {ec}\n"
                    comment += "\n"

                gaps = suggestions.get("coverage_gaps", [])
                if gaps:
                    comment += "### Coverage Gaps\n"
                    for g in gaps[:5]:
                        comment += f"- {g}\n"

                # GitLab API limit is ~1MB, truncate to safe limit
                MAX_COMMENT_LEN = 60000
                if len(comment) > MAX_COMMENT_LEN:
                    comment = comment[:MAX_COMMENT_LEN] + "\n\n*...truncated*"

                await gitlab.add_mr_comment(gl_project_id, mr_iid, comment)
        except Exception:
            logger.exception("Failed to post test suggestions")
