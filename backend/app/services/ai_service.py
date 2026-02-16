"""AI service for ShipIt — task breakdown, meeting notes extraction, blocker detection, digest."""

import json
import re

from app.services.gradient_service import gradient

# Approximate char limit per chunk — keeps each AI call well within context limits.
_CHUNK_CHAR_LIMIT = 3000


def _parse_json(content: str, fallback: dict | list) -> dict | list:
    """Strip markdown fences and parse JSON, returning fallback on failure."""
    cleaned = re.sub(r"```(?:json)?\s*", "", content).strip().rstrip("`")
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        return fallback


def _chunk_text(text: str, limit: int = _CHUNK_CHAR_LIMIT) -> list[str]:
    """Split long text into chunks on paragraph boundaries with overlap."""
    if len(text) <= limit:
        return [text]

    paragraphs = re.split(r"\n\s*\n", text)
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        if current and len(current) + len(para) + 2 > limit:
            chunks.append(current.strip())
            # Keep last ~200 chars as overlap for context continuity
            current = current[-200:] + "\n\n" + para
        else:
            current = (current + "\n\n" + para) if current else para

    if current.strip():
        chunks.append(current.strip())

    return chunks if chunks else [text]


def _merge_extraction_results(results: list[dict]) -> dict:
    """Merge multiple extraction results, deduplicating updates by task_id."""
    all_tasks: list[dict] = []
    seen_update_ids: set[int] = set()
    all_updates: list[dict] = []
    seen_titles: set[str] = set()

    for r in results:
        for t in r.get("tasks", []):
            title_lower = t.get("title", "").strip().lower()
            if title_lower and title_lower not in seen_titles:
                seen_titles.add(title_lower)
                all_tasks.append(t)

        for u in r.get("updates", []):
            tid = u.get("task_id")
            if tid and tid not in seen_update_ids:
                seen_update_ids.add(tid)
                all_updates.append(u)

    return {"tasks": all_tasks, "updates": all_updates}


async def break_down_task(description: str, existing_members: list[str]) -> dict:
    members_str = ", ".join(existing_members) if existing_members else "no members yet"
    messages = [
        {
            "role": "system",
            "content": (
                "You are a project management AI. Break down the given task description "
                "into actionable subtasks. Return valid JSON only.\n\n"
                f"Team members: {members_str}"
            ),
        },
        {
            "role": "user",
            "content": (
                f"Break this down into subtasks:\n\n{description}\n\n"
                "Return JSON with this exact structure:\n"
                '{\n'
                '  "title": "main task title",\n'
                '  "subtasks": [\n'
                '    {\n'
                '      "title": "subtask title",\n'
                '      "description": "what needs to be done",\n'
                '      "priority": "low|medium|high|urgent",\n'
                '      "estimated_hours": 2.0,\n'
                '      "suggested_assignee": "member name or null"\n'
                '    }\n'
                '  ],\n'
                '  "suggested_priority": "medium",\n'
                '  "detected_blockers": ["any dependency or blocker"]\n'
                '}'
            ),
        },
    ]
    content = await gradient.chat_completion(messages, max_tokens=2048, temperature=0.3)
    return _parse_json(content, {"title": description, "subtasks": [], "suggested_priority": "medium", "detected_blockers": []})


async def _extract_chunk(
    chunk: str,
    members_str: str,
    existing_tasks_str: str,
    source_label: str = "conversation",
) -> dict:
    """Run extraction on a single chunk of text."""
    messages = [
        {
            "role": "system",
            "content": (
                "You are a project management AI. Extract action items from the given text. "
                "You MUST do two things:\n"
                "1. Identify NEW tasks that should be created.\n"
                "2. Identify STATUS UPDATES for EXISTING tasks mentioned in the text "
                "(e.g. 'login page is done', 'API work started', 'payment is blocked').\n\n"
                "Match existing tasks by looking for references to their titles or descriptions in the text. "
                "Return valid JSON only.\n\n"
                f"Team members: {members_str}"
                f"{existing_tasks_str}"
            ),
        },
        {
            "role": "user",
            "content": (
                f"Extract tasks and updates from this {source_label}:\n\n{chunk}\n\n"
                "Return JSON with this exact structure:\n"
                '{\n'
                '  "tasks": [\n'
                '    {\n'
                '      "title": "new task title",\n'
                '      "description": "details",\n'
                '      "priority": "low|medium|high|urgent",\n'
                '      "estimated_hours": 2.0,\n'
                '      "suggested_assignee": "member name or null"\n'
                '    }\n'
                '  ],\n'
                '  "updates": [\n'
                '    {\n'
                '      "task_id": 1,\n'
                '      "task_title": "existing task title",\n'
                '      "new_status": "todo|in_progress|done|blocked",\n'
                '      "new_priority": "low|medium|high|urgent or null if unchanged",\n'
                '      "new_assignee": "member name or null if unchanged",\n'
                '      "reason": "brief reason from the text"\n'
                '    }\n'
                '  ]\n'
                '}\n\n'
                "IMPORTANT: Only include updates for tasks that are clearly referenced in the text. "
                "Do NOT update tasks that aren't mentioned. If no updates are needed, return an empty updates array."
            ),
        },
    ]
    content = await gradient.chat_completion(messages, max_tokens=2048, temperature=0.3)
    return _parse_json(content, {"tasks": [], "updates": []})


