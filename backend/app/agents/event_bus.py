"""In-process async event bus with pub/sub for agent communication."""

import asyncio
import logging
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Coroutine, Optional

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    # Jira events
    JIRA_TICKET_CREATED = "jira.ticket.created"
    JIRA_TICKET_UPDATED = "jira.ticket.updated"

    # GitLab events
    CODE_PUSHED = "gitlab.code.pushed"
    PR_OPENED = "gitlab.pr.opened"
    PR_READY_FOR_REVIEW = "gitlab.pr.ready_for_review"
    PR_APPROVED = "gitlab.pr.approved"
    MERGE_TO_MAIN = "gitlab.merge.main"
    GITLAB_ISSUE_ASSIGNED = "gitlab.issue.assigned"
    PIPELINE_STARTED = "gitlab.pipeline.started"
    PIPELINE_COMPLETED = "gitlab.pipeline.completed"
    PIPELINE_FAILED = "gitlab.pipeline.failed"

    # Figma events
    FIGMA_DESIGN_CHANGED = "figma.design.changed"

    # Product Intelligence Agent
    REQUIREMENTS_ANALYZED = "agent.product.requirements_analyzed"
    COMPLEXITY_TAGGED = "agent.product.complexity_tagged"
    STORIES_EXTRACTED = "agent.product.stories_extracted"

    # Design Sync Agent
    DESIGN_COMPARED = "agent.design.compared"
    IMPLEMENTATION_NOTES_GENERATED = "agent.design.impl_notes"

    # Code Orchestration Agent
    BRANCH_CREATED = "agent.code.branch_created"
    BOILERPLATE_GENERATED = "agent.code.boilerplate_generated"
    PR_TEMPLATE_CREATED = "agent.code.pr_template_created"

    # Security & Compliance Agent
    SECURITY_SCAN_COMPLETE = "agent.security.scan_complete"
    VULNERABILITY_FOUND = "agent.security.vulnerability_found"
    MERGE_BLOCKED = "agent.security.merge_blocked"
    COMPLIANCE_REPORT_GENERATED = "agent.security.compliance_report"

    # Test Intelligence Agent
    TEST_SUGGESTIONS_GENERATED = "agent.test.suggestions_generated"
    TEST_REPORT_CREATED = "agent.test.report_created"
    COVERAGE_REPORT = "agent.test.coverage_report"

    # Review Coordination Agent
    REVIEWERS_ASSIGNED = "agent.review.reviewers_assigned"
    REVIEW_REMINDER_SENT = "agent.review.reminder_sent"
    REVIEW_SLA_BREACHED = "agent.review.sla_breached"
    PR_AUTO_MERGED = "agent.review.auto_merged"

    # Deployment Orchestrator Agent
    DEPLOY_STARTED = "agent.deploy.started"
    DEPLOY_COMPLETE = "agent.deploy.complete"
    DEPLOY_FAILED = "agent.deploy.failed"
    ROLLBACK_TRIGGERED = "agent.deploy.rollback"
    RELEASE_NOTES_GENERATED = "agent.deploy.release_notes"

    # Analytics & Insights Agent
    METRICS_COLLECTED = "agent.analytics.metrics_collected"
    REPORT_GENERATED = "agent.analytics.report_generated"
    BOTTLENECK_DETECTED = "agent.analytics.bottleneck_detected"

    # Cross-cutting
    SLACK_NOTIFICATION = "notification.slack"
    AGENT_ERROR = "agent.error"


@dataclass
class Event:
    type: EventType
    data: dict[str, Any]
    source_agent: str = "system"
    project_id: Optional[int] = None
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None


EventHandler = Callable[[Event], Coroutine[Any, Any, None]]


class EventBus:
    """Async in-process event bus with pub/sub pattern."""

    def __init__(self, history_size: int = 1000):
        self._subscribers: dict[EventType, list[EventHandler]] = {}
        self._queue: asyncio.Queue[Event] = asyncio.Queue()
        self._history: deque[Event] = deque(maxlen=history_size)
        self._running = False
        self._dispatch_task: Optional[asyncio.Task] = None

    @property
    def is_running(self) -> bool:
        return self._running

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.debug(f"Subscribed {handler.__qualname__} to {event_type.value}")

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                h for h in self._subscribers[event_type] if h != handler
            ]

    async def publish(self, event: Event) -> None:
        self._history.append(event)
        await self._queue.put(event)
        logger.info(
            f"Event published: {event.type.value} from {event.source_agent} "
            f"(project={event.project_id}, id={event.event_id})"
        )

    async def _dispatch(self) -> None:
        while self._running:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

            handlers = self._subscribers.get(event.type, [])
            if not handlers:
                logger.debug(f"No subscribers for {event.type.value}")
                continue

            for handler in handlers:
                try:
                    await handler(event)
                except Exception:
                    logger.exception(
                        f"Error in handler {handler.__qualname__} for {event.type.value}"
                    )

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._dispatch_task = asyncio.create_task(self._dispatch())
        logger.info("Event bus started")

    async def stop(self) -> None:
        self._running = False
        if self._dispatch_task:
            self._dispatch_task.cancel()
            try:
                await self._dispatch_task
            except asyncio.CancelledError:
                pass
            self._dispatch_task = None
        logger.info("Event bus stopped")

    def get_history(
        self,
        limit: int = 50,
        event_type: Optional[EventType] = None,
        project_id: Optional[int] = None,
    ) -> list[Event]:
        events = list(self._history)
        if event_type:
            events = [e for e in events if e.type == event_type]
        if project_id:
            events = [e for e in events if e.project_id == project_id]
        return events[-limit:]


# Module-level singleton
event_bus = EventBus()
