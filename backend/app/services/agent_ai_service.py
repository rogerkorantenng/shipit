"""Agent-specific AI prompt functions using Gradient service."""

import json
import logging
import re
from typing import Any

from app.services.gradient_service import gradient

logger = logging.getLogger(__name__)


def _parse_json(content: str, fallback: Any = None) -> Any:
    """Parse JSON from AI response, stripping markdown fences."""
    if fallback is None:
        fallback = {}
    cleaned = re.sub(r"```(?:json)?\s*", "", content).strip().rstrip("`")
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        return fallback


def _validate_keys(data: dict, required_keys: list[str], fallback: dict) -> dict:
    """Ensure all required keys exist in the parsed response, filling from fallback."""
    if not isinstance(data, dict):
        return fallback
    for key in required_keys:
        if key not in data:
            data[key] = fallback.get(key)
    return data


async def _ai_call(system: str, user: str, max_tokens: int = 2048) -> str:
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    try:
        return await gradient.chat_completion(
            messages=messages,
            model="claude-haiku-4-5",
            max_tokens=max_tokens,
            temperature=0.3,
        )
    except Exception:
        logger.exception("AI call failed")
        raise


async def analyze_requirements(ticket_data: dict) -> dict:
    """Analyze a Jira ticket for requirements, stories, complexity."""
    fallback = {
        "summary": ticket_data.get("title", ""),
        "stories": [],
        "complexity": "medium",
        "estimated_effort_hours": 4,
        "tags": [],
        "related_topics": [],
    }
    system = (
        "You are a product intelligence agent. Analyze the ticket and extract "
        "structured requirements. You MUST return valid JSON with these exact keys: "
        "summary (string), stories (list of objects with title, description, "
        "acceptance_criteria), complexity (one of: low, medium, high), "
        "estimated_effort_hours (number), tags (list of strings), "
        "related_topics (list of strings). Return ONLY JSON, no other text."
    )
    user = (
        f"Analyze this ticket:\n"
        f"Title: {ticket_data.get('title', '')}\n"
        f"Description: {ticket_data.get('description', '')}\n"
        f"Priority: {ticket_data.get('priority', '')}\n"
        f"Labels: {', '.join(ticket_data.get('labels', []))}"
    )
    try:
        result = await _ai_call(system, user)
        parsed = _parse_json(result, fallback)
        return _validate_keys(parsed, list(fallback.keys()), fallback)
    except Exception:
        logger.warning("AI requirements analysis failed, using fallback")
        return fallback


async def generate_implementation_notes(design_data: dict, ticket_data: dict) -> dict:
    """Generate technical implementation notes from design changes."""
    fallback = {
        "component_specs": [],
        "implementation_steps": [],
        "design_ticket_alignment": "partial",
        "notes": "",
    }
    system = (
        "You are a design-to-code translation agent. Compare design changes with "
        "ticket requirements and generate implementation notes. You MUST return "
        "valid JSON with these exact keys: component_specs (list of objects with "
        "name, css_changes, props), implementation_steps (list of strings), "
        "design_ticket_alignment (one of: matched, mismatched, partial), "
        "notes (string). Return ONLY JSON, no other text."
    )
    user = (
        f"Design data: {json.dumps(design_data, default=str)}\n"
        f"Ticket data: {json.dumps(ticket_data, default=str)}"
    )
    try:
        result = await _ai_call(system, user, max_tokens=3000)
        parsed = _parse_json(result, fallback)
        return _validate_keys(parsed, list(fallback.keys()), fallback)
    except Exception:
        logger.warning("AI implementation notes generation failed, using fallback")
        return fallback


async def generate_boilerplate(requirements: dict, branch_name: str) -> dict:
    """Generate boilerplate code structure from requirements."""
    fallback = {
        "files": [],
        "pr_description": "",
        "suggested_reviewers_criteria": "",
    }
    system = (
        "You are a code scaffolding agent. Generate file structure and boilerplate "
        "based on requirements. You MUST return valid JSON with these exact keys: "
        "files (list of objects with path, content, description), "
        "pr_description (string - markdown PR body), "
        "suggested_reviewers_criteria (string). Return ONLY JSON, no other text."
    )
    user = (
        f"Branch: {branch_name}\n"
        f"Requirements: {json.dumps(requirements, default=str)}"
    )
    try:
        result = await _ai_call(system, user, max_tokens=4000)
        parsed = _parse_json(result, fallback)
        parsed = _validate_keys(parsed, list(fallback.keys()), fallback)
        # Validate files list structure
        validated_files = []
        for f in parsed.get("files", []):
            if isinstance(f, dict) and "path" in f:
                validated_files.append({
                    "path": f["path"],
                    "content": f.get("content", ""),
                    "description": f.get("description", f["path"]),
                })
        parsed["files"] = validated_files
        return parsed
    except Exception:
        logger.warning("AI boilerplate generation failed, using fallback")
        return fallback


