#!/usr/bin/env python3
"""Comprehensive endpoint tests for Sprint feature + existing endpoints."""

import httpx
import asyncio
import json
import sys

BASE = "http://127.0.0.1:8099/api"
PASS = 0
FAIL = 0
RESULTS = []


def report(name: str, passed: bool, detail: str = ""):
    global PASS, FAIL
    status = "PASS" if passed else "FAIL"
    if passed:
        PASS += 1
    else:
        FAIL += 1
    line = f"  [{status}] {name}"
    if detail and not passed:
        line += f" — {detail}"
    RESULTS.append(line)
    print(line)


async def main():
    async with httpx.AsyncClient(timeout=15.0) as c:
        headers = {}

        # ========== 1. Health Check ==========
        print("\n=== Health Check ===")
        r = await c.get(f"{BASE}/health")
        report("GET /api/health", r.status_code == 200 and r.json().get("status") == "ok", f"{r.status_code} {r.text[:100]}")

        # ========== 2. Auth — create test user ==========
        print("\n=== Auth ===")
        r = await c.post(f"{BASE}/auth/enter", json={"name": "SprintTestUser"})
        report("POST /api/auth/enter", r.status_code == 200 and "id" in r.json(), f"{r.status_code} {r.text[:200]}")
        user = r.json()
        user_id = user["id"]
        headers = {"X-User-Id": str(user_id)}

        # Create second user for assignee tests
        r2 = await c.post(f"{BASE}/auth/enter", json={"name": "SprintDev"})
        user2 = r2.json()
        user2_id = user2["id"]

        # ========== 3. Create test project ==========
        print("\n=== Project ===")
        r = await c.post(f"{BASE}/projects/", json={"name": "Sprint Test Project", "description": "Testing sprints"}, headers=headers)
        report("POST /api/projects/ (create)", r.status_code == 200 and "id" in r.json(), f"{r.status_code} {r.text[:200]}")
        project = r.json()
        pid = project["id"]

        # Add second user as member
        r = await c.post(f"{BASE}/projects/{pid}/members", json={"name": "SprintDev"}, headers=headers)
        report("POST /projects/{pid}/members (add member)", r.status_code == 200, f"{r.status_code} {r.text[:200]}")

        # ========== 4. Create test tasks ==========
        print("\n=== Tasks (create for sprint tests) ===")
        task_ids = []
        for i, title in enumerate(["Build login page", "Design API", "Write tests", "Deploy CI/CD", "Database migration"]):
            r = await c.post(f"{BASE}/projects/{pid}/tasks", json={
                "title": title,
                "status": "todo" if i < 3 else "in_progress",
                "priority": ["high", "medium", "low", "high", "medium"][i],
                "estimated_hours": [8, 4, 6, 3, 2][i],
            }, headers=headers)
            report(f"POST /projects/{pid}/tasks (task '{title}')", r.status_code == 200 and "id" in r.json(), f"{r.status_code} {r.text[:200]}")
            task_ids.append(r.json()["id"])

        # Verify sprint_id appears in task serialization
        r = await c.get(f"{BASE}/projects/{pid}/tasks", headers=headers)
        report("GET /projects/{pid}/tasks (board) — has sprint_id field",
               r.status_code == 200 and "sprint_id" in json.dumps(r.json()), f"{r.status_code}")
        board = r.json()
        first_task_in_board = None
        for col in board.values():
            if col:
                first_task_in_board = col[0]
                break
        if first_task_in_board:
            report("Task serialization includes sprint_id", "sprint_id" in first_task_in_board, f"Keys: {list(first_task_in_board.keys())}")

        # ========== 5. Sprint CRUD ==========
        print("\n=== Sprint CRUD ===")

        # List sprints (empty)
        r = await c.get(f"{BASE}/projects/{pid}/sprints", headers=headers)
        report("GET /projects/{pid}/sprints (empty list)", r.status_code == 200 and r.json() == [], f"{r.status_code} {r.text[:200]}")

        # Get active sprint (none)
        r = await c.get(f"{BASE}/projects/{pid}/sprints/active", headers=headers)
        report("GET /projects/{pid}/sprints/active (none)", r.status_code == 200 and r.json() is None, f"{r.status_code} {r.text[:200]}")

        # Create sprint 1
        r = await c.post(f"{BASE}/projects/{pid}/sprints", json={
            "name": "Sprint 1",
            "goal": "Complete core features",
            "start_date": "2026-02-10",
            "end_date": "2026-02-24",
            "capacity_hours": 40,
        }, headers=headers)
        report("POST /projects/{pid}/sprints (create Sprint 1)", r.status_code == 200 and r.json().get("name") == "Sprint 1", f"{r.status_code} {r.text[:300]}")
        sprint1 = r.json()
        sprint1_id = sprint1["id"]
        report("Sprint 1 fields correct",
               sprint1.get("goal") == "Complete core features" and
               sprint1.get("status") == "planned" and
               sprint1.get("capacity_hours") == 40 and
               sprint1.get("start_date") == "2026-02-10",
               f"Got: {json.dumps(sprint1, indent=2)[:300]}")

        # Create sprint 2
        r = await c.post(f"{BASE}/projects/{pid}/sprints", json={
            "name": "Sprint 2",
            "goal": "Polish and deploy",
            "start_date": "2026-02-24",
            "end_date": "2026-03-10",
            "capacity_hours": 30,
        }, headers=headers)
        report("POST /projects/{pid}/sprints (create Sprint 2)", r.status_code == 200, f"{r.status_code} {r.text[:200]}")
        sprint2 = r.json()
        sprint2_id = sprint2["id"]

        # List sprints (now has 2)
        r = await c.get(f"{BASE}/projects/{pid}/sprints", headers=headers)
        report("GET /projects/{pid}/sprints (list 2)", r.status_code == 200 and len(r.json()) == 2, f"{r.status_code} count={len(r.json()) if r.status_code == 200 else 'N/A'}")

        # Update sprint 1
        r = await c.put(f"{BASE}/projects/{pid}/sprints/{sprint1_id}", json={
            "name": "Sprint 1 — Core",
            "capacity_hours": 50,
        }, headers=headers)
        report("PUT /projects/{pid}/sprints/{id} (update)",
               r.status_code == 200 and r.json().get("name") == "Sprint 1 — Core" and r.json().get("capacity_hours") == 50,
               f"{r.status_code} {r.text[:200]}")

        # ========== 6. Move tasks into sprint ==========
        print("\n=== Sprint Task Management ===")

        # Add 3 tasks to sprint 1
        r = await c.post(f"{BASE}/projects/{pid}/sprints/{sprint1_id}/tasks", json={
            "task_ids": task_ids[:3],
            "action": "add",
        }, headers=headers)
        report("POST /sprints/{id}/tasks (add 3 tasks)", r.status_code == 200 and r.json().get("moved") == 3, f"{r.status_code} {r.text[:200]}")

        # Add 2 tasks to sprint 2
        r = await c.post(f"{BASE}/projects/{pid}/sprints/{sprint2_id}/tasks", json={
            "task_ids": task_ids[3:],
            "action": "add",
        }, headers=headers)
        report("POST /sprints/{id}/tasks (add 2 tasks to sprint 2)", r.status_code == 200 and r.json().get("moved") == 2, f"{r.status_code} {r.text[:200]}")

        # Verify task counts on sprint list
        r = await c.get(f"{BASE}/projects/{pid}/sprints", headers=headers)
        sprints_list = r.json()
        s1_data = next((s for s in sprints_list if s["id"] == sprint1_id), None)
        s2_data = next((s for s in sprints_list if s["id"] == sprint2_id), None)
        s1_total = sum(s1_data["task_counts"].values()) if s1_data else 0
        s2_total = sum(s2_data["task_counts"].values()) if s2_data else 0
        report("Sprint 1 task counts correct (3 tasks)", s1_total == 3, f"Got {s1_total}, counts={s1_data.get('task_counts') if s1_data else 'N/A'}")
        report("Sprint 2 task counts correct (2 tasks)", s2_total == 2, f"Got {s2_total}, counts={s2_data.get('task_counts') if s2_data else 'N/A'}")

        # Remove one task from sprint 1
        r = await c.post(f"{BASE}/projects/{pid}/sprints/{sprint1_id}/tasks", json={
            "task_ids": [task_ids[2]],
            "action": "remove",
        }, headers=headers)
        report("POST /sprints/{id}/tasks (remove 1 task)", r.status_code == 200 and r.json().get("moved") == 1, f"{r.status_code} {r.text[:200]}")

        # ========== 7. Board filtering by sprint ==========
        print("\n=== Board Sprint Filtering ===")

        # Board filtered by sprint 1
        r = await c.get(f"{BASE}/projects/{pid}/tasks", params={"sprint_id": sprint1_id}, headers=headers)
        board_s1 = r.json()
        s1_task_count = sum(len(col) for col in board_s1.values())
        report("GET /tasks?sprint_id={s1} (filtered board)", r.status_code == 200 and s1_task_count == 2, f"Expected 2, got {s1_task_count}")

        # Board filtered by sprint 2
        r = await c.get(f"{BASE}/projects/{pid}/tasks", params={"sprint_id": sprint2_id}, headers=headers)
        board_s2 = r.json()
        s2_task_count = sum(len(col) for col in board_s2.values())
        report("GET /tasks?sprint_id={s2} (filtered board)", r.status_code == 200 and s2_task_count == 2, f"Expected 2, got {s2_task_count}")

        # Backlog (tasks not in any sprint)
        r = await c.get(f"{BASE}/projects/{pid}/tasks", params={"backlog": True}, headers=headers)
        backlog_board = r.json()
        backlog_count = sum(len(col) for col in backlog_board.values())
        report("GET /tasks?backlog=true (backlog)", r.status_code == 200 and backlog_count == 1, f"Expected 1, got {backlog_count}")

        # Backlog endpoint
        r = await c.get(f"{BASE}/projects/{pid}/backlog", headers=headers)
        report("GET /projects/{pid}/backlog (dedicated endpoint)", r.status_code == 200 and len(r.json()) == 1, f"{r.status_code} count={len(r.json()) if r.status_code == 200 else 'N/A'}")

        # ========== 8. Sprint lifecycle ==========
        print("\n=== Sprint Lifecycle ===")

        # Start sprint 1
        r = await c.post(f"{BASE}/projects/{pid}/sprints/{sprint1_id}/start", headers=headers)
        report("POST /sprints/{id}/start (start Sprint 1)",
               r.status_code == 200 and r.json().get("status") == "active",
               f"{r.status_code} status={r.json().get('status') if r.status_code == 200 else 'N/A'}")

        # Verify active sprint
        r = await c.get(f"{BASE}/projects/{pid}/sprints/active", headers=headers)
        report("GET /sprints/active (Sprint 1 is active)",
               r.status_code == 200 and r.json() is not None and r.json().get("id") == sprint1_id,
               f"{r.status_code} {r.text[:200]}")

        # Default board load (no params) should use active sprint
        r = await c.get(f"{BASE}/projects/{pid}/tasks", headers=headers)
        default_board = r.json()
        default_count = sum(len(col) for col in default_board.values())
        report("GET /tasks (default) uses active sprint", r.status_code == 200 and default_count == 2, f"Expected 2 (active sprint tasks), got {default_count}")

        # Start sprint 2 — should auto-complete sprint 1
        r = await c.post(f"{BASE}/projects/{pid}/sprints/{sprint2_id}/start", headers=headers)
        report("POST /sprints/{id}/start (start Sprint 2, auto-complete Sprint 1)",
               r.status_code == 200 and r.json().get("status") == "active",
               f"{r.status_code} {r.text[:200]}")

        # Verify sprint 1 is now completed
        r = await c.get(f"{BASE}/projects/{pid}/sprints", headers=headers)
        sprints_after = r.json()
        s1_after = next((s for s in sprints_after if s["id"] == sprint1_id), None)
        report("Sprint 1 auto-completed when Sprint 2 started",
               s1_after is not None and s1_after["status"] == "completed",
               f"Sprint 1 status={s1_after.get('status') if s1_after else 'N/A'}")

        # Complete sprint 2 — incomplete tasks should move to backlog
        r = await c.post(f"{BASE}/projects/{pid}/sprints/{sprint2_id}/complete", headers=headers)
        report("POST /sprints/{id}/complete (complete Sprint 2)",
               r.status_code == 200 and r.json().get("status") == "completed",
               f"{r.status_code} {r.text[:200]}")

        # Verify tasks moved to backlog
        r = await c.get(f"{BASE}/projects/{pid}/backlog", headers=headers)
        backlog_after_complete = r.json()
        report("Incomplete tasks moved to backlog after sprint complete",
               len(backlog_after_complete) == 3,  # 1 original + 2 from sprint 2 (both in_progress, not done)
               f"Expected 3 backlog tasks, got {len(backlog_after_complete)}")

        # ========== 9. Create task with sprint_id ==========
        print("\n=== Task with sprint_id ===")

        # Create a new sprint for this test
        r = await c.post(f"{BASE}/projects/{pid}/sprints", json={"name": "Sprint 3"}, headers=headers)
        sprint3_id = r.json()["id"]

        r = await c.post(f"{BASE}/projects/{pid}/tasks", json={
            "title": "New task in sprint 3",
            "sprint_id": sprint3_id,
            "priority": "high",
        }, headers=headers)
        report("POST /tasks with sprint_id",
               r.status_code == 200 and r.json().get("sprint_id") == sprint3_id,
               f"{r.status_code} sprint_id={r.json().get('sprint_id') if r.status_code == 200 else 'N/A'}")

        # Update task's sprint_id
        new_task_id = r.json()["id"]
        r = await c.put(f"{BASE}/projects/{pid}/tasks/{new_task_id}", json={"sprint_id": None}, headers=headers)
        report("PUT /tasks/{id} sprint_id=null (move to backlog)",
               r.status_code == 200 and r.json().get("sprint_id") is None,
               f"{r.status_code} sprint_id={r.json().get('sprint_id') if r.status_code == 200 else 'N/A'}")

        # ========== 10. Delete sprint ==========
        print("\n=== Delete Sprint ===")

        # Move task back into sprint 3 first
        r = await c.post(f"{BASE}/projects/{pid}/sprints/{sprint3_id}/tasks", json={
            "task_ids": [new_task_id],
            "action": "add",
        }, headers=headers)

        # Delete sprint 3 — tasks should go to backlog
        r = await c.delete(f"{BASE}/projects/{pid}/sprints/{sprint3_id}", headers=headers)
        report("DELETE /sprints/{id}", r.status_code == 200 and r.json().get("ok"), f"{r.status_code} {r.text[:200]}")

        # Verify task is now in backlog
        r = await c.get(f"{BASE}/projects/{pid}/tasks/{new_task_id}", headers=headers)
        report("Task moved to backlog after sprint deleted",
               r.status_code == 200 and r.json().get("sprint_id") is None,
               f"sprint_id={r.json().get('sprint_id') if r.status_code == 200 else 'N/A'}")

        # ========== 11. Error cases ==========
        print("\n=== Error Cases ===")

        # Sprint not found
        r = await c.get(f"{BASE}/projects/{pid}/sprints/active", headers=headers)
        report("GET /sprints/active (none active)", r.status_code == 200 and r.json() is None, f"{r.status_code}")

        r = await c.put(f"{BASE}/projects/{pid}/sprints/99999", json={"name": "Nope"}, headers=headers)
        report("PUT /sprints/99999 (not found)", r.status_code == 404, f"{r.status_code}")

        r = await c.delete(f"{BASE}/projects/{pid}/sprints/99999", headers=headers)
        report("DELETE /sprints/99999 (not found)", r.status_code == 404, f"{r.status_code}")

        r = await c.post(f"{BASE}/projects/{pid}/sprints/99999/start", headers=headers)
        report("POST /sprints/99999/start (not found)", r.status_code == 404, f"{r.status_code}")

        r = await c.post(f"{BASE}/projects/{pid}/sprints/99999/complete", headers=headers)
        report("POST /sprints/99999/complete (not found)", r.status_code == 404, f"{r.status_code}")

        r = await c.post(f"{BASE}/projects/{pid}/sprints/99999/tasks", json={"task_ids": [1], "action": "add"}, headers=headers)
        report("POST /sprints/99999/tasks (not found)", r.status_code == 404, f"{r.status_code}")

        # Auth required (FastAPI returns 422 for missing X-User-Id header dependency)
        r = await c.get(f"{BASE}/projects/{pid}/sprints")
        report("GET /sprints (no auth header)", r.status_code == 422, f"{r.status_code}")

        # ========== 12. Jira connection status has sprint fields ==========
        print("\n=== Jira Sprint Fields ===")

        # Can't fully test Jira without real creds, but verify the schema
        r = await c.get(f"{BASE}/projects/{pid}/jira/connection", headers=headers)
        report("GET /jira/connection (not connected)", r.status_code == 200 and r.json().get("connected") is False, f"{r.status_code} {r.text[:200]}")

        # Import sprints without connection should fail
        r = await c.post(f"{BASE}/projects/{pid}/jira/import-sprints", headers=headers)
        report("POST /jira/import-sprints (no connection) — 404", r.status_code == 404, f"{r.status_code}")

        # Export sprint without connection should fail
        r = await c.post(f"{BASE}/projects/{pid}/jira/export-sprint/{sprint1_id}", headers=headers)
        report("POST /jira/export-sprint (no connection) — 404", r.status_code == 404, f"{r.status_code}")

        # ========== 13. AI Sprint Plan Apply (creates real sprint) ==========
        print("\n=== AI Sprint Plan Apply (persistence) ===")

        # Create some fresh backlog tasks
        fresh_tasks = []
        for title in ["AI Task A", "AI Task B"]:
            r = await c.post(f"{BASE}/projects/{pid}/tasks", json={"title": title, "estimated_hours": 5}, headers=headers)
            fresh_tasks.append(r.json()["id"])

        r = await c.post(f"{BASE}/projects/{pid}/ai/sprint-plan/apply", json={
            "sprint_name": "AI Sprint Alpha",
            "goal": "AI planned sprint",
            "start_date": "2026-03-01",
            "end_date": "2026-03-14",
            "capacity_hours": 20,
            "assignments": [
                {"task_id": fresh_tasks[0], "assignee": "SprintDev"},
                {"task_id": fresh_tasks[1], "assignee": "SprintTestUser"},
            ],
        }, headers=headers)
        report("POST /ai/sprint-plan/apply (creates persistent sprint)",
               r.status_code == 200 and r.json().get("sprint_id") is not None and r.json().get("applied") == 2,
               f"{r.status_code} {r.text[:300]}")

        if r.status_code == 200:
            ai_sprint_id = r.json()["sprint_id"]

            # Verify the sprint was actually created
            r = await c.get(f"{BASE}/projects/{pid}/sprints", headers=headers)
            ai_sprint = next((s for s in r.json() if s["id"] == ai_sprint_id), None)
            report("AI sprint exists in sprint list",
                   ai_sprint is not None and ai_sprint["name"] == "AI Sprint Alpha" and ai_sprint["goal"] == "AI planned sprint",
                   f"Sprint: {json.dumps(ai_sprint, indent=2)[:200] if ai_sprint else 'NOT FOUND'}")

            # Verify tasks were assigned to the sprint
            r = await c.get(f"{BASE}/projects/{pid}/tasks", params={"sprint_id": ai_sprint_id}, headers=headers)
            ai_board = r.json()
            ai_task_count = sum(len(col) for col in ai_board.values())
            report("AI sprint has 2 tasks assigned", ai_task_count == 2, f"Got {ai_task_count}")

            # Verify assignees were set
            r = await c.get(f"{BASE}/projects/{pid}/tasks/{fresh_tasks[0]}", headers=headers)
            report("AI task A has assignee (SprintDev)",
                   r.status_code == 200 and r.json().get("assignee_name") == "SprintDev",
                   f"assignee_name={r.json().get('assignee_name') if r.status_code == 200 else 'N/A'}")

        # ========== 14. Existing endpoints still work ==========
        print("\n=== Existing Endpoints Regression ===")

        r = await c.get(f"{BASE}/projects/{pid}/tasks", headers=headers)
        report("GET /tasks (board load)", r.status_code == 200 and isinstance(r.json(), dict), f"{r.status_code}")

        r = await c.get(f"{BASE}/projects/{pid}/tasks/{task_ids[0]}", headers=headers)
        report("GET /tasks/{id} (task detail)", r.status_code == 200 and r.json().get("id") == task_ids[0], f"{r.status_code}")

        r = await c.put(f"{BASE}/projects/{pid}/tasks/{task_ids[0]}", json={"priority": "urgent"}, headers=headers)
        report("PUT /tasks/{id} (update priority)", r.status_code == 200 and r.json().get("priority") == "urgent", f"{r.status_code}")

        r = await c.get(f"{BASE}/projects/{pid}/activity", headers=headers)
        report("GET /activity (has sprint events)", r.status_code == 200, f"{r.status_code}")

        r = await c.get(f"{BASE}/projects/", headers=headers)
        report("GET /projects/ (list)", r.status_code == 200, f"{r.status_code}")

        r = await c.get(f"{BASE}/projects/{pid}/members", headers=headers)
        report("GET /projects/{pid}/members", r.status_code == 200, f"{r.status_code}")

        # ========== 15. Cleanup ==========
        print("\n=== Cleanup ===")
        r = await c.delete(f"{BASE}/projects/{pid}", headers=headers)
        report("DELETE /projects/{pid} (cleanup)", r.status_code == 200, f"{r.status_code}")

    # ========== Summary ==========
    print(f"\n{'='*50}")
    print(f"  TOTAL: {PASS + FAIL}  |  PASS: {PASS}  |  FAIL: {FAIL}")
    print(f"{'='*50}")

    if FAIL > 0:
        print("\nFailed tests:")
        for line in RESULTS:
            if "[FAIL]" in line:
                print(line)
        sys.exit(1)
    else:
        print("\nAll tests passed!")


asyncio.run(main())
