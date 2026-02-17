"""
ShipIt Demo Seeder — Uses Playwright to simulate real user interactions
and populate the app with impressive demo data.
"""

import asyncio
from playwright.async_api import async_playwright, Page

BASE = "http://localhost:5173"

# ── Demo data ──────────────────────────────────────────────────────────────

USERS = [
    "Roger Koranteng",
    "Ama Mensah",
    "Kwame Asante",
    "Nana Osei",
    "Efua Darko",
]

PROJECTS = [
    {
        "name": "ShipIt Platform",
        "description": "AI-powered project management with autonomous agents, Jira sync, and real-time collaboration.",
    },
    {
        "name": "Mobile App v2",
        "description": "Next-gen mobile experience with offline mode, push notifications, and biometric auth.",
    },
    {
        "name": "Data Pipeline",
        "description": "Real-time ETL pipeline processing 10M+ events/day with anomaly detection.",
    },
]

TASKS = {
    "ShipIt Platform": [
        {"title": "Set up CI/CD pipeline with GitLab runners", "desc": "Configure .gitlab-ci.yml with build, test, and deploy stages. Include Docker layer caching.", "status": "done", "priority": "high"},
        {"title": "Implement agent event bus architecture", "desc": "In-process asyncio pub/sub system with ring buffer history and correlation IDs for all 8 agents.", "status": "done", "priority": "high"},
        {"title": "Build GitLab adapter for code orchestration", "desc": "REST API v4 client: create branches, MRs, post comments, fetch diffs.", "status": "done", "priority": "high"},
        {"title": "Design agent dashboard UI", "desc": "Grid of agent cards with status indicators, metrics, enable/disable toggles and event log.", "status": "done", "priority": "medium"},
        {"title": "Integrate Figma design sync agent", "desc": "Poll Figma API for design changes, compare with Jira tickets, generate CSS specs.", "status": "in_progress", "priority": "high"},
        {"title": "Add Slack notification delivery", "desc": "SlackNotifierAgent subscribes to SLACK_NOTIFICATION events and delivers via Web API.", "status": "done", "priority": "medium"},
        {"title": "Security scanning on MR diffs", "desc": "AI-powered SAST: detect secrets, SQL injection, XSS, command injection in code.", "status": "in_progress", "priority": "high"},
        {"title": "Implement deployment orchestrator", "desc": "Validate release readiness, trigger CI/CD, generate release notes from commits.", "status": "in_progress", "priority": "high"},
        {"title": "Build analytics insights engine", "desc": "Collect velocity metrics, cycle time, lead time. AI identifies bottlenecks.", "status": "todo", "priority": "medium"},
        {"title": "Add Datadog monitoring integration", "desc": "Query metrics, get monitors, create events. Dual-key auth.", "status": "done", "priority": "medium"},
        {"title": "Implement credential reveal in dashboard", "desc": "Eye toggle to show/hide stored API tokens with masked display.", "status": "done", "priority": "low"},
        {"title": "Write E2E tests for agent pipeline", "desc": "Test full chain: webhook to event bus to agent processing to Slack.", "status": "todo", "priority": "medium"},
        {"title": "Add webhook retry with exponential backoff", "desc": "Failed deliveries retry 3 times with 1s, 5s, 30s delays.", "status": "todo", "priority": "low"},
        {"title": "Optimize AI prompt token usage", "desc": "Switch analysis prompts from Sonnet to Haiku where quality is acceptable.", "status": "blocked", "priority": "medium"},
        {"title": "Add role-based access control", "desc": "Owner, Admin, Member, Viewer roles for agent config and credentials.", "status": "todo", "priority": "high"},
    ],
    "Mobile App v2": [
        {"title": "Set up React Native project scaffold", "desc": "Initialize with Expo, configure TypeScript, set up navigation stack.", "status": "done", "priority": "high"},
        {"title": "Implement biometric authentication", "desc": "FaceID/TouchID login with expo-local-authentication and SecureStore.", "status": "done", "priority": "high"},
        {"title": "Build offline-first task sync engine", "desc": "SQLite local cache with conflict resolution and CRDT merge on reconnect.", "status": "in_progress", "priority": "high"},
        {"title": "Design push notification system", "desc": "Firebase Cloud Messaging for task assignments, mentions, and agent alerts.", "status": "in_progress", "priority": "medium"},
        {"title": "Create task kanban with gestures", "desc": "Swipe-to-complete, long-press drag between columns, 60fps animations.", "status": "in_progress", "priority": "medium"},
        {"title": "Add dark mode theming", "desc": "System-aware theme switching with custom dark palette.", "status": "todo", "priority": "low"},
        {"title": "Implement voice-to-task feature", "desc": "Speech recognition to create tasks with AI-parsed structure.", "status": "todo", "priority": "medium"},
        {"title": "Build team chat with WebSockets", "desc": "Real-time messaging per project with typing indicators and mentions.", "status": "blocked", "priority": "high"},
        {"title": "Performance audit and optimization", "desc": "Profile with Flipper, reduce bundle, optimize FlatList for 1000+ tasks.", "status": "todo", "priority": "medium"},
        {"title": "Beta release to TestFlight and Play Console", "desc": "Configure signing, set up beta tracks, invite 50 internal testers.", "status": "todo", "priority": "high"},
    ],
    "Data Pipeline": [
        {"title": "Design event schema and Avro registry", "desc": "Define schemas for 15 event types with backward compatibility.", "status": "done", "priority": "high"},
        {"title": "Deploy Kafka cluster on Kubernetes", "desc": "3-broker Kafka with KRaft, 7-day retention, replication factor 3.", "status": "done", "priority": "high"},
        {"title": "Build Flink stream processing jobs", "desc": "Windowed aggregations, sessionization, anomaly detection.", "status": "in_progress", "priority": "high"},
        {"title": "Implement data quality checks", "desc": "Great Expectations: schema validation, null checks, range validation.", "status": "in_progress", "priority": "medium"},
        {"title": "Set up ClickHouse analytics warehouse", "desc": "Materialized views for dashboards, partition by day, 90-day TTL.", "status": "done", "priority": "high"},
        {"title": "Create Grafana monitoring dashboards", "desc": "Lag monitoring, throughput, error rates, latency p50/p95/p99.", "status": "in_progress", "priority": "medium"},
        {"title": "Implement dead letter queue handling", "desc": "Route failed events to DLQ, inspection dashboard, replay button.", "status": "todo", "priority": "medium"},
        {"title": "Add PII detection and masking", "desc": "ML-based PII scanner to auto-mask emails, phones, SSNs in pipeline.", "status": "todo", "priority": "high"},
        {"title": "Load testing at 50k events per second", "desc": "Locust load test, identify bottlenecks, tune partitions and parallelism.", "status": "blocked", "priority": "high"},
        {"title": "Write runbooks for on-call engineers", "desc": "Document failure scenarios: consumer lag, broker failure, schema mismatch.", "status": "todo", "priority": "low"},
    ],
}

