"""Datadog and Sentry API adapters for monitoring."""

import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class DatadogAdapter:
    """Client for Datadog API."""

    def __init__(self, api_key: str, app_key: str, site: str = "datadoghq.com"):
        self.base_url = f"https://api.{site}/api/v1"
        self._headers = {
            "DD-API-KEY": api_key,
            "DD-APPLICATION-KEY": app_key,
            "Content-Type": "application/json",
        }

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        async with httpx.AsyncClient() as client:
            resp = await client.request(
                method,
                f"{self.base_url}{path}",
                headers=self._headers,
                timeout=30.0,
                **kwargs,
            )
            resp.raise_for_status()
            return resp.json()

    async def test_connection(self) -> dict:
        return await self._request("GET", "/validate")

    async def query_metrics(
        self, query: str, from_ts: int, to_ts: int
    ) -> dict:
        return await self._request(
            "GET",
            "/query",
            params={"query": query, "from": from_ts, "to": to_ts},
        )

    async def get_monitors(
        self, tags: Optional[list[str]] = None
    ) -> list[dict]:
        params = {}
        if tags:
            params["monitor_tags"] = ",".join(tags)
        return await self._request("GET", "/monitor", params=params)

    async def create_event(
        self, title: str, text: str, tags: Optional[list[str]] = None
    ) -> dict:
        data: dict[str, Any] = {"title": title, "text": text}
        if tags:
            data["tags"] = tags
        return await self._request("POST", "/events", json=data)


class SentryAdapter:
    """Client for Sentry API."""

    def __init__(self, token: str, base_url: str = "https://sentry.io"):
        self.base_url = f"{base_url.rstrip('/')}/api/0"
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        async with httpx.AsyncClient() as client:
            resp = await client.request(
                method,
                f"{self.base_url}{path}",
                headers=self._headers,
                timeout=30.0,
                **kwargs,
            )
            resp.raise_for_status()
            return resp.json()

    async def test_connection(self) -> dict:
        orgs = await self._request("GET", "/organizations/")
        return {"organizations": len(orgs)}

    async def get_issues(
        self,
        org_slug: str,
        project_slug: str,
        query: str = "is:unresolved",
        limit: int = 25,
    ) -> list[dict]:
        return await self._request(
            "GET",
            f"/projects/{org_slug}/{project_slug}/issues/",
            params={"query": query, "limit": limit},
        )

    async def get_project_stats(
        self, org_slug: str, project_slug: str, stat: str = "received"
    ) -> list:
        return await self._request(
            "GET",
            f"/projects/{org_slug}/{project_slug}/stats/",
            params={"stat": stat},
        )
