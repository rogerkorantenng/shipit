"""Agent 4: Security & Compliance - AI-based SAST, dependency checks, compliance."""

import logging

from app.agents.base import BaseAgent
from app.agents.event_bus import Event, EventType
from app.services import agent_ai_service

logger = logging.getLogger(__name__)


class SecurityComplianceAgent(BaseAgent):

    @property
    def name(self) -> str:
        return "security_compliance"

    @property
    def description(self) -> str:
        return (
            "Performs AI-based security scanning (SAST), dependency vulnerability "
            "checks, and generates compliance reports for code changes"
        )

    @property
    def subscribed_events(self) -> list[EventType]:
        return [EventType.PR_OPENED, EventType.CODE_PUSHED]

    async def handle_event(self, event: Event) -> None:
        data = event.data
        mr_iid = data.get("mr_iid")
        project_id = event.project_id

        logger.info(f"Security scan for MR {mr_iid} in project {project_id}")

        # Fetch diff from GitLab
        diff_content, file_paths = await self._get_diff(project_id, mr_iid, data)

        if not diff_content:
            logger.info("No diff content available, skipping scan")
            return

        # Run AI security scan
        scan_result = await agent_ai_service.security_scan(diff_content, file_paths)

        vulnerabilities = scan_result.get("vulnerabilities", [])
        critical_vulns = [v for v in vulnerabilities if v.get("severity") == "critical"]
        high_vulns = [v for v in vulnerabilities if v.get("severity") == "high"]

        # Post findings as MR comments
        if mr_iid and vulnerabilities:
            await self._post_findings(project_id, mr_iid, scan_result)

        # Block merge if critical vulnerabilities - post blocking comment and add label
        if critical_vulns and mr_iid:
            await self._block_merge(project_id, mr_iid, critical_vulns)
            await self.publish(Event(
                type=EventType.MERGE_BLOCKED,
                data={
                    "mr_iid": mr_iid,
                    "reason": f"{len(critical_vulns)} critical vulnerabilities found",
                    "vulnerabilities": critical_vulns,
                },
                source_agent=self.name,
                project_id=project_id,
                correlation_id=event.correlation_id,
            ))

        if vulnerabilities:
            await self.publish(Event(
                type=EventType.VULNERABILITY_FOUND,
                data={
                    "mr_iid": mr_iid,
                    "count": len(vulnerabilities),
                    "critical": len(critical_vulns),
                    "high": len(high_vulns),
                    "vulnerabilities": vulnerabilities,
                },
                source_agent=self.name,
                project_id=project_id,
                correlation_id=event.correlation_id,
            ))

        # Publish scan complete
        await self.publish(Event(
            type=EventType.SECURITY_SCAN_COMPLETE,
            data={
                "mr_iid": mr_iid,
                "passed": scan_result.get("passed", True),
                "overall_risk": scan_result.get("overall_risk", "low"),
                "vulnerability_count": len(vulnerabilities),
                "summary": scan_result.get("summary", ""),
            },
            source_agent=self.name,
            project_id=project_id,
            correlation_id=event.correlation_id,
        ))

        # Generate compliance report
        await self.publish(Event(
            type=EventType.COMPLIANCE_REPORT_GENERATED,
            data={
                "mr_iid": mr_iid,
                "scan_result": scan_result,
            },
            source_agent=self.name,
            project_id=project_id,
            correlation_id=event.correlation_id,
        ))

    async def _block_merge(
        self, project_id: int | None, mr_iid: int, critical_vulns: list[dict]
    ) -> None:
        """Block merge by posting an unresolved discussion thread on GitLab MR."""
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

                # Post a blocking comment (unresolved discussion blocks merge in GitLab
                # when "All discussions must be resolved" is enabled)
                block_msg = (
                    "## MERGE BLOCKED - Critical Security Vulnerabilities\n\n"
                    "This merge request has been blocked due to critical security issues "
                    "that must be resolved before merging.\n\n"
                )
                for v in critical_vulns[:5]:
                    block_msg += (
                        f"- **{v.get('type', 'Unknown')}** in `{v.get('file', '?')}`: "
                        f"{v.get('description', 'No description')}\n"
                        f"  Recommendation: {v.get('recommendation', 'N/A')}\n\n"
                    )
                block_msg += (
                    "\nResolve these issues and push a new commit to re-trigger the security scan. "
                    "Resolve this discussion thread once all issues are fixed."
                )

                # Use the discussions API to create an unresolved thread
                import httpx
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        f"{gitlab.api_url}/projects/{gl_project_id}/merge_requests/{mr_iid}/discussions",
                        headers=gitlab._headers,
                        json={"body": block_msg},
                        timeout=15.0,
                    )
                    resp.raise_for_status()
                    logger.info(f"Created blocking discussion on MR {mr_iid}")

                # Also notify Slack about the block
                await self.publish(Event(
                    type=EventType.SLACK_NOTIFICATION,
                    data={
                        "message": (
                            f"*MERGE BLOCKED* - MR !{mr_iid}\n"
                            f"{len(critical_vulns)} critical vulnerabilities found. "
                            f"Merge is blocked until resolved."
                        ),
                    },
                    source_agent=self.name,
                    project_id=project_id,
                ))
        except Exception:
            logger.exception(f"Failed to block merge for MR {mr_iid}")

    async def _get_diff(
        self, project_id: int | None, mr_iid: int | None, data: dict
    ) -> tuple[str, list[str]]:
        # If diff is already in event data
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

    async def _post_findings(
        self, project_id: int | None, mr_iid: int, scan_result: dict
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

                vulns = scan_result.get("vulnerabilities", [])
                comment = "## Security Scan Results\n\n"
                comment += f"**Overall Risk:** {scan_result.get('overall_risk', 'unknown')}\n"
                comment += f"**Status:** {'PASSED' if scan_result.get('passed') else 'FAILED'}\n\n"

                if vulns:
                    comment += "### Vulnerabilities Found\n\n"
                    for v in vulns[:10]:
                        emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(
                            v.get("severity", ""), "⚪"
                        )
                        comment += (
                            f"- {emoji} **{v.get('severity', '').upper()}** - "
                            f"{v.get('type', 'Unknown')}: {v.get('description', '')}\n"
                            f"  - File: `{v.get('file', '?')}`\n"
                            f"  - Fix: {v.get('recommendation', 'N/A')}\n\n"
                        )
                else:
                    comment += "No vulnerabilities detected.\n"

                # GitLab API limit is ~1MB, truncate to safe limit
                MAX_COMMENT_LEN = 60000
                if len(comment) > MAX_COMMENT_LEN:
                    comment = comment[:MAX_COMMENT_LEN] + "\n\n*...truncated*"

                await gitlab.add_mr_comment(gl_project_id, mr_iid, comment)
        except Exception:
            logger.exception("Failed to post security findings")