async def security_scan(diff_content: str, file_paths: list[str]) -> dict:
    """AI-based security analysis of code changes."""
    fallback = {
        "vulnerabilities": [],
        "overall_risk": "low",
        "passed": True,
        "summary": "Scan completed - unable to perform full analysis",
    }
    system = (
        "You are a security scanning agent. Analyze the code diff for vulnerabilities "
        "including: secrets/credentials, SQL injection, XSS, OWASP top 10, insecure "
        "dependencies, hardcoded passwords, command injection, path traversal. "
        "You MUST return valid JSON with these exact keys: "
        "vulnerabilities (list of objects with severity [critical/high/medium/low], "
        "type, file, line, description, recommendation), "
        "overall_risk (one of: low, medium, high, critical), "
        "passed (boolean - false if any critical or high severity found), "
        "summary (string). Return ONLY JSON, no other text."
    )
    user = f"Files changed: {', '.join(file_paths)}\n\nDiff:\n{diff_content[:8000]}"
    try:
        result = await _ai_call(system, user, max_tokens=3000)
        parsed = _parse_json(result, fallback)
        parsed = _validate_keys(parsed, list(fallback.keys()), fallback)
        # Validate vulnerability structure and enforce passed logic
        validated_vulns = []
        for v in parsed.get("vulnerabilities", []):
            if isinstance(v, dict) and v.get("severity") in ("critical", "high", "medium", "low"):
                validated_vulns.append(v)
        parsed["vulnerabilities"] = validated_vulns
        # Enforce: if any critical/high vulns, passed must be False
        has_critical_or_high = any(
            v.get("severity") in ("critical", "high") for v in validated_vulns
        )
        if has_critical_or_high:
            parsed["passed"] = False
            if parsed.get("overall_risk") == "low":
                parsed["overall_risk"] = "high"
        return parsed
    except Exception:
        logger.warning("AI security scan failed, using conservative fallback")
        # On AI failure, return conservative result (not passed) to be safe
        return {
            "vulnerabilities": [],
            "overall_risk": "unknown",
            "passed": False,
            "summary": "Security scan AI analysis failed - manual review required",
        }


async def generate_test_suggestions(diff_content: str, file_paths: list[str]) -> dict:
    """Generate test suggestions for code changes."""
    fallback = {
        "unit_tests": [],
        "integration_tests": [],
        "edge_cases": [],
        "coverage_gaps": [],
        "priority_order": [],
    }
    system = (
        "You are a test intelligence agent. Analyze code changes and suggest tests. "
        "You MUST return valid JSON with these exact keys: "
        "unit_tests (list of objects with name, description, file, code_hint), "
        "integration_tests (list of objects with name, description), "
        "edge_cases (list of strings), coverage_gaps (list of strings), "
        "priority_order (list of test name strings). Return ONLY JSON, no other text."
    )
    user = f"Files changed: {', '.join(file_paths)}\n\nDiff:\n{diff_content[:8000]}"
    try:
        result = await _ai_call(system, user, max_tokens=3000)
        parsed = _parse_json(result, fallback)
        return _validate_keys(parsed, list(fallback.keys()), fallback)
    except Exception:
        logger.warning("AI test suggestions failed, using fallback")
        return fallback


