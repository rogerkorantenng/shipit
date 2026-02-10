"""Jira Cloud REST API client — two-way sync between ShipIt and Jira."""

import httpx
from typing import Optional


# ShipIt status ↔ Jira status name mapping
STATUS_TO_JIRA = {
    "todo": "To Do",
    "in_progress": "In Progress",
    "done": "Done",
    "blocked": "Blocked",
}
STATUS_FROM_JIRA = {v.lower(): k for k, v in STATUS_TO_JIRA.items()}

PRIORITY_TO_JIRA = {
    "urgent": "Highest",
    "high": "High",
    "medium": "Medium",
    "low": "Low",
}
PRIORITY_FROM_JIRA = {v.lower(): k for k, v in PRIORITY_TO_JIRA.items()}


SPRINT_STATE_MAP = {
    "future": "planned",
    "active": "active",
    "closed": "completed",
}


class JiraService:
    """Client for Jira Cloud REST API v3 using Basic Auth (email + API token)."""

    def __init__(self, site: str, email: str, api_token: str):
        site = site.strip().rstrip("/")
        self.base_url = f"https://{site}/rest/api/3"
        self.agile_url = f"https://{site}/rest/agile/1.0"
        self.auth = (email, api_token)

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            auth=self.auth,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=30.0,
        )

    async def test_connection(self) -> dict:
        """Test credentials by calling /myself."""
        async with self._client() as client:
            resp = await client.get(f"{self.base_url}/myself")
            resp.raise_for_status()
            return resp.json()

    async def list_projects(self) -> list[dict]:
        """List Jira projects accessible to the user."""
        async with self._client() as client:
            resp = await client.get(f"{self.base_url}/project")
            resp.raise_for_status()
            return resp.json()

    async def create_issue(
        self,
        project_key: str,
        summary: str,
        description: str = "",
        priority: str = "medium",
    ) -> dict:
        """Create a Jira issue. Description uses ADF format."""
        jira_priority = PRIORITY_TO_JIRA.get(priority, "Medium")

        # Atlassian Document Format for description
        adf_body = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": description or "No description"}],
                }
            ],
        }

        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": adf_body,
                "issuetype": {"name": "Task"},
                "priority": {"name": jira_priority},
            }
        }

        async with self._client() as client:
            resp = await client.post(f"{self.base_url}/issue", json=payload)
            resp.raise_for_status()
            return resp.json()

    async def get_issue(self, issue_key: str) -> dict:
        """Get a single Jira issue by key."""
        async with self._client() as client:
            resp = await client.get(f"{self.base_url}/issue/{issue_key}")
            resp.raise_for_status()
            return resp.json()

    async def transition_issue(self, issue_key: str, target_status: str) -> bool:
        """Transition a Jira issue to a target status name. Returns True on success."""
        jira_status = STATUS_TO_JIRA.get(target_status, target_status)

        async with self._client() as client:
            # Get available transitions
            resp = await client.get(f"{self.base_url}/issue/{issue_key}/transitions")
            resp.raise_for_status()
            transitions = resp.json().get("transitions", [])

            # Find matching transition
            target = None
            for t in transitions:
                if t["to"]["name"].lower() == jira_status.lower():
                    target = t
                    break

            if not target:
                return False

            # Execute transition
            resp = await client.post(
                f"{self.base_url}/issue/{issue_key}/transitions",
                json={"transition": {"id": target["id"]}},
            )
            resp.raise_for_status()
            return True

    async def search_issues(
        self, project_key: str, max_results: int = 100
    ) -> list[dict]:
        """Search for issues in a Jira project using JQL (POST endpoint)."""
        jql = f"project = {project_key} ORDER BY created DESC"
        async with self._client() as client:
            resp = await client.post(
                f"{self.base_url}/search/jql",
                json={
                    "jql": jql,
                    "maxResults": max_results,
                    "fields": ["summary", "status", "priority", "description", "sprint"],
                },
            )
            resp.raise_for_status()
            return resp.json().get("issues", [])

    # --- Agile / Sprint API ---

    async def get_boards(self, project_key: str) -> list[dict]:
        """Get Jira boards for a project."""
        async with self._client() as client:
            resp = await client.get(
                f"{self.agile_url}/board",
                params={"projectKeyOrId": project_key},
            )
            resp.raise_for_status()
            return resp.json().get("values", [])

    async def get_sprints(self, board_id: int, state: str = "") -> list[dict]:
        """Get sprints for a board. state can be 'future', 'active', 'closed' or empty for all."""
        params = {}
        if state:
            params["state"] = state
        async with self._client() as client:
            resp = await client.get(
                f"{self.agile_url}/board/{board_id}/sprint",
                params=params,
            )
            resp.raise_for_status()
            return resp.json().get("values", [])

    async def get_sprint_issues(self, sprint_id: int) -> list[dict]:
        """Get issues in a sprint."""
        async with self._client() as client:
            resp = await client.get(
                f"{self.agile_url}/sprint/{sprint_id}/issue",
                params={"maxResults": 200},
            )
            resp.raise_for_status()
            return resp.json().get("issues", [])

    async def move_issues_to_sprint(self, sprint_id: int, issue_keys: list[str]) -> bool:
        """Move issues into a Jira sprint."""
        if not issue_keys:
            return True
        async with self._client() as client:
            resp = await client.post(
                f"{self.agile_url}/sprint/{sprint_id}/issue",
                json={"issues": issue_keys},
            )
            resp.raise_for_status()
            return True

    async def create_sprint(
        self,
        board_id: int,
        name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        goal: str = "",
    ) -> dict:
        """Create a new sprint on a Jira board."""
        payload: dict = {
            "name": name,
            "originBoardId": board_id,
        }
        if start_date:
            payload["startDate"] = start_date
        if end_date:
            payload["endDate"] = end_date
        if goal:
            payload["goal"] = goal

        async with self._client() as client:
            resp = await client.post(
                f"{self.agile_url}/sprint",
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    def parse_jira_sprint_state(state: str) -> str:
        """Convert Jira sprint state to local sprint status."""
        return SPRINT_STATE_MAP.get(state.lower(), "planned")

    @staticmethod
    def parse_jira_status(jira_status_name: str) -> str:
        """Convert a Jira status name to ShipIt status."""
        return STATUS_FROM_JIRA.get(jira_status_name.lower(), "todo")

    @staticmethod
    def parse_jira_priority(jira_priority_name: Optional[str]) -> str:
        """Convert a Jira priority name to ShipIt priority."""
        if not jira_priority_name:
            return "medium"
        return PRIORITY_FROM_JIRA.get(jira_priority_name.lower(), "medium")

    @staticmethod
    def extract_plain_text(adf: Optional[dict]) -> str:
        """Extract plain text from Atlassian Document Format."""
        if not adf or not isinstance(adf, dict):
            return ""
        texts: list[str] = []

        def _walk(node: dict) -> None:
            if node.get("type") == "text":
                texts.append(node.get("text", ""))
            for child in node.get("content", []):
                if isinstance(child, dict):
                    _walk(child)

        _walk(adf)
        return " ".join(texts)
