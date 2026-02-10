"""StudyDrip Tutor Agent — Gradient ADK entrypoint.

An adaptive AI tutor with a 3-axis persona system that teaches, quizzes,
and tracks student progress using uploaded course materials.
"""

import json
import os
from typing import AsyncGenerator

import httpx
from dotenv import load_dotenv

from persona import PersonaState
from prompts import build_system_prompt
from tools import TOOL_DEFINITIONS, execute_tool

load_dotenv()

GRADIENT_API_KEY = os.getenv("GRADIENT_API_KEY", "")
INFERENCE_URL = "https://inference.do-ai.run/v1/chat/completions"


async def call_inference(
    messages: list[dict],
    tools: list[dict] | None = None,
    model: str = "claude-haiku-4-5",
    stream: bool = True,
) -> AsyncGenerator[str, None] | dict:
    """Call Gradient Inference API (Claude via DigitalOcean)."""
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 2048,
        "temperature": 0.7,
    }
    if tools:
        payload["tools"] = tools

    headers = {
        "Authorization": f"Bearer {GRADIENT_API_KEY}",
        "Content-Type": "application/json",
    }

    if stream and not tools:
        payload["stream"] = True
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST", INFERENCE_URL, json=payload, headers=headers, timeout=60.0
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
    else:
        payload["stream"] = False
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                INFERENCE_URL, json=payload, headers=headers, timeout=60.0
            )
            return resp.json()


class TutorAgent:
    """The StudyDrip tutor agent with adaptive persona."""

    def __init__(self):
        self.persona = PersonaState()
        self.conversation_history: list[dict] = []

    async def initialize(self, user_id: int, course_id: int, kb_id: str = "") -> None:
        """Initialize the agent for a conversation."""
        self.context = {
            "user_id": user_id,
            "course_id": course_id,
            "kb_id": kb_id,
        }
        # Fetch current progress
        from tools import get_progress

        progress = await get_progress(user_id, course_id)
        self.persona.update_from_progress(progress)

    def _build_messages(self, user_message: str) -> list[dict]:
        """Build the full message list with system prompt."""
        # Suggest mode based on user message
        self.persona.mode = self.persona.suggest_mode(user_message)

        system_prompt = build_system_prompt(
            level=self.persona.level,
            momentum=self.persona.momentum,
            mode=self.persona.mode,
        )

        messages = [{"role": "system", "content": system_prompt}]
        # Include conversation history (last 20 messages)
        messages.extend(self.conversation_history[-20:])
        messages.append({"role": "user", "content": user_message})
        return messages

    async def chat(self, user_message: str) -> AsyncGenerator[str, None]:
        """Process a user message and stream the response."""
        self.conversation_history.append({"role": "user", "content": user_message})
        messages = self._build_messages(user_message)

        # First, check if we need tool calls (non-streaming)
        response = await call_inference(
            messages, tools=TOOL_DEFINITIONS, stream=False
        )

        if not isinstance(response, dict):
            # Shouldn't happen with stream=False, but handle gracefully
            yield "I'm having trouble processing that. Could you try again?"
            return

        choice = response.get("choices", [{}])[0]
        message = choice.get("message", {})

        # Handle tool calls
        if tool_calls := message.get("tool_calls"):
            messages.append(message)

            for tc in tool_calls:
                func_name = tc["function"]["name"]
                try:
                    arguments = json.loads(tc["function"]["arguments"])
                except json.JSONDecodeError:
                    arguments = {}

                result = await execute_tool(func_name, arguments, self.context)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result,
                })

                # If quiz was generated, update persona
                if func_name == "generate_quiz":
                    self.persona.mode = "quiz"

            # Now get the final response (streaming)
            full_response = ""
            async for chunk in call_inference(messages, stream=True):
                full_response += chunk
                yield chunk

            self.conversation_history.append(
                {"role": "assistant", "content": full_response}
            )
        elif content := message.get("content"):
            # No tool calls, just stream the content
            # Re-do as streaming for better UX
            full_response = ""
            async for chunk in call_inference(messages, stream=True):
                full_response += chunk
                yield chunk

            self.conversation_history.append(
                {"role": "assistant", "content": full_response}
            )
        else:
            yield "I'm not sure how to respond to that. Could you rephrase?"

    async def grade_quiz(self, quiz_id: int, answers: dict) -> dict:
        """Grade a quiz attempt and update progress."""
        from tools import update_progress

        # The actual grading happens on the backend
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{os.getenv('BACKEND_URL', 'http://localhost:8000')}/api/quiz/{quiz_id}/submit",
                json={
                    "user_id": self.context["user_id"],
                    "answers": answers,
                },
                timeout=15.0,
            )
            if resp.status_code == 200:
                result = resp.json()
                score = result.get("score", 0)

                # Update persona
                self.persona.record_quiz_score(score)
                level_change = self.persona.assess_level_change()

                # Update backend progress
                update_data = {
                    "user_id": self.context["user_id"],
                    "course_id": self.context["course_id"],
                    "score": score,
                    "momentum": self.persona.momentum,
                }
                if level_change:
                    update_data["level"] = level_change
                    self.persona.level = level_change

                await update_progress(**update_data)
                return result

        return {"error": "Failed to grade quiz"}


# Gradient ADK entrypoint
agent = TutorAgent()


async def entrypoint(message: str, context: dict = None) -> AsyncGenerator[str, None]:
    """Gradient ADK entrypoint for the tutor agent.

    Args:
        message: The user's message
        context: Dict with user_id, course_id, kb_id, and optional history

    Yields:
        Streamed response chunks
    """
    ctx = context or {}
    user_id = ctx.get("user_id", 0)
    course_id = ctx.get("course_id", 0)
    kb_id = ctx.get("kb_id", "")

    # Initialize if needed
    if not hasattr(agent, "context") or agent.context.get("course_id") != course_id:
        await agent.initialize(user_id, course_id, kb_id)

    # Restore conversation history if provided
    if history := ctx.get("history"):
        agent.conversation_history = history

    async for chunk in agent.chat(message):
        yield chunk