async def extract_meeting_notes(
    notes: str, existing_members: list[str], existing_tasks: list[dict] | None = None
) -> dict:
    members_str = ", ".join(existing_members) if existing_members else "no members yet"

    existing_tasks_str = ""
    if existing_tasks:
        existing_tasks_str = (
            "\n\nEXISTING TASKS ON THE BOARD (use these IDs for updates):\n"
            + json.dumps(existing_tasks, indent=2)
        )

    chunks = _chunk_text(notes)

    if len(chunks) == 1:
        return await _extract_chunk(chunks[0], members_str, existing_tasks_str, "conversation")

    # Process multiple chunks and merge
    import asyncio
    results = await asyncio.gather(
        *[_extract_chunk(c, members_str, existing_tasks_str, "conversation (part)") for c in chunks]
    )
    return _merge_extraction_results(list(results))


async def extract_tasks_from_text(
    text: str, existing_members: list[str], existing_tasks: list[dict] | None = None
) -> dict:
    """Extract tasks from any text — meeting notes, emails, Slack messages, etc."""
    members_str = ", ".join(existing_members) if existing_members else "no members yet"

    existing_tasks_str = ""
    if existing_tasks:
        existing_tasks_str = (
            "\n\nEXISTING TASKS ON THE BOARD (use these IDs for updates):\n"
            + json.dumps(existing_tasks, indent=2)
        )

    chunks = _chunk_text(text)

    if len(chunks) == 1:
        return await _extract_chunk(chunks[0], members_str, existing_tasks_str, "text")

    import asyncio
    results = await asyncio.gather(
        *[_extract_chunk(c, members_str, existing_tasks_str, "text (part)") for c in chunks]
    )
    return _merge_extraction_results(list(results))


async def detect_blockers(tasks: list[dict]) -> dict:
    tasks_summary = json.dumps(tasks, indent=2)
    messages = [
        {
            "role": "system",
            "content": (
                "You are a project management AI. Analyze the project tasks and identify "
                "potential blockers, dependency issues, and risks. Return valid JSON only."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Analyze these tasks for blockers and dependencies:\n\n{tasks_summary}\n\n"
                "Return JSON with this exact structure:\n"
                '{\n'
                '  "blockers": [\n'
                '    {\n'
                '      "task_id": 1,\n'
                '      "task_title": "task name",\n'
                '      "issue": "description of the blocker or risk",\n'
                '      "severity": "low|medium|high",\n'
                '      "suggestion": "recommended action"\n'
                '    }\n'
                '  ]\n'
                '}'
            ),
        },
    ]
    content = await gradient.chat_completion(messages, max_tokens=2048, temperature=0.3)
    return _parse_json(content, {"blockers": []})


async def plan_sprint(
    tasks: list[dict], members: list[dict], capacity_hours: float
) -> dict:
    """AI sprint planner — assigns tasks to a sprint based on team capacity."""
    context = json.dumps(
        {"tasks": tasks, "members": members, "total_capacity_hours": capacity_hours},
        indent=2,
    )
    messages = [
        {
            "role": "system",
            "content": (
                "You are a project management AI. Plan a sprint by selecting and assigning "
                "tasks from the backlog to fit within the team's capacity. Prioritize high-priority "
                "and blocked-dependency tasks. Balance workload across members. Return valid JSON only."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Plan a sprint with this data:\n\n{context}\n\n"
                "Return JSON with this exact structure:\n"
                '{\n'
                '  "sprint_name": "Sprint name",\n'
                '  "goal": "brief sprint goal statement",\n'
                '  "start_date": "YYYY-MM-DD",\n'
                '  "end_date": "YYYY-MM-DD",\n'
                '  "total_hours": 40,\n'
                '  "assignments": [\n'
                '    {\n'
                '      "task_id": 1,\n'
                '      "task_title": "task name",\n'
                '      "assignee": "member name",\n'
                '      "estimated_hours": 4,\n'
                '      "priority": "high",\n'
                '      "reason": "why this task was included"\n'
                '    }\n'
                '  ],\n'
                '  "deferred": [\n'
                '    {\n'
                '      "task_id": 2,\n'
                '      "task_title": "task name",\n'
                '      "reason": "why this was deferred"\n'
                '    }\n'
                '  ]\n'
                '}'
            ),
        },
    ]
    content = await gradient.chat_completion(messages, max_tokens=2048, temperature=0.3)
    return _parse_json(content, {"sprint_name": "Sprint", "goal": "", "start_date": None, "end_date": None, "total_hours": 0, "assignments": [], "deferred": []})