async def analyze_review_complexity(diff_content: str, file_count: int) -> dict:
    """Analyze PR complexity for reviewer assignment."""
    fallback = {
        "complexity": "medium",
        "risk_areas": [],
        "recommended_expertise": [],
        "estimated_review_minutes": 30,
        "summary": "",
        "auto_merge_eligible": False,
    }
    system = (
        "You are a code review coordination agent. Analyze the PR for complexity, "
        "risk areas, and recommended expertise. You MUST return valid JSON with "
        "these exact keys: complexity (one of: low, medium, high), "
        "risk_areas (list of strings), recommended_expertise (list of strings "
        "like 'backend', 'frontend', 'database', 'security', 'devops'), "
        "estimated_review_minutes (number), summary (string), "
        "auto_merge_eligible (boolean - true only for low complexity with no "
        "risk areas). Return ONLY JSON, no other text."
    )
    user = f"Files changed: {file_count}\n\nDiff:\n{diff_content[:6000]}"
    try:
        result = await _ai_call(system, user)
        parsed = _parse_json(result, fallback)
        parsed = _validate_keys(parsed, list(fallback.keys()), fallback)
        # Validate complexity is valid enum
        if parsed.get("complexity") not in ("low", "medium", "high"):
            parsed["complexity"] = "medium"
        # Enforce auto_merge logic: never auto-merge high complexity
        if parsed.get("complexity") == "high":
            parsed["auto_merge_eligible"] = False
        return parsed
    except Exception:
        logger.warning("AI review complexity analysis failed, using fallback")
        return fallback


async def generate_release_notes(commits: list[dict], prs: list[dict]) -> dict:
    """Generate release notes from commits and PRs."""
    fallback = {
        "version_summary": "",
        "features": [],
        "bugfixes": [],
        "breaking_changes": [],
        "notes": "",
    }
    system = (
        "You are a release notes generator. Create user-facing release notes from "
        "the commit history and PRs. You MUST return valid JSON with these exact keys: "
        "version_summary (string - 1-2 sentence overview), "
        "features (list of strings), bugfixes (list of strings), "
        "breaking_changes (list of strings), notes (string). "
        "Return ONLY JSON, no other text."
    )
    user = (
        f"Commits: {json.dumps(commits[:20], default=str)}\n"
        f"PRs: {json.dumps(prs[:10], default=str)}"
    )
    try:
        result = await _ai_call(system, user)
        parsed = _parse_json(result, fallback)
        return _validate_keys(parsed, list(fallback.keys()), fallback)
    except Exception:
        logger.warning("AI release notes generation failed, using fallback")
        # Build basic release notes from commit messages
        features = [c.get("message", "").split("\n")[0] for c in commits[:10] if c.get("message")]
        return {
            "version_summary": f"Release with {len(commits)} commits",
            "features": features,
            "bugfixes": [],
            "breaking_changes": [],
            "notes": "Auto-generated from commit log (AI analysis unavailable)",
        }


async def analyze_metrics(metrics_data: dict) -> dict:
    """Analyze project metrics and identify insights."""
    fallback = {
        "bottlenecks": [],
        "predictions": {"sprint_completion_pct": 0, "velocity_trend": "stable"},
        "recommendations": [],
        "executive_summary": "",
    }
    system = (
        "You are a project analytics agent. Analyze velocity metrics and identify "
        "insights. You MUST return valid JSON with these exact keys: "
        "bottlenecks (list of objects with area, description, severity), "
        "predictions (object with sprint_completion_pct as number 0-100, "
        "velocity_trend as one of: increasing, stable, decreasing), "
        "recommendations (list of actionable strings), "
        "executive_summary (string - 2-3 sentences). Return ONLY JSON, no other text."
    )
    user = f"Metrics data:\n{json.dumps(metrics_data, default=str)}"
    try:
        result = await _ai_call(system, user)
        parsed = _parse_json(result, fallback)
        parsed = _validate_keys(parsed, list(fallback.keys()), fallback)
        # Validate predictions structure
        predictions = parsed.get("predictions", {})
        if not isinstance(predictions, dict):
            parsed["predictions"] = fallback["predictions"]
        else:
            pct = predictions.get("sprint_completion_pct", 0)
            if not isinstance(pct, (int, float)) or pct < 0 or pct > 100:
                predictions["sprint_completion_pct"] = 0
            trend = predictions.get("velocity_trend", "stable")
            if trend not in ("increasing", "stable", "decreasing"):
                predictions["velocity_trend"] = "stable"
        return parsed
    except Exception:
        logger.warning("AI metrics analysis failed, using fallback")
        # Build basic analysis from raw metrics
        task_dist = metrics_data.get("task_distribution", {})
        total = sum(task_dist.values()) if task_dist else 0
        done = task_dist.get("done", 0)
        completion = round((done / total * 100) if total else 0)
        return {
            "bottlenecks": [],
            "predictions": {
                "sprint_completion_pct": completion,
                "velocity_trend": "stable",
            },
            "recommendations": [],
            "executive_summary": (
                f"Project has {total} tasks total, {done} completed ({completion}%). "
                f"AI analysis unavailable - showing raw metrics."
            ),
        }
