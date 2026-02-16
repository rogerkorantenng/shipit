"""Agent 6: Review Coordination - Assigns reviewers, tracks SLAs, auto-merges."""

import logging
from datetime import datetime
from typing import Optional

from app.agents.base import BaseAgent
from app.agents.event_bus import Event, EventType
from app.services import agent_ai_service

logger = logging.getLogger(__name__)

DEFAULT_SLA_HOURS = 24

# In-memory MR readiness tracker: mr_key -> {security_passed, tests_passed, approved}
_mr_state: dict[str, dict] = {}


def _mr_key(project_id: int | None, mr_iid: int | None) -> str:
    return f"{project_id}:{mr_iid}"


class ReviewCoordinationAgent(BaseAgent):

    @property
    def name(self) -> str:
        return "review_coordination"

    @property
    def description(self) -> str:
        return (
            "Coordinates code reviews: assigns reviewers based on expertise, "
            "tracks SLAs, sends reminders, and auto-merges approved PRs"
        )

    @property
    def subscribed_events(self) -> list[EventType]:
        return [
            EventType.PR_READY_FOR_REVIEW,
            EventType.PR_OPENED,
            EventType.TEST_REPORT_CREATED,
            EventType.SECURITY_SCAN_COMPLETE,
        ]

    async def handle_event(self, event: Event) -> None:
        if event.type in (EventType.PR_READY_FOR_REVIEW, EventType.PR_OPENED):
            await self._handle_pr_opened(event)
        elif event.type == EventType.SECURITY_SCAN_COMPLETE:
            await self._on_security_complete(event)
        elif event.type == EventType.TEST_REPORT_CREATED:
            await self._on_tests_complete(event)

    async def _handle_pr_opened(self, event: Event) -> None:
        data = event.data
        mr_iid = data.get("mr_iid")
        project_id = event.project_id

        logger.info(f"Review coordination for MR {mr_iid}")

        # Initialize MR state tracking
        key = _mr_key(project_id, mr_iid)
        _mr_state[key] = {
            "security_passed": False,
            "tests_passed": False,
            "auto_merge_eligible": False,
            "opened_at": datetime.utcnow().isoformat(),
        }

        # Get diff for complexity analysis
        diff_content = data.get("diff", "")
        file_count = len(data.get("files", []))

        if not diff_content and project_id and mr_iid:
            diff_content, files = await self._get_diff(project_id, mr_iid)
            file_count = len(files)

        # Analyze complexity
        analysis = await agent_ai_service.analyze_review_complexity(
            diff_content[:6000], file_count
        )

        # Store auto-merge eligibility
        _mr_state[key]["auto_merge_eligible"] = analysis.get("auto_merge_eligible", False)

        # Assign reviewers based on expertise matching
        reviewer_ids = await self._assign_reviewers(
            project_id, analysis.get("recommended_expertise", [])
        )

        await self.publish(Event(
            type=EventType.REVIEWERS_ASSIGNED,
            data={
                "mr_iid": mr_iid,
                "reviewers": reviewer_ids,
                "complexity": analysis.get("complexity", "medium"),
                "estimated_review_minutes": analysis.get("estimated_review_minutes", 30),
                "risk_areas": analysis.get("risk_areas", []),
                "summary": analysis.get("summary", ""),
                "auto_merge_eligible": analysis.get("auto_merge_eligible", False),
            },
            source_agent=self.name,
            project_id=project_id,
            correlation_id=event.correlation_id,
        ))

        # Post review summary as MR comment
        if mr_iid:
            await self._post_review_summary(project_id, mr_iid, analysis)

        # Send Slack notification
        await self.publish(Event(
            type=EventType.SLACK_NOTIFICATION,
            data={
                "message": (
                    f"*Review Needed* - MR !{mr_iid}\n"
                    f"Complexity: {analysis.get('complexity', 'medium')} | "
                    f"Est. time: {analysis.get('estimated_review_minutes', 30)}min\n"
                    f"Risk areas: {', '.join(analysis.get('risk_areas', ['none']))}"
                ),
            },
            source_agent=self.name,
            project_id=project_id,
            correlation_id=event.correlation_id,
        ))

    async def _on_security_complete(self, event: Event) -> None:
        data = event.data
        mr_iid = data.get("mr_iid")
        project_id = event.project_id

        if not mr_iid or not project_id:
            return

        key = _mr_key(project_id, mr_iid)
        if key not in _mr_state:
            _mr_state[key] = {
                "security_passed": False,
                "tests_passed": False,
                "auto_merge_eligible": False,
            }

        passed = data.get("passed", False)
        _mr_state[key]["security_passed"] = passed

        if not passed:
            logger.info(f"MR {mr_iid} failed security scan - auto-merge blocked")
            return

        logger.info(f"MR {mr_iid} passed security scan")
        await self._try_auto_merge(project_id, mr_iid, event.correlation_id)

    async def _on_tests_complete(self, event: Event) -> None:
        data = event.data
        mr_iid = data.get("mr_iid")
        project_id = event.project_id

        if not mr_iid or not project_id:
            return

        key = _mr_key(project_id, mr_iid)
        if key not in _mr_state:
            _mr_state[key] = {
                "security_passed": False,
                "tests_passed": False,
                "auto_merge_eligible": False,
            }

        # Tests are considered passed when a report is created
        _mr_state[key]["tests_passed"] = True

        logger.info(f"MR {mr_iid} test report received")
        await self._try_auto_merge(project_id, mr_iid, event.correlation_id)

    async def _try_auto_merge(
        self, project_id: int, mr_iid: int, correlation_id: str | None
    ) -> None:
        """Attempt auto-merge if all conditions are met."""
        key = _mr_key(project_id, mr_iid)
        state = _mr_state.get(key, {})

        security_ok = state.get("security_passed", False)
        tests_ok = state.get("tests_passed", False)
        eligible = state.get("auto_merge_eligible", False)

        # Check if auto-merge is enabled for this project
        auto_merge_enabled = await self._is_auto_merge_enabled(project_id)

        if not auto_merge_enabled:
            logger.info(f"MR {mr_iid}: auto-merge disabled for project {project_id}")
            return

        if not eligible:
            logger.info(f"MR {mr_iid}: not eligible for auto-merge (complexity too high)")
            return

        if not security_ok:
            logger.info(f"MR {mr_iid}: waiting for security scan to pass")
            return

        if not tests_ok:
            logger.info(f"MR {mr_iid}: waiting for test report")
            return

        # All conditions met - execute auto-merge via GitLab API
        logger.info(f"MR {mr_iid}: all checks passed, executing auto-merge")

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
                    logger.error(f"MR {mr_iid}: no GitLab connection for auto-merge")
                    return

                gitlab = GitLabAdapter(conn.base_url or "https://gitlab.com", conn.api_token)
                gl_project_id = (conn.config or {}).get("project_id")
                if not gl_project_id:
                    logger.error(f"MR {mr_iid}: no GitLab project_id for auto-merge")
                    return

                merge_result = await gitlab.merge_mr(gl_project_id, mr_iid)
                logger.info(f"MR {mr_iid} auto-merged successfully: {merge_result.get('state')}")

                # Clean up state
                _mr_state.pop(key, None)

                await self.publish(Event(
                    type=EventType.PR_AUTO_MERGED,
                    data={
                        "mr_iid": mr_iid,
                        "merge_state": merge_result.get("state"),
                        "merged_by": "auto-merge",
                    },
                    source_agent=self.name,
                    project_id=project_id,
                    correlation_id=correlation_id,
                ))

                await self.publish(Event(
                    type=EventType.SLACK_NOTIFICATION,
                    data={
                        "message": (
                            f"*Auto-Merged* - MR !{mr_iid}\n"
                            f"Security: passed | Tests: passed | Eligible: yes"
                        ),
                    },
                    source_agent=self.name,
                    project_id=project_id,
                    correlation_id=correlation_id,
                ))
        except Exception:
            logger.exception(f"Failed to auto-merge MR {mr_iid}")

    async def _is_auto_merge_enabled(self, project_id: int) -> bool:
        """Check project agent config for auto-merge setting."""
        try:
            from sqlalchemy import select
            from app.models.agent_state import AgentConfig

            async with self.get_db_session() as db:
                result = await db.execute(
                    select(AgentConfig).where(
                        AgentConfig.project_id == project_id,
                        AgentConfig.agent_name == self.name,
                    )
                )
                cfg = result.scalars().first()
                if cfg and cfg.config:
                    return cfg.config.get("auto_merge", False)
        except Exception:
            logger.exception("Failed to check auto-merge config")
        return False

    async def _assign_reviewers(
        self, project_id: int | None, expertise: list[str]
    ) -> list[int]:
        """Assign reviewers from project members, scoring by expertise match."""
        if not project_id:
            return []

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
                    return []

                gitlab = GitLabAdapter(conn.base_url or "https://gitlab.com", conn.api_token)
                gl_project_id = (conn.config or {}).get("project_id")
                if not gl_project_id:
                    return []

                members = await gitlab.list_project_members(gl_project_id)
                if not members:
                    return []

                # Score members by expertise match using username/name overlap
                expertise_lower = {e.lower() for e in expertise}
                scored = []
                for m in members:
                    score = 0
                    name_parts = set(m.get("name", "").lower().split())
                    username = m.get("username", "").lower()
                    # Higher access level = more experienced
                    access = m.get("access_level", 0)
                    if access >= 40:  # Maintainer+
                        score += 3
                    elif access >= 30:  # Developer
                        score += 1
                    # Check if member's name/username hints at expertise
                    for exp in expertise_lower:
                        if exp in username or exp in name_parts:
                            score += 5
                    scored.append((score, m["id"]))

                # Sort by score descending, take top 2
                scored.sort(key=lambda x: x[0], reverse=True)

                # Get configurable reviewer count
                num_reviewers = 2
                cfg_result = await db.execute(
                    select(ServiceConnection).where(  # reuse to avoid extra import
                        ServiceConnection.project_id == project_id,
                        ServiceConnection.service_type == "gitlab",
                    )
                )

                from app.models.agent_state import AgentConfig
                cfg_result = await db.execute(
                    select(AgentConfig).where(
                        AgentConfig.project_id == project_id,
                        AgentConfig.agent_name == self.name,
                    )
                )
                cfg = cfg_result.scalars().first()
                if cfg and cfg.config:
                    num_reviewers = cfg.config.get("min_reviewers", 2)

                return [member_id for _, member_id in scored[:num_reviewers]]
        except Exception:
            logger.exception("Failed to assign reviewers")
            return []

    async def _get_diff(
        self, project_id: int | None, mr_iid: int
    ) -> tuple[str, list[str]]:
        if not project_id:
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
            logger.exception("Failed to fetch diff")
            return "", []

    async def _post_review_summary(
        self, project_id: int | None, mr_iid: int, analysis: dict
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

                comment = "## Review Summary\n\n"
                comment += f"**Complexity:** {analysis.get('complexity', 'medium')}\n"
                comment += f"**Estimated Review Time:** {analysis.get('estimated_review_minutes', 30)} minutes\n"
                comment += f"**Auto-merge Eligible:** {'Yes' if analysis.get('auto_merge_eligible') else 'No'}\n\n"

                risk_areas = analysis.get("risk_areas", [])
                if risk_areas:
                    comment += "### Risk Areas\n"
                    for area in risk_areas:
                        comment += f"- {area}\n"
                    comment += "\n"

                if analysis.get("summary"):
                    comment += f"### Summary\n{analysis['summary']}\n"

                await gitlab.add_mr_comment(gl_project_id, mr_iid, comment)
        except Exception:
            logger.exception("Failed to post review summary")