async def score_priorities(tasks: list[dict]) -> dict:
    """AI priority scoring — suggests reordering based on dependencies, urgency, impact."""
    tasks_summary = json.dumps(tasks, indent=2)
    messages = [
        {
            "role": "system",
            "content": (
                "You are a project management AI. Analyze tasks and suggest optimal priority "
                "ordering based on dependencies, urgency, business impact, and effort. "
                "Return valid JSON only."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Score and reorder these tasks by priority:\n\n{tasks_summary}\n\n"
                "Return JSON with this exact structure:\n"
                '{\n'
                '  "recommendations": [\n'
                '    {\n'
                '      "task_id": 1,\n'
                '      "task_title": "task name",\n'
                '      "current_priority": "medium",\n'
                '      "suggested_priority": "high",\n'
                '      "score": 85,\n'
                '      "reason": "why this priority is recommended"\n'
                '    }\n'
                '  ]\n'
                '}'
            ),
        },
    ]
    content = await gradient.chat_completion(messages, max_tokens=2048, temperature=0.3)
    return _parse_json(content, {"recommendations": []})


async def generate_standup(
    activities: list[dict], tasks: list[dict], members: list[str]
) -> dict:
    """AI standup generator — per-member summary of did/doing/blocked."""
    context = json.dumps(
        {"recent_activities": activities, "current_tasks": tasks, "members": members},
        indent=2,
    )
    messages = [
        {
            "role": "system",
            "content": (
                "You are a project management AI. Generate a daily standup report for each "
                "team member based on recent activity and current task assignments. "
                "Return valid JSON only."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Generate standup from this data:\n\n{context}\n\n"
                "Return JSON with this exact structure:\n"
                '{\n'
                '  "date": "today\'s date",\n'
                '  "standups": [\n'
                '    {\n'
                '      "member": "member name",\n'
                '      "did": ["completed or progressed items"],\n'
                '      "doing": ["currently working on"],\n'
                '      "blocked": ["blockers or issues"]\n'
                '    }\n'
                '  ],\n'
                '  "team_summary": "brief overall team status"\n'
                '}'
            ),
        },
    ]
    content = await gradient.chat_completion(messages, max_tokens=2048, temperature=0.3)
    return _parse_json(content, {"date": "", "standups": [], "team_summary": "No data"})


async def generate_digest(activities: list[dict], tasks: list[dict]) -> dict:
    context = json.dumps({"recent_activities": activities, "current_tasks": tasks}, indent=2)
    messages = [
        {
            "role": "system",
            "content": (
                "You are a project management AI. Generate a daily digest summarizing "
                "project progress. Return valid JSON only."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Generate a project digest from this data:\n\n{context}\n\n"
                "Return JSON with this exact structure:\n"
                '{\n'
                '  "summary": "brief overall summary",\n'
                '  "moved": ["tasks that made progress"],\n'
                '  "stuck": ["tasks that seem stuck or blocked"],\n'
                '  "at_risk": ["tasks at risk of missing deadlines or having issues"]\n'
                '}'
            ),
        },
    ]
    content = await gradient.chat_completion(messages, max_tokens=2048, temperature=0.3)
    return _parse_json(content, {"summary": "No data available", "moved": [], "stuck": [], "at_risk": []})


async def generate_pulse_insights(
    pulse_data: list[dict], completed_tasks: list[dict]
) -> dict:
    """AI insights from mood/energy pulse data correlated with task completion."""
    context = json.dumps(
        {"pulse_history": pulse_data, "completed_tasks": completed_tasks},
        indent=2,
    )
    messages = [
        {
            "role": "system",
            "content": (
                "You are a personal productivity coach AI. Analyze the user's daily "
                "mood and energy pulse data alongside their task completion history. "
                "Find patterns, correlations, and give actionable advice. "
                "Be warm and encouraging. Return valid JSON only."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Analyze this pulse and productivity data:\n\n{context}\n\n"
                "Return JSON with this exact structure:\n"
                '{\n'
                '  "insights": "2-3 sentence overall summary of patterns",\n'
                '  "patterns": [\n'
                '    {\n'
                '      "observation": "what you noticed",\n'
                '      "advice": "actionable recommendation"\n'
                '    }\n'
                '  ],\n'
                '  "energy_trend": "rising|stable|declining",\n'
                '  "mood_trend": "rising|stable|declining",\n'
                '  "best_day": "day of week when most productive",\n'
                '  "burnout_risk": "low|medium|high"\n'
                '}'
            ),
        },
    ]
    content = await gradient.chat_completion(messages, max_tokens=2048, temperature=0.3)
    return _parse_json(content, {
        "insights": "Not enough data yet.",
        "patterns": [],
        "energy_trend": "stable",
        "mood_trend": "stable",
        "best_day": "unknown",
        "burnout_risk": "low",
    })
