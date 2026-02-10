"""Function calling tools for the StudyDrip tutor agent."""

import json
import httpx
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


async def search_knowledge_base(query: str, kb_id: str) -> dict:
    """Search the course knowledge base for relevant material.

    Args:
        query: The search query (topic or question to look up)
        kb_id: The Gradient Knowledge Base ID for the course

    Returns:
        Dict with 'results' containing relevant text chunks from course materials.
    """
    if not kb_id:
        return {"results": [], "message": "No knowledge base configured for this course."}

    # In production, this calls the Gradient KB search API
    # For now, proxy through our backend
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{BACKEND_URL}/api/courses/kb/search",
                json={"query": query, "kb_id": kb_id},
                timeout=15.0,
            )
            if resp.status_code == 200:
                return resp.json()
        except httpx.RequestError:
            pass

    return {"results": [], "message": "Knowledge base search unavailable."}


async def generate_quiz(
    course_id: int,
    user_id: int,
    topic: str = "",
    num_questions: int = 5,
    difficulty: str = "medium",
) -> dict:
    """Generate a quiz from course materials.

    Args:
        course_id: The course ID
        user_id: The user ID
        topic: Optional topic to focus on
        num_questions: Number of questions (default 5)
        difficulty: easy, medium, or hard

    Returns:
        Dict with quiz 'id' and 'questions' array.
    """
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{BACKEND_URL}/api/quiz/generate",
                json={
                    "course_id": course_id,
                    "user_id": user_id,
                    "topic": topic,
                    "num_questions": num_questions,
                    "difficulty": difficulty,
                },
                timeout=30.0,
            )
            if resp.status_code == 200:
                return resp.json()
        except httpx.RequestError:
            pass

    return {"error": "Failed to generate quiz. Please try again."}


async def get_progress(user_id: int, course_id: int) -> dict:
    """Get the student's current learning progress.

    Args:
        user_id: The user ID
        course_id: The course ID

    Returns:
        Dict with progress data (level, momentum, scores, etc.)
    """
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{BACKEND_URL}/api/progress/{course_id}",
                params={"user_id": user_id},
                timeout=10.0,
            )
            if resp.status_code == 200:
                return resp.json()
        except httpx.RequestError:
            pass

    return {
        "level": "beginner",
        "momentum": "steady",
        "avg_score": 0.0,
        "total_quizzes": 0,
        "topics_mastered": [],
        "weak_areas": [],
    }


async def update_progress(
    user_id: int,
    course_id: int,
    score: float | None = None,
    level: str | None = None,
    momentum: str | None = None,
    topics_mastered: list[str] | None = None,
    weak_areas: list[str] | None = None,
) -> dict:
    """Update the student's learning progress.

    Args:
        user_id: The user ID
        course_id: The course ID
        score: New quiz score to record (0.0 to 1.0)
        level: New learning level if changed
        momentum: New momentum tier if changed
        topics_mastered: List of mastered topics to add
        weak_areas: List of weak areas to add

    Returns:
        Dict with updated progress data.
    """
    payload = {"user_id": user_id, "course_id": course_id}
    if score is not None:
        payload["score"] = score
    if level is not None:
        payload["level"] = level
    if momentum is not None:
        payload["momentum"] = momentum
    if topics_mastered is not None:
        payload["topics_mastered"] = topics_mastered
    if weak_areas is not None:
        payload["weak_areas"] = weak_areas

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.put(
                f"{BACKEND_URL}/api/progress/{course_id}",
                json=payload,
                timeout=10.0,
            )
            if resp.status_code == 200:
                return resp.json()
        except httpx.RequestError:
            pass

    return {"error": "Failed to update progress."}


# Tool definitions for the agent (OpenAI function calling format)
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search the student's uploaded course materials for relevant information. Use this before answering questions about course content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query — topic or question to look up in course materials",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_quiz",
            "description": "Generate quiz questions from course materials. Use when the student wants to be tested or after explaining a concept.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Optional topic to focus the quiz on",
                    },
                    "num_questions": {
                        "type": "integer",
                        "description": "Number of questions (1-10, default 5)",
                        "default": 5,
                    },
                    "difficulty": {
                        "type": "string",
                        "enum": ["easy", "medium", "hard"],
                        "description": "Quiz difficulty level",
                        "default": "medium",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_progress",
            "description": "Retrieve the student's current learning progress, scores, and stats.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_progress",
            "description": "Update the student's progress after a quiz or when their level changes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "score": {
                        "type": "number",
                        "description": "Quiz score as a fraction (0.0 to 1.0)",
                    },
                    "level": {
                        "type": "string",
                        "enum": ["beginner", "intermediate", "advanced"],
                        "description": "New learning level if changed",
                    },
                    "momentum": {
                        "type": "string",
                        "enum": ["struggling", "steady", "thriving"],
                        "description": "New momentum tier if changed",
                    },
                    "topics_mastered": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Topics the student has mastered",
                    },
                    "weak_areas": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Areas where the student needs more practice",
                    },
                },
                "required": [],
            },
        },
    },
]


# Map tool names to functions
TOOL_MAP = {
    "search_knowledge_base": search_knowledge_base,
    "generate_quiz": generate_quiz,
    "get_progress": get_progress,
    "update_progress": update_progress,
}


async def execute_tool(name: str, arguments: dict, context: dict) -> str:
    """Execute a tool by name with the given arguments and conversation context.

    Args:
        name: Tool function name
        arguments: Tool arguments from the model
        context: Conversation context (user_id, course_id, kb_id)

    Returns:
        JSON string of the tool result
    """
    func = TOOL_MAP.get(name)
    if not func:
        return json.dumps({"error": f"Unknown tool: {name}"})

    # Inject context into tool calls
    if name == "search_knowledge_base":
        arguments["kb_id"] = context.get("kb_id", "")
    elif name in ("generate_quiz", "update_progress", "get_progress"):
        arguments["user_id"] = context.get("user_id")
        arguments["course_id"] = context.get("course_id")

    result = await func(**arguments)
    return json.dumps(result)
