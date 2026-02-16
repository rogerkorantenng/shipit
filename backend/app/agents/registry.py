"""Agent registry for lifecycle management of all agents."""

import logging
from typing import Optional

from app.agents.base import BaseAgent
from app.agents.event_bus import EventBus, event_bus

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Manages agent lifecycle: register, start, stop, enable/disable."""

    def __init__(self, bus: Optional[EventBus] = None):
        self.bus = bus or event_bus
        self._agents: dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        self._agents[agent.name] = agent
        agent.register()
        logger.info(f"Registered agent: {agent.name}")

    def get(self, name: str) -> Optional[BaseAgent]:
        return self._agents.get(name)

    def all_agents(self) -> list[BaseAgent]:
        return list(self._agents.values())

    def enable(self, name: str) -> bool:
        agent = self._agents.get(name)
        if agent:
            agent.enable()
            return True
        return False

    def disable(self, name: str) -> bool:
        agent = self._agents.get(name)
        if agent:
            agent.disable()
            return True
        return False

    async def start_all(self) -> None:
        await self.bus.start()
        logger.info(f"All {len(self._agents)} agents registered and bus started")

    async def stop_all(self) -> None:
        for agent in self._agents.values():
            agent.unregister()
        await self.bus.stop()
        logger.info("All agents stopped")

    def status(self) -> list[dict]:
        return [agent.to_dict() for agent in self._agents.values()]


def create_registry(bus: Optional[EventBus] = None) -> AgentRegistry:
    """Instantiate and register all 8 agents."""
    from app.agents.product_intelligence import ProductIntelligenceAgent
    from app.agents.design_sync import DesignSyncAgent
    from app.agents.code_orchestration import CodeOrchestrationAgent
    from app.agents.security_compliance import SecurityComplianceAgent
    from app.agents.test_intelligence import TestIntelligenceAgent
    from app.agents.review_coordination import ReviewCoordinationAgent
    from app.agents.deployment_orchestrator import DeploymentOrchestratorAgent
    from app.agents.analytics_insights import AnalyticsInsightsAgent
    from app.agents.slack_notifier import SlackNotifierAgent

    registry = AgentRegistry(bus=bus)

    agents = [
        ProductIntelligenceAgent(bus=bus),
        DesignSyncAgent(bus=bus),
        CodeOrchestrationAgent(bus=bus),
        SecurityComplianceAgent(bus=bus),
        TestIntelligenceAgent(bus=bus),
        ReviewCoordinationAgent(bus=bus),
        DeploymentOrchestratorAgent(bus=bus),
        AnalyticsInsightsAgent(bus=bus),
        SlackNotifierAgent(bus=bus),
    ]

    for agent in agents:
        registry.register(agent)

    return registry
