"""Lightweight cron-like scheduler for periodic agent tasks."""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Callable, Coroutine, Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class Job:
    name: str
    func: Callable[[], Coroutine[Any, Any, None]]
    interval_seconds: float
    last_run: float = 0.0


class Scheduler:
    """Asyncio-based periodic task scheduler with 30s tick resolution."""

    def __init__(self, tick_interval: float = 30.0):
        self._jobs: list[Job] = []
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._tick_interval = tick_interval

    def add_job(
        self,
        name: str,
        func: Callable[[], Coroutine[Any, Any, None]],
        interval_seconds: float,
    ) -> None:
        self._jobs.append(Job(name=name, func=func, interval_seconds=interval_seconds))
        logger.info(f"Scheduled job '{name}' every {interval_seconds}s")

    async def _tick(self) -> None:
        while self._running:
            now = time.monotonic()
            for job in self._jobs:
                if now - job.last_run >= job.interval_seconds:
                    job.last_run = now
                    try:
                        await job.func()
                    except Exception:
                        logger.exception(f"Scheduler job '{job.name}' failed")
            try:
                await asyncio.sleep(self._tick_interval)
            except asyncio.CancelledError:
                break

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._tick())
        logger.info("Scheduler started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Scheduler stopped")