MEMBERS_PER_PROJECT = {
    "ShipIt Platform": ["Ama Mensah", "Kwame Asante", "Nana Osei", "Efua Darko"],
    "Mobile App v2": ["Kwame Asante", "Efua Darko"],
    "Data Pipeline": ["Ama Mensah", "Nana Osei"],
}


async def api_call(page: Page, method: str, url: str, body: dict | None = None) -> dict | None:
    """Make an API call via page.evaluate to include the auth header."""
    body_json = str(body).replace("'", "\\'") if body else "null"
    try:
        result = await page.evaluate(f"""
            async () => {{
                const user = JSON.parse(localStorage.getItem('user') || '{{}}');
                const opts = {{
                    method: '{method}',
                    headers: {{
                        'Content-Type': 'application/json',
                        'X-User-Id': String(user.id || '')
                    }}
                }};
                {f"opts.body = JSON.stringify({body});" if body else ""}
                const resp = await fetch('{url}', opts);
                return await resp.json();
            }}
        """)
        return result
    except Exception as e:
        print(f"   API error: {e}")
        return None


async def seed_demo(headless: bool = False):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, slow_mo=60)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        print("=" * 60)
        print("  ShipIt Demo Seeder")
        print("=" * 60)

        # ── Step 1: Log in ────────────────────────────────────────
        print("\n[1/7] Logging in as primary user...")
        await page.goto(BASE)
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(1)

        # The login page has: input[placeholder="e.g. alex_dev"] + button "Get Started"
        login_input = page.locator('input[placeholder="e.g. alex_dev"]')
        await login_input.fill(USERS[0])
        await asyncio.sleep(0.3)
        await page.locator('button:has-text("Get Started")').click()
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(1.5)
        print(f"   Logged in as: {USERS[0]}")

        # ── Step 2: Register other users via API ──────────────────
        print("\n[2/7] Registering team members...")
        for user in USERS[1:]:
            await api_call(page, "POST", "/api/auth/enter", {"name": user})
            print(f"   Registered: {user}")
            await asyncio.sleep(0.2)

        # ── Step 3: Create projects via UI ────────────────────────
        print("\n[3/7] Creating projects...")
        project_ids = {}

        for proj in PROJECTS:
            print(f"   Creating: {proj['name']}...")

            # Click "New Project" button
            await page.locator('button:has-text("New Project")').click()
            await asyncio.sleep(0.5)

            # Fill the modal form — exact selectors from Dashboard.tsx
            # Project Name input: placeholder="e.g., Q1 Product Launch"
            await page.locator('input[placeholder="e.g., Q1 Product Launch"]').fill(proj["name"])
            await asyncio.sleep(0.2)

            # Description textarea: placeholder="What is this project about?"
            await page.locator('textarea[placeholder="What is this project about?"]').fill(proj["description"])
            await asyncio.sleep(0.2)

            # Click "Create Project" — the submit button inside the form
            await page.locator('form button[type="submit"]').click()
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(1)

        # Get project IDs by clicking into each one
        await page.goto(BASE)
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(1)

        for proj in PROJECTS:
            try:
                # ProjectCard likely shows the name as a link
                card = page.locator(f'text="{proj["name"]}"').first
                await card.click()
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(0.8)

                # Extract project ID from URL: /projects/123
                url = page.url
                pid = url.split("/projects/")[1].split("/")[0].split("?")[0]
                project_ids[proj["name"]] = int(pid)
                print(f"   {proj['name']} → project_id={pid}")

                await page.goto(BASE)
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"   Warning: Could not get ID for {proj['name']}: {e}")

        # ── Step 4: Add members via API ───────────────────────────
        print("\n[4/7] Adding team members to projects...")
        for proj_name, members in MEMBERS_PER_PROJECT.items():
            pid = project_ids.get(proj_name)
            if not pid:
                continue
            for member in members:
                result = await api_call(page, "POST", f"/api/projects/{pid}/members", {"name": member})
                if result:
                    print(f"   Added {member} → {proj_name}")
                await asyncio.sleep(0.2)

        # ── Step 5: Create tasks via API ──────────────────────────
        print("\n[5/7] Creating tasks...")
        total_created = 0
        for proj_name, tasks in TASKS.items():
            pid = project_ids.get(proj_name)
            if not pid:
                continue

            for i, task in enumerate(tasks):
                result = await api_call(page, "POST", f"/api/projects/{pid}/tasks", {
                    "title": task["title"],
                    "description": task["desc"],
                    "status": task["status"],
                    "priority": task["priority"],
                    "position": i,
                })
                if result:
                    total_created += 1
                    status_icon = {"done": "✓", "in_progress": "→", "todo": "○", "blocked": "✕"}.get(task["status"], "?")
                    print(f"   {status_icon} [{proj_name[:12]:12s}] {task['title'][:55]}")

        # ── Step 6: Browse each board + take screenshots ──────────
        print("\n[6/7] Browsing boards & taking screenshots...")
        for proj_name, pid in project_ids.items():
            await page.goto(f"{BASE}/projects/{pid}")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)

            safe = proj_name.lower().replace(" ", "_")
            path = f"/home/rogerkorantenng/dev/Hackathons/Shipit/demo_{safe}.png"
            await page.screenshot(path=path, full_page=True)
            print(f"   Board: {proj_name} → demo_{safe}.png")

        # ── Step 7: Visit Agents page, trigger events, screenshot ─
        print("\n[7/7] Triggering agents & capturing agent dashboard...")

        # Store the first project as lastProjectId so agents page picks it up
        first_pid = list(project_ids.values())[0]
        await page.evaluate(f"localStorage.setItem('lastProjectId', '{first_pid}')")

        # Trigger all agents for the first project
        agent_names = [
            "product_intelligence", "design_sync", "code_orchestration",
            "security_compliance", "test_intelligence", "review_coordination",
            "deployment_orchestrator", "analytics_insights",
        ]
        for agent_name in agent_names:
            await api_call(page, "POST", f"/api/projects/{first_pid}/agents/{agent_name}/trigger", {
                "event_data": {"source": "demo_seed", "message": f"Demo trigger for {agent_name}"}
            })
            print(f"   Triggered: {agent_name}")
            await asyncio.sleep(0.2)

        # Wait for events to process
        await asyncio.sleep(3)

        # Navigate to Agents page
        await page.goto(f"{BASE}/agents")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        await page.screenshot(
            path="/home/rogerkorantenng/dev/Hackathons/Shipit/demo_agents.png",
            full_page=True,
        )
        print("   Screenshot: demo_agents.png")

        # ── Dashboard final screenshot ────────────────────────────
        await page.goto(BASE)
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(1.5)
        await page.screenshot(
            path="/home/rogerkorantenng/dev/Hackathons/Shipit/demo_dashboard.png",
            full_page=True,
        )
        print("   Screenshot: demo_dashboard.png")

        await browser.close()

        # ── Summary ───────────────────────────────────────────────
        print("\n" + "=" * 60)
        print("  Demo seeding complete!")
        print("=" * 60)
        print(f"\n  Users:    {len(USERS)}")
        print(f"  Projects: {len(PROJECTS)}")
        print(f"  Tasks:    {total_created}")
        print(f"  Agents:   {len(agent_names)} triggered")
        print(f"\n  Screenshots saved to project root.")
        print(f"  Open {BASE} to explore!\n")


if __name__ == "__main__":
    asyncio.run(seed_demo(headless=True))
