"""Agent 7: Deployment Orchestrator - Manages deployments, release notes, rollbacks."""

import logging

from app.agents.base import BaseAgent
from app.agents.event_bus import Event, EventType
from app.services import agent_ai_service

logger = logging.getLogger(__name__)


class DeploymentOrchestratorAgent(BaseAgent):

    @property
    def name(self) -> str:
        return "deployment_orchestrator"

    @property
    def description(self) -> str:
        return (
            "Orchestrates deployments: validates readiness, triggers CI/CD, "
            "generates release notes, monitors post-deploy, and handles rollbacks"
        )

    @property
    def subscribed_events(self) -> list[EventType]:
        return [
            EventType.MERGE_TO_MAIN,
            EventType.PR_AUTO_MERGED,
            EventType.PR_APPROVED,
        ]

    async def handle_event(self, event: Event) -> None:
        data = event.data
        project_id = event.project_id

        logger.info(f"Deployment triggered for project {project_id}")

        # Validate readiness
        ready, issues = await self._validate_readiness(project_id, data)

        if not ready:
            logger.warning(f"Deployment blocked: {issues}")
            await self.publish(Event(
                type=EventType.DEPLOY_FAILED,
                data={
                    "reason": "Readiness check failed",
                    "issues": issues,
                },
                source_agent=self.name,
                project_id=project_id,
                correlation_id=event.correlation_id,
            ))
            return

        # Start deployment
        await self.publish(Event(
            type=EventType.DEPLOY_STARTED,
            data={
                "ref": data.get("ref", "main"),
                "trigger_event": event.type.value,
            },
            source_agent=self.name,
            project_id=project_id,
            correlation_id=event.correlation_id,
        ))

        # Trigger CI/CD pipeline
        pipeline_result = await self._trigger_pipeline(project_id, data.get("ref", "main"))

        # Generate release notes (try GitLab, fall back to inline commit data)
        release_notes = await self._generate_release_notes(project_id, data)

        if release_notes:
            await self.publish(Event(
                type=EventType.RELEASE_NOTES_GENERATED,
                data=release_notes,
                source_agent=self.name,
                project_id=project_id,
                correlation_id=event.correlation_id,
            ))

        # Monitor post-deploy (check monitoring)
        health = await self._check_post_deploy_health(project_id)

        if health.get("healthy", True):
            await self.publish(Event(
                type=EventType.DEPLOY_COMPLETE,
                data={
                    "pipeline": pipeline_result,
                    "release_notes": release_notes,
                    "health_check": health,
                },
                source_agent=self.name,
                project_id=project_id,
                correlation_id=event.correlation_id,
            ))

            # Slack notification
            await self.publish(Event(
                type=EventType.SLACK_NOTIFICATION,
                data={
                    "message": (
                        f"*Deployment Complete* :rocket:\n"
                        f"Ref: `{data.get('ref', 'main')}`\n"
                        f"Health: All checks passed"
                    ),
                },
                source_agent=self.name,
                project_id=project_id,
                correlation_id=event.correlation_id,
            ))
        else:
            # Trigger rollback
            await self._rollback(project_id, health)
            await self.publish(Event(
                type=EventType.ROLLBACK_TRIGGERED,
                data={
                    "reason": health.get("reason", "Health check failed"),
                    "errors": health.get("errors", []),
                },
                source_agent=self.name,
                project_id=project_id,
                correlation_id=event.correlation_id,
            ))

            await self.publish(Event(
                type=EventType.SLACK_NOTIFICATION,
                data={
                    "message": (
                        f"*Deployment Rolled Back* :warning:\n"
                        f"Reason: {health.get('reason', 'Health check failure')}"
                    ),
                },
                source_agent=self.name,
                project_id=project_id,
                correlation_id=event.correlation_id,
            ))

    async def _validate_readiness(
        self, project_id: int | None, data: dict
    ) -> tuple[bool, list[str]]:
        issues = []

        # Check if Jira tickets are in correct state
        if project_id:
            try:
                from sqlalchemy import select, func
                from app.models.task import Task

                async with self.get_db_session() as db:
                    result = await db.execute(
                        select(func.count()).select_from(Task).where(
                            Task.project_id == project_id,
                            Task.status == "in_progress",
                        )
                    )
                    in_progress = result.scalar() or 0
                    if in_progress > 0:
                        issues.append(f"{in_progress} tasks still in progress")
            except Exception:
                logger.exception("Failed to check task readiness")

        return len(issues) == 0, issues

    async def _trigger_pipeline(
        self, project_id: int | None, ref: str
    ) -> dict:
        if not project_id:
            return {"status": "skipped", "reason": "no project_id"}

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
                    return {"status": "skipped", "reason": "no gitlab connection"}

                gitlab = GitLabAdapter(conn.base_url or "https://gitlab.com", conn.api_token)
                gl_project_id = (conn.config or {}).get("project_id")
                if not gl_project_id:
                    return {"status": "skipped", "reason": "no gitlab project_id"}

                pipeline = await gitlab.trigger_pipeline(gl_project_id, ref=ref)
                return {"status": "triggered", "pipeline_id": pipeline.get("id")}
        except Exception:
            logger.exception("Failed to trigger pipeline")
            return {"status": "error"}

    async def _generate_release_notes(self, project_id: int | None, data: dict | None = None) -> dict:
        if not project_id:
            return {}

        commit_data = []

        # Try GitLab first
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
                    gitlab = GitLabAdapter(conn.base_url or "https://gitlab.com", conn.api_token)
                    gl_project_id = (conn.config or {}).get("project_id")
                    if gl_project_id:
                        commits = await gitlab.get_commits(gl_project_id, limit=20)
                        commit_data = [
                            {"message": c.get("message", ""), "author": c.get("author_name", "")}
                            for c in commits
                        ]
        except Exception:
            logger.exception("Failed to fetch commits from GitLab")

        # Fall back to inline commit messages from trigger data
        if not commit_data and data:
            commit_msgs = data.get("commit_messages", [])
            if commit_msgs:
                commit_data = [{"message": m, "author": "team"} for m in commit_msgs]

        if not commit_data:
            return {}

        try:
            return await agent_ai_service.generate_release_notes(commit_data, [])
        except Exception:
            logger.exception("Failed to generate release notes")
            return {}

    async def _check_post_deploy_health(self, project_id: int | None) -> dict:
        if not project_id:
            logger.warning("No project_id for health check - treating as unhealthy")
            return {"healthy": False, "errors": ["No project_id"], "reason": "No project_id"}

        errors = []
        checks_run = 0

        # Check Sentry for new errors
        try:
            from sqlalchemy import select
            from app.models.service_connection import ServiceConnection
            from app.models.agent_state import AgentConfig
            from app.adapters.monitoring_adapter import SentryAdapter

            async with self.get_db_session() as db:
                result = await db.execute(
                    select(ServiceConnection).where(
                        ServiceConnection.project_id == project_id,
                        ServiceConnection.service_type == "sentry",
                        ServiceConnection.enabled == True,
                    )
                )
                conn = result.scalars().first()
                if conn:
                    checks_run += 1
                    config = conn.config or {}
                    sentry = SentryAdapter(conn.api_token, conn.base_url or "https://sentry.io")
                    issues = await sentry.get_issues(
                        config.get("org_slug", ""),
                        config.get("project_slug", ""),
                        query="is:unresolved age:-1h",
                        limit=25,
                    )

                    # Get configurable threshold from agent config
                    threshold = 3
                    agent_cfg = await db.execute(
                        select(AgentConfig).where(
                            AgentConfig.project_id == project_id,
                            AgentConfig.agent_name == self.name,
                        )
                    )
                    cfg = agent_cfg.scalars().first()
                    if cfg and cfg.config:
                        threshold = cfg.config.get("error_threshold", 3)

                    if len(issues) > threshold:
                        errors.append(
                            f"{len(issues)} new Sentry issues in last hour "
                            f"(threshold: {threshold})"
                        )

                # Check Datadog monitors if connected
                result = await db.execute(
                    select(ServiceConnection).where(
                        ServiceConnection.project_id == project_id,
                        ServiceConnection.service_type == "datadog",
                        ServiceConnection.enabled == True,
                    )
                )
                dd_conn = result.scalars().first()
                if dd_conn:
                    checks_run += 1
                    from app.adapters.monitoring_adapter import DatadogAdapter
                    dd_config = dd_conn.config or {}
                    datadog = DatadogAdapter(
                        dd_conn.api_token,
                        dd_config.get("app_key", ""),
                    )
                    monitors = await datadog.get_monitors(
                        tags=dd_config.get("monitor_tags")
                    )
                    alerting = [m for m in monitors if m.get("overall_state") == "Alert"]
                    if alerting:
                        errors.append(
                            f"{len(alerting)} Datadog monitors in Alert state"
                        )
        except Exception:
            logger.exception("Health check encountered errors")
            errors.append("Health check failed to complete")

        return {
            "healthy": len(errors) == 0,
            "errors": errors,
            "reason": errors[0] if errors else None,
            "checks_run": checks_run,
        }

    async def _rollback(self, project_id: int | None, health: dict) -> None:
        """Trigger a rollback by re-running the last successful pipeline on main."""
        logger.warning(f"Rollback triggered for project {project_id}: {health}")

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
                    logger.error("No GitLab connection for rollback")
                    return

                gitlab = GitLabAdapter(conn.base_url or "https://gitlab.com", conn.api_token)
                gl_project_id = (conn.config or {}).get("project_id")
                if not gl_project_id:
                    logger.error("No GitLab project_id for rollback")
                    return

                # Find the last successful pipeline on main to re-trigger
                pipelines = await gitlab.get_pipelines(gl_project_id, ref="main", limit=10)
                last_success = None
                for p in pipelines:
                    if p.get("status") == "success":
                        last_success = p
                        break

                if last_success:
                    # Trigger a new pipeline with rollback variable
                    rollback_pipeline = await gitlab.trigger_pipeline(
                        gl_project_id,
                        ref="main",
                        variables=[
                            {"key": "ROLLBACK", "value": "true"},
                            {"key": "ROLLBACK_PIPELINE_ID", "value": str(last_success["id"])},
                        ],
                    )
                    logger.info(
                        f"Rollback pipeline triggered: {rollback_pipeline.get('id')} "
                        f"(rolling back to pipeline {last_success['id']})"
                    )
                else:
                    logger.error("No successful pipeline found on main for rollback")
        except Exception:
            logger.exception("Failed to execute rollback")
