"""GitLab REST API v4 adapter."""

import logging
from typing import Any, Optional
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)


class GitLabAdapter:
    """Client for GitLab REST API v4."""

    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/api/v4"
        self._headers = {"PRIVATE-TOKEN": token}

    async def _request(
        self, method: str, path: str, **kwargs
    ) -> Any:
        async with httpx.AsyncClient() as client:
            resp = await client.request(
                method,
                f"{self.api_url}{path}",
                headers=self._headers,
                timeout=30.0,
                **kwargs,
            )
            resp.raise_for_status()
            return resp.json() if resp.content else None

    async def test_connection(self) -> dict:
        return await self._request("GET", "/user")

    async def create_issue(
        self,
        project_id: int,
        title: str,
        description: str = "",
        labels: Optional[list[str]] = None,
        assignee_ids: Optional[list[int]] = None,
    ) -> dict:
        data: dict[str, Any] = {"title": title, "description": description}
        if labels:
            data["labels"] = ",".join(labels)
        if assignee_ids:
            data["assignee_ids"] = assignee_ids
        return await self._request(
            "POST", f"/projects/{project_id}/issues", json=data
        )

    async def create_branch(
        self, project_id: int, branch_name: str, ref: str = "main"
    ) -> dict:
        return await self._request(
            "POST",
            f"/projects/{project_id}/repository/branches",
            json={"branch": branch_name, "ref": ref},
        )

    async def create_merge_request(
        self,
        project_id: int,
        source_branch: str,
        target_branch: str = "main",
        title: str = "",
        description: str = "",
        assignee_id: Optional[int] = None,
        reviewer_ids: Optional[list[int]] = None,
    ) -> dict:
        data: dict[str, Any] = {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
            "description": description,
        }
        if assignee_id:
            data["assignee_id"] = assignee_id
        if reviewer_ids:
            data["reviewer_ids"] = reviewer_ids
        return await self._request(
            "POST", f"/projects/{project_id}/merge_requests", json=data
        )

    async def get_mr_diff(self, project_id: int, mr_iid: int) -> list[dict]:
        return await self._request(
            "GET", f"/projects/{project_id}/merge_requests/{mr_iid}/diffs"
        )

    async def add_mr_comment(
        self, project_id: int, mr_iid: int, body: str
    ) -> dict:
        return await self._request(
            "POST",
            f"/projects/{project_id}/merge_requests/{mr_iid}/notes",
            json={"body": body},
        )

    async def merge_mr(self, project_id: int, mr_iid: int) -> dict:
        return await self._request(
            "PUT", f"/projects/{project_id}/merge_requests/{mr_iid}/merge"
        )

    async def get_pipelines(
        self, project_id: int, ref: Optional[str] = None, limit: int = 20
    ) -> list[dict]:
        params: dict[str, Any] = {"per_page": limit}
        if ref:
            params["ref"] = ref
        return await self._request(
            "GET", f"/projects/{project_id}/pipelines", params=params
        )

    async def list_project_members(self, project_id: int) -> list[dict]:
        return await self._request(
            "GET", f"/projects/{project_id}/members/all", params={"per_page": 100}
        )

    async def create_file(
        self,
        project_id: int,
        file_path: str,
        content: str,
        branch: str,
        commit_message: str,
    ) -> dict:
        encoded_path = quote(file_path, safe="")
        return await self._request(
            "POST",
            f"/projects/{project_id}/repository/files/{encoded_path}",
            json={
                "branch": branch,
                "content": content,
                "commit_message": commit_message,
            },
        )

    async def get_commits(
        self, project_id: int, ref_name: Optional[str] = None, limit: int = 20
    ) -> list[dict]:
        params: dict[str, Any] = {"per_page": limit}
        if ref_name:
            params["ref_name"] = ref_name
        return await self._request(
            "GET", f"/projects/{project_id}/repository/commits", params=params
        )

    async def trigger_pipeline(
        self, project_id: int, ref: str = "main", variables: Optional[list[dict]] = None
    ) -> dict:
        data: dict[str, Any] = {"ref": ref}
        if variables:
            data["variables"] = variables
        return await self._request(
            "POST", f"/projects/{project_id}/pipeline", json=data
        )
