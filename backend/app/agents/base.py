"""Base agent class with common infrastructure for all agents."""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from app.agents.event_bus import Event, EventBus, EventType, event_bus
from app.db.database import async_session
from app.services.gradient_service import gradient

logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class AgentMetrics:
    events_processed: int = 0
    errors: int = 0
    last_run: Optional[datetime] = None
    avg_processing_ms: float = 0.0
    _total_ms: float = field(default=0.0, repr=False)


class BaseAgent(ABC):
    """Abstract base class for all ShipIt agents."""

    def __init__(self, bus: Optional[EventBus] = None):
        self.bus = bus or event_bus
        self.status = AgentStatus.IDLE
        self.metrics = AgentMetrics()
        self._enabled = True

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        ...

    @property
    @abstractmethod
    def subscribed_events(self) -> list[EventType]:
        ...

    @abstractmethod
    async def handle_event(self, event: Event) -> None:
        ...

    def register(self) -> None:
        for event_type in self.subscribed_events:
            self.bus.subscribe(event_type, self._on_event)

    def unregister(self) -> None:
        for event_type in self.subscribed_events:
            self.bus.unsubscribe(event_type, self._on_event)

    async def _on_event(self, event: Event) -> None:
        if not self._enabled:
            return

        self.status = AgentStatus.RUNNING
        start = time.monotonic()

        try:
            await self.handle_event(event)
            elapsed_ms = (time.monotonic() - start) * 1000
            self.metrics.events_processed += 1
            self.metrics._total_ms += elapsed_ms
            self.metrics.avg_processing_ms = (
                self.metrics._total_ms / self.metrics.events_processed
            )
            self.metrics.last_run = datetime.utcnow()
            self.status = AgentStatus.IDLE
        except Exception as e:
            elapsed_ms = (time.monotonic() - start) * 1000
            self.metrics.errors += 1
            self.status = AgentStatus.ERROR
            logger.exception(f"Agent {self.name} error handling {event.type.value}")
            await self.publish(Event(
                type=EventType.AGENT_ERROR,
                data={
                    "agent": self.name,
                    "event_type": event.type.value,
                    "error": str(e),
                    "processing_ms": elapsed_ms,
                },
                source_agent=self.name,
                project_id=event.project_id,
                correlation_id=event.correlation_id,
            ))

    async def publish(self, event: Event) -> None:
        await self.bus.publish(event)

    async def ai_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "claude-haiku-4-5",
        max_tokens: int = 2048,
        temperature: float = 0.3,
    ) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return await gradient.chat_completion(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    def get_db_session(self):
        return async_session()

    def enable(self) -> None:
        self._enabled = True
        if self.status == AgentStatus.DISABLED:
            self.status = AgentStatus.IDLE

    def disable(self) -> None:
        self._enabled = False
        self.status = AgentStatus.DISABLED

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "enabled": self._enabled,
            "subscribed_events": [e.value for e in self.subscribed_events],
            "metrics": {
                "events_processed": self.metrics.events_processed,
                "errors": self.metrics.errors,
                "last_run": self.metrics.last_run.isoformat() if self.metrics.last_run else None,
                "avg_processing_ms": round(self.metrics.avg_processing_ms, 2),
            },
        }
