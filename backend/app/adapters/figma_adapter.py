"""Figma REST API adapter."""

import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

FIGMA_API = "https://api.figma.com/v1"


class FigmaAdapter:
    """Client for Figma REST API."""

    def __init__(self, token: str):
        self._headers = {"X-Figma-Token": token}

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        async with httpx.AsyncClient() as client:
            resp = await client.request(
                method,
                f"{FIGMA_API}{path}",
                headers=self._headers,
                timeout=30.0,
                **kwargs,
            )
            resp.raise_for_status()
            return resp.json()

    async def test_connection(self) -> dict:
        return await self._request("GET", "/me")

    async def get_file(self, file_key: str) -> dict:
        return await self._request("GET", f"/files/{file_key}")

    async def get_file_versions(
        self, file_key: str, limit: int = 10
    ) -> dict:
        return await self._request(
            "GET", f"/files/{file_key}/versions", params={"page_size": limit}
        )

    async def get_images(
        self,
        file_key: str,
        node_ids: list[str],
        format: str = "png",
        scale: float = 2.0,
    ) -> dict:
        return await self._request(
            "GET",
            f"/images/{file_key}",
            params={
                "ids": ",".join(node_ids),
                "format": format,
                "scale": scale,
            },
        )

    async def get_comments(self, file_key: str) -> dict:
        return await self._request("GET", f"/files/{file_key}/comments")

    async def post_comment(
        self,
        file_key: str,
        message: str,
        client_meta: Optional[dict] = None,
    ) -> dict:
        data: dict[str, Any] = {"message": message}
        if client_meta:
            data["client_meta"] = client_meta
        return await self._request(
            "POST", f"/files/{file_key}/comments", json=data
        )

    async def get_file_components(self, file_key: str) -> dict:
        return await self._request("GET", f"/files/{file_key}/components")
