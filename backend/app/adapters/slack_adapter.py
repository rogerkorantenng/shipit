"""Slack Web API adapter."""

import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

SLACK_API = "https://slack.com/api"


class SlackAdapter:
    """Client for Slack Web API."""

    def __init__(self, bot_token: str):
        self._headers = {
            "Authorization": f"Bearer {bot_token}",
            "Content-Type": "application/json",
        }

    async def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.request(
                method,
                f"{SLACK_API}/{endpoint}",
                headers=self._headers,
                timeout=15.0,
                **kwargs,
            )
            resp.raise_for_status()
            data = resp.json()
            if not data.get("ok"):
                raise Exception(f"Slack API error: {data.get('error', 'unknown')}")
            return data

    async def test_connection(self) -> dict:
        return await self._request("POST", "auth.test")

    async def post_message(
        self,
        channel: str,
        text: str,
        blocks: Optional[list[dict]] = None,
        thread_ts: Optional[str] = None,
    ) -> dict:
        data: dict[str, Any] = {"channel": channel, "text": text}
        if blocks:
            data["blocks"] = blocks
        if thread_ts:
            data["thread_ts"] = thread_ts
        return await self._request("POST", "chat.postMessage", json=data)

    async def update_message(
        self,
        channel: str,
        ts: str,
        text: str,
        blocks: Optional[list[dict]] = None,
    ) -> dict:
        data: dict[str, Any] = {"channel": channel, "ts": ts, "text": text}
        if blocks:
            data["blocks"] = blocks
        return await self._request("POST", "chat.update", json=data)

    async def send_dm(self, user_id: str, text: str) -> dict:
        open_resp = await self._request(
            "POST", "conversations.open", json={"users": user_id}
        )
        channel = open_resp["channel"]["id"]
        return await self.post_message(channel, text)

    async def add_reaction(
        self, channel: str, timestamp: str, emoji: str
    ) -> dict:
        return await self._request(
            "POST",
            "reactions.add",
            json={"channel": channel, "timestamp": timestamp, "name": emoji},
        )
