"""Agent 8: Analytics & Insights - Velocity metrics, reports, bottleneck detection."""

import logging
from datetime import datetime, timedelta

from app.agents.base import BaseAgent
from app.agents.event_bus import Event, EventType
from app.services import agent_ai_service

logger = logging.getLogger(__name__)


class AnalyticsInsightsAgent(BaseAgent):

    @property
    def name(self) -> str:
        return "analytics_insights"

    @property
    def description(self) -> str:
        return (
            "Collects velocity metrics, generates reports, detects bottlenecks, "
            "and provides AI-powered process improvement suggestions"
        )

    @property
    def subscribed_events(self) -> list[EventType]:
        return [EventType.METRICS_COLLECTED]

    async def handle_event(self, event: Event) -> None:
        project_id = event.project_id
        logger.info(f"Analytics collection for project {project_id}")

        metrics = await self._collect_metrics(project_id)
        if not metrics:
            return

        # AI analysis
        analysis = await agent_ai_service.analyze_metrics(metrics)

        # Check for bottlenecks
        bottlenecks = analysis.get("bottlenecks", [])
        if bottlenecks:
            await self.publish(Event(
                type=EventType.BOTTLENECK_DETECTED,
                data={
                    "bottlenecks": bottlenecks,
                    "recommendations": analysis.get("recommendations", []),
                },
                source_agent=self.name,
                project_id=project_id,
                correlation_id=event.correlation_id,
            ))

        # Generate report
        report = {
            "metrics": metrics,
            "analysis": analysis,
            "generated_at": datetime.utcnow().isoformat(),
        }

        await self.publish(Event(
            type=EventType.REPORT_GENERATED,
            data=report,
            source_agent=self.name,
            project_id=project_id,
            correlation_id=event.correlation_id,
        ))

        # Slack summary
        exec_summary = analysis.get("executive_summary", "No summary available")
        predictions = analysis.get("predictions", {})

        await self.publish(Event(
            type=EventType.SLACK_NOTIFICATION,
            data={
                "message": (
                    f"*Analytics Report* :chart_with_upwards_trend:\n"
                    f"{exec_summary}\n\n"
                    f"Sprint completion: {predictions.get('sprint_completion_pct', 'N/A')}%\n"
                    f"Velocity trend: {predictions.get('velocity_trend', 'stable')}\n"
                    f"Bottlenecks: {len(bottlenecks)}"
                ),
            },
            source_agent=self.name,
            project_id=project_id,
            correlation_id=event.correlation_id,
        ))

    async def run_scheduled_report(self, project_ids: list[int] | None = None) -> None:
        """Called by scheduler for periodic reports. Collects and analyzes for each project."""
        if not project_ids:
            project_ids = await self._get_active_project_ids()

        for pid in project_ids:
            logger.info(f"Scheduled analytics report for project {pid}")
            try:
                metrics = await self._collect_metrics(pid)
                if not metrics:
                    logger.info(f"No metrics for project {pid}, skipping")
                    continue

                analysis = await agent_ai_service.analyze_metrics(metrics)

                bottlenecks = analysis.get("bottlenecks", [])
                if bottlenecks:
                    await self.bus.publish(Event(
                        type=EventType.BOTTLENECK_DETECTED,
                        data={
                            "bottlenecks": bottlenecks,
                            "recommendations": analysis.get("recommendations", []),
                        },
                        source_agent=self.name,
                        project_id=pid,
                    ))

                report = {
                    "metrics": metrics,
                    "analysis": analysis,
                    "generated_at": datetime.utcnow().isoformat(),
                    "trigger": "scheduled",
                }

                await self.bus.publish(Event(
                    type=EventType.REPORT_GENERATED,
                    data=report,
                    source_agent=self.name,
                    project_id=pid,
                ))

                exec_summary = analysis.get("executive_summary", "No summary available")
                predictions = analysis.get("predictions", {})
                await self.bus.publish(Event(
                    type=EventType.SLACK_NOTIFICATION,
                    data={
                        "message": (
                            f"*Scheduled Analytics Report* (Project #{pid})\n"
                            f"{exec_summary}\n\n"
                            f"Sprint completion: {predictions.get('sprint_completion_pct', 'N/A')}%\n"
                            f"Velocity trend: {predictions.get('velocity_trend', 'stable')}\n"
                            f"Bottlenecks: {len(bottlenecks)}"
                        ),
                    },
                    source_agent=self.name,
                    project_id=pid,
                ))
            except Exception:
                logger.exception(f"Scheduled report failed for project {pid}")

    async def _collect_metrics(self, project_id: int | None) -> dict:
        if not project_id:
            return {}

        try:
            from sqlalchemy import select, func
            from app.models.task import Task
            from app.models.activity import Activity
            from app.models.sprint import Sprint

            async with self.get_db_session() as db:
                # Task distribution
                result = await db.execute(
                    select(Task.status, func.count()).where(
                        Task.project_id == project_id
                    ).group_by(Task.status)
                )
                task_dist = {row[0]: row[1] for row in result.all()}

                # Tasks completed recently
                week_ago = datetime.utcnow() - timedelta(days=7)
                result = await db.execute(
                    select(func.count()).select_from(Task).where(
                        Task.project_id == project_id,
                        Task.status == "done",
                        Task.updated_at >= week_ago,
                    )
                )
                completed_this_week = result.scalar() or 0

                # Active sprint
                result = await db.execute(
                    select(Sprint).where(
                        Sprint.project_id == project_id,
                        Sprint.status == "active",
                    ).limit(1)
                )
                active_sprint = result.scalars().first()

                sprint_info = None
                if active_sprint:
                    result = await db.execute(
                        select(func.count()).select_from(Task).where(
                            Task.sprint_id == active_sprint.id,
                            Task.status == "done",
                        )
                    )
                    sprint_done = result.scalar() or 0

                    result = await db.execute(
                        select(func.count()).select_from(Task).where(
                            Task.sprint_id == active_sprint.id,
                        )
                    )
                    sprint_total = result.scalar() or 0

                    sprint_info = {
                        "name": active_sprint.name,
                        "start_date": active_sprint.start_date,
                        "end_date": active_sprint.end_date,
                        "tasks_done": sprint_done,
                        "tasks_total": sprint_total,
                    }

                # Recent activity count
                result = await db.execute(
                    select(func.count()).select_from(Activity).where(
                        Activity.project_id == project_id,
                        Activity.created_at >= week_ago,
                    )
                )
                activity_count = result.scalar() or 0

                return {
                    "task_distribution": task_dist,
                    "completed_this_week": completed_this_week,
                    "weekly_activity_count": activity_count,
                    "active_sprint": sprint_info,
                    "total_tasks": sum(task_dist.values()),
                }
        except Exception:
            logger.exception("Failed to collect metrics")
            return {}

    async def _get_active_project_ids(self) -> list[int]:
        """Get project IDs that have the analytics agent enabled."""
        try:
            from sqlalchemy import select
            from app.models.agent_state import AgentConfig
            from app.models.project import Project

            async with self.get_db_session() as db:
                # First check if any projects have explicitly configured this agent
                result = await db.execute(
                    select(AgentConfig.project_id).where(
                        AgentConfig.agent_name == self.name,
                        AgentConfig.enabled == True,
                    )
                )
                configured_ids = [row[0] for row in result.all()]

                if configured_ids:
                    return configured_ids

                # If no explicit configs, run for all projects (default enabled)
                result = await db.execute(select(Project.id))
                return [row[0] for row in result.all()]
        except Exception:
            logger.exception("Failed to get project IDs")
            return []
