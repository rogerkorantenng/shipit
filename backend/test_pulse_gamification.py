#!/usr/bin/env python3
"""Comprehensive endpoint tests for Pulse, Gamification, and Join Code features."""

import httpx
import asyncio
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
        report("GET /api/health", r.status_code == 200 and r.json().get("status") == "ok", f"{r.status_code}")

        # ========== 2. Auth — create test users ==========
        print("\n=== Auth ===")
        r = await c.post(f"{BASE}/auth/enter", json={"name": "PulseTestUser"})
        report("Create user PulseTestUser", r.status_code == 200 and "id" in r.json(), f"{r.status_code} {r.text[:100]}")
        user = r.json()
        headers = {"X-User-Id": str(user["id"])}

        r = await c.post(f"{BASE}/auth/enter", json={"name": "PulseTestUser2"})
        report("Create user PulseTestUser2", r.status_code == 200, f"{r.status_code}")
        user2 = r.json()
        headers2 = {"X-User-Id": str(user2["id"])}

        # ========== 3. Create Project ==========
        print("\n=== Project Setup ===")
        r = await c.post(f"{BASE}/projects/", json={"name": "Pulse Test Project", "description": "Testing pulse"}, headers=headers)
        report("Create project", r.status_code == 200 and "id" in r.json(), f"{r.status_code} {r.text[:100]}")
        project_id = r.json()["id"]

        # Check join_code is returned
        join_code = r.json().get("join_code")
        report("Project has join_code", join_code is not None and len(join_code) > 0, f"join_code={join_code}")

        # ========== 4. Join by Code ==========
        print("\n=== Join by Code ===")
        r = await c.post(f"{BASE}/projects/join", json={"join_code": join_code}, headers=headers2)
        report("Join by code", r.status_code == 200 and r.json().get("ok") is True, f"{r.status_code} {r.text[:200]}")
        report("Join returns project_id", r.json().get("project_id") == project_id, f"got {r.json().get('project_id')}")

        # Join again (should succeed with "already member")
        r = await c.post(f"{BASE}/projects/join", json={"join_code": join_code}, headers=headers2)
        report("Join again (idempotent)", r.status_code == 200 and "Already a member" in r.json().get("message", ""), f"{r.status_code} {r.text[:200]}")

        # Invalid join code
        r = await c.post(f"{BASE}/projects/join", json={"join_code": "XXXXXXXX"}, headers=headers2)
        report("Invalid join code → 404", r.status_code == 404, f"{r.status_code}")

        # ========== 5. Pulse — Log ==========
        print("\n=== Pulse ===")
        r = await c.post(f"{BASE}/projects/{project_id}/pulse", json={"energy": 4, "mood": 5, "note": "Feeling great!"}, headers=headers)
        report("Log pulse", r.status_code == 200, f"{r.status_code} {r.text[:200]}")
        if r.status_code == 200:
            pulse = r.json()
            report("Pulse has energy=4", pulse.get("energy") == 4, f"got {pulse.get('energy')}")
            report("Pulse has mood=5", pulse.get("mood") == 5, f"got {pulse.get('mood')}")
            report("Pulse has note", pulse.get("note") == "Feeling great!", f"got {pulse.get('note')}")
            report("Pulse has user_name", pulse.get("user_name") == "PulseTestUser", f"got {pulse.get('user_name')}")

        # Log pulse user 2
        r = await c.post(f"{BASE}/projects/{project_id}/pulse", json={"energy": 2, "mood": 3}, headers=headers2)
        report("Log pulse user 2", r.status_code == 200, f"{r.status_code}")

        # Upsert — log again same user same day
        r = await c.post(f"{BASE}/projects/{project_id}/pulse", json={"energy": 5, "mood": 4, "note": "Updated!"}, headers=headers)
        report("Upsert pulse", r.status_code == 200, f"{r.status_code}")
        if r.status_code == 200:
            pulse = r.json()
            report("Upsert updated energy to 5", pulse.get("energy") == 5, f"got {pulse.get('energy')}")
            report("Upsert updated note", pulse.get("note") == "Updated!", f"got {pulse.get('note')}")

        # ========== 6. Pulse — Get Today ==========
        print("\n=== Pulse Today ===")
        r = await c.get(f"{BASE}/projects/{project_id}/pulse/today", headers=headers)
        report("Get today's pulse", r.status_code == 200, f"{r.status_code}")
        if r.status_code == 200 and r.json():
            report("Today pulse energy=5 (from upsert)", r.json().get("energy") == 5, f"got {r.json().get('energy')}")

        # ========== 7. Pulse — History ==========
        print("\n=== Pulse History ===")
        r = await c.get(f"{BASE}/projects/{project_id}/pulse/history", headers=headers)
        report("Get pulse history", r.status_code == 200 and isinstance(r.json(), list), f"{r.status_code}")
        if r.status_code == 200:
            report("History has entries", len(r.json()) >= 1, f"got {len(r.json())} entries")

        r = await c.get(f"{BASE}/projects/{project_id}/pulse/history?days=7", headers=headers)
        report("Get pulse history with days param", r.status_code == 200, f"{r.status_code}")

        # ========== 8. Pulse — Team ==========
        print("\n=== Pulse Team ===")
        r = await c.get(f"{BASE}/projects/{project_id}/pulse/team", headers=headers)
        report("Get team pulse", r.status_code == 200, f"{r.status_code}")
        if r.status_code == 200:
            team = r.json()
            report("Team has avg_energy", "avg_energy" in team, f"keys: {list(team.keys())}")
            report("Team has avg_mood", "avg_mood" in team, f"keys: {list(team.keys())}")
            report("Team logged_count >= 2", team.get("logged_count", 0) >= 2, f"got {team.get('logged_count')}")
            report("Team has entries list", isinstance(team.get("entries"), list), f"type: {type(team.get('entries'))}")

        # ========== 9. Pulse — Insights (may fail if no AI key, just check endpoint exists) ==========
        print("\n=== Pulse Insights ===")
        r = await c.get(f"{BASE}/projects/{project_id}/pulse/insights", headers=headers)
        report("Get pulse insights (endpoint exists)", r.status_code in (200, 500), f"{r.status_code}")

        # ========== 10. Gamification — Stats (before any task completion) ==========
        print("\n=== Gamification — Stats ===")
        r = await c.get(f"{BASE}/projects/{project_id}/stats", headers=headers)
        report("Get user stats", r.status_code == 200, f"{r.status_code} {r.text[:200]}")
        if r.status_code == 200:
            stats = r.json()
            report("Stats has xp", "xp" in stats, f"keys: {list(stats.keys())}")
            report("Stats has level", "level" in stats, f"keys: {list(stats.keys())}")
            report("Stats xp starts at 0", stats.get("xp") == 0, f"got {stats.get('xp')}")
            report("Stats level starts at 1", stats.get("level") == 1, f"got {stats.get('level')}")
            report("Stats has current_streak", "current_streak" in stats, f"keys: {list(stats.keys())}")
            report("Stats has xp_progress", "xp_progress" in stats, f"keys: {list(stats.keys())}")
            report("Stats has xp_needed", "xp_needed" in stats, f"keys: {list(stats.keys())}")

        # ========== 11. Gamification — Badges ==========
        print("\n=== Gamification — Badges ===")
        r = await c.get(f"{BASE}/projects/{project_id}/stats/badges", headers=headers)
        report("Get badges", r.status_code == 200 and isinstance(r.json(), list), f"{r.status_code}")
        if r.status_code == 200:
            badges = r.json()
            report("Has multiple badge defs", len(badges) >= 10, f"got {len(badges)}")
            first = badges[0] if badges else {}
            report("Badge has id field", "id" in first, f"keys: {list(first.keys())}")
            report("Badge has name field", "name" in first, f"keys: {list(first.keys())}")
            report("Badge has unlocked field", "unlocked" in first, f"keys: {list(first.keys())}")
            # All should be locked initially
            unlocked = [b for b in badges if b.get("unlocked")]
            report("No badges unlocked initially", len(unlocked) == 0, f"got {len(unlocked)} unlocked")

        # ========== 12. Gamification — Leaderboard ==========
        print("\n=== Gamification — Leaderboard ===")
        r = await c.get(f"{BASE}/projects/{project_id}/leaderboard", headers=headers)
        report("Get leaderboard", r.status_code == 200 and isinstance(r.json(), list), f"{r.status_code}")
        if r.status_code == 200:
            lb = r.json()
            report("Leaderboard has members", len(lb) >= 1, f"got {len(lb)}")

        # ========== 13. Create task and complete it → gamification XP ==========
        print("\n=== Task Completion → XP ===")
        r = await c.post(f"{BASE}/projects/{project_id}/tasks", json={
            "title": "XP test task", "priority": "high"
        }, headers=headers)
        report("Create task", r.status_code == 200, f"{r.status_code}")
        task_id = r.json()["id"]

        # Move to done → should award XP
        r = await c.put(f"{BASE}/projects/{project_id}/tasks/{task_id}", json={"status": "done"}, headers=headers)
        report("Complete task (move to done)", r.status_code == 200, f"{r.status_code}")
        if r.status_code == 200:
            result = r.json()
            gam = result.get("gamification")
            report("Response includes gamification data", gam is not None, f"keys: {list(result.keys())}")
            if gam:
                report("Gamification has xp_gained", "xp_gained" in gam, f"keys: {list(gam.keys())}")
                report("XP gained > 0", gam.get("xp_gained", 0) > 0, f"got {gam.get('xp_gained')}")
                report("Has new_badges list", isinstance(gam.get("new_badges"), list), f"type: {type(gam.get('new_badges'))}")
                # first_blood badge should be awarded
                report("First blood badge earned", "first_blood" in gam.get("new_badges", []), f"badges: {gam.get('new_badges')}")

        # Check updated stats
        r = await c.get(f"{BASE}/projects/{project_id}/stats", headers=headers)
        if r.status_code == 200:
            stats = r.json()
            report("Stats XP > 0 after completion", stats.get("xp", 0) > 0, f"xp={stats.get('xp')}")
            report("Stats tasks_completed = 1", stats.get("tasks_completed") == 1, f"got {stats.get('tasks_completed')}")
            report("Stats current_streak >= 1", stats.get("current_streak", 0) >= 1, f"got {stats.get('current_streak')}")
            report("Badges include first_blood", "first_blood" in stats.get("badges", []), f"badges: {stats.get('badges')}")

        # Complete another medium-priority task
        r = await c.post(f"{BASE}/projects/{project_id}/tasks", json={
            "title": "XP test task 2", "priority": "medium"
        }, headers=headers)
        task_id2 = r.json()["id"]
        r = await c.put(f"{BASE}/projects/{project_id}/tasks/{task_id2}", json={"status": "done"}, headers=headers)
        report("Complete second task", r.status_code == 200, f"{r.status_code}")

        r = await c.get(f"{BASE}/projects/{project_id}/stats", headers=headers)
        if r.status_code == 200:
            stats = r.json()
            report("Stats tasks_completed = 2", stats.get("tasks_completed") == 2, f"got {stats.get('tasks_completed')}")

        # ========== 14. Badges after completions ==========
        print("\n=== Badges After Completions ===")
        r = await c.get(f"{BASE}/projects/{project_id}/stats/badges", headers=headers)
        if r.status_code == 200:
            badges = r.json()
            first_blood = next((b for b in badges if b["id"] == "first_blood"), None)
            report("first_blood badge unlocked", first_blood is not None and first_blood.get("unlocked") is True, f"{first_blood}")

        # ========== 15. Leaderboard after XP ==========
        print("\n=== Leaderboard After XP ===")
        r = await c.get(f"{BASE}/projects/{project_id}/leaderboard", headers=headers)
        if r.status_code == 200:
            lb = r.json()
            # User 1 should have more XP
            if len(lb) >= 2:
                report("Leaderboard sorted by XP (desc)", lb[0]["xp"] >= lb[1]["xp"], f"{lb[0]['xp']} vs {lb[1]['xp']}")
            top = lb[0] if lb else {}
            report("Top user is PulseTestUser", top.get("user_name") == "PulseTestUser", f"got {top.get('user_name')}")

        # ========== 16. Pulse validation ==========
        print("\n=== Pulse Validation ===")
        r = await c.post(f"{BASE}/projects/{project_id}/pulse", json={"energy": 0, "mood": 3}, headers=headers)
        report("Energy < 1 rejected", r.status_code == 400, f"{r.status_code}")

        r = await c.post(f"{BASE}/projects/{project_id}/pulse", json={"energy": 6, "mood": 3}, headers=headers)
        report("Energy > 5 rejected", r.status_code == 400, f"{r.status_code}")

        r = await c.post(f"{BASE}/projects/{project_id}/pulse", json={"energy": 3, "mood": 0}, headers=headers)
        report("Mood < 1 rejected", r.status_code == 400, f"{r.status_code}")

        r = await c.post(f"{BASE}/projects/{project_id}/pulse", json={"energy": 3, "mood": 6}, headers=headers)
        report("Mood > 5 rejected", r.status_code == 400, f"{r.status_code}")

        # ========== 17. Non-member access denied ==========
        print("\n=== Access Control ===")
        r = await c.post(f"{BASE}/auth/enter", json={"name": "OutsiderUser"})
        outsider = r.json()
        outsider_headers = {"X-User-Id": str(outsider["id"])}

        r = await c.post(f"{BASE}/projects/{project_id}/pulse", json={"energy": 3, "mood": 3}, headers=outsider_headers)
        report("Non-member can't log pulse", r.status_code == 404, f"{r.status_code}")

        r = await c.get(f"{BASE}/projects/{project_id}/pulse/today", headers=outsider_headers)
        report("Non-member can't get pulse today", r.status_code == 404, f"{r.status_code}")

        r = await c.get(f"{BASE}/projects/{project_id}/stats", headers=outsider_headers)
        report("Non-member can't get stats", r.status_code == 404, f"{r.status_code}")

        r = await c.get(f"{BASE}/projects/{project_id}/leaderboard", headers=outsider_headers)
        report("Non-member can't get leaderboard", r.status_code == 404, f"{r.status_code}")

        # ========== 18. Project detail includes join_code ==========
        print("\n=== Project Detail ===")
        r = await c.get(f"{BASE}/projects/{project_id}", headers=headers)
        report("Project detail has join_code", "join_code" in r.json(), f"keys: {list(r.json().keys())}")

        # ========== 19. Members after join ==========
        print("\n=== Members After Join ===")
        r = await c.get(f"{BASE}/projects/{project_id}/members", headers=headers)
        report("Members list", r.status_code == 200, f"{r.status_code}")
        if r.status_code == 200:
            members = r.json()
            names = [m["name"] for m in members]
            report("PulseTestUser in members", "PulseTestUser" in names, f"names: {names}")
            report("PulseTestUser2 in members (joined by code)", "PulseTestUser2" in names, f"names: {names}")

        # ========== Summary ==========
        print("\n" + "=" * 50)
        print(f"TOTAL: {PASS + FAIL} | PASS: {PASS} | FAIL: {FAIL}")
        print("=" * 50)

        if FAIL > 0:
            print("\nFailed tests:")
            for line in RESULTS:
                if "[FAIL]" in line:
                    print(line)
            sys.exit(1)
        else:
            print("\nAll tests passed!")


if __name__ == "__main__":
    asyncio.run(main())
