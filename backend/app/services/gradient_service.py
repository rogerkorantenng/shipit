"""Gradient AI SDK client for knowledge base management and agent calls."""

import json
from typing import AsyncGenerator

import httpx

from app.config import get_settings

settings = get_settings()

GRADIENT_BASE = "https://api.do-ai.run/v1"
AGENT_URL = f"{settings.gradient_agent_endpoint}/api/v1/chat/completions" if settings.gradient_agent_endpoint else "https://inference.do-ai.run/v1/chat/completions"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.gradient_api_key}",
        "Content-Type": "application/json",
    }


class GradientService:
    """Client for Gradient AI platform APIs."""

    # --- Knowledge Base Management ---

    async def create_knowledge_base(self, name: str, description: str = "") -> dict:
        """Create a new Gradient Knowledge Base."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{GRADIENT_BASE}/knowledge-bases",
                headers=_headers(),
                json={"name": name, "description": description},
                timeout=30.0,
            )
            resp.raise_for_status()
            return resp.json()

    async def upload_to_knowledge_base(
        self, kb_id: str, file_content: bytes, filename: str
    ) -> dict:
        """Upload a file to a Knowledge Base for indexing."""
        headers = {"Authorization": f"Bearer {settings.gradient_api_key}"}
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{GRADIENT_BASE}/knowledge-bases/{kb_id}/documents",
                headers=headers,
                files={"file": (filename, file_content)},
                timeout=60.0,
            )
            resp.raise_for_status()
            return resp.json()

    async def search_knowledge_base(
        self, kb_id: str, query: str, top_k: int = 5
    ) -> list[dict]:
        """Search a Knowledge Base with semantic retrieval."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{GRADIENT_BASE}/knowledge-bases/{kb_id}/search",
                headers=_headers(),
                json={"query": query, "top_k": top_k},
                timeout=15.0,
            )
            resp.raise_for_status()
            return resp.json().get("results", [])

    async def delete_knowledge_base(self, kb_id: str) -> None:
        """Delete a Knowledge Base."""
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{GRADIENT_BASE}/knowledge-bases/{kb_id}",
                headers=_headers(),
                timeout=15.0,
            )
            resp.raise_for_status()

    # --- Inference ---

    async def chat_completion(
        self,
        messages: list[dict],
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> dict:
        """Non-streaming chat completion via agent endpoint."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                AGENT_URL,
                headers=_headers(),
                json={
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                timeout=120.0,
            )
            resp.raise_for_status()
            data = resp.json()
            # Handle reasoning models: content may be in reasoning_content
            msg = data["choices"][0]["message"]
            if not msg.get("content") and msg.get("reasoning_content"):
                msg["content"] = msg["reasoning_content"]
            return data

    async def chat_completion_stream(
        self,
        messages: list[dict],
        model: str = "claude-haiku-4-5",
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """Streaming chat completion — yields content chunks."""
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                AGENT_URL,
                headers=_headers(),
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": True,
                },
                timeout=60.0,
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            delta = chunk["choices"][0].get("delta", {})
                            if content := delta.get("content"):
                                yield content
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue


gradient = GradientService()
