"""
ShipIt Full Demo Video — Playwright walkthrough with annotations.
Shows EVERY feature: login, dashboard, kanban, task CRUD, all AI tools,
Jira sync, gamification, pulse, sprints, agents, connections, events.
Target: ~3.5 minutes.
"""

import asyncio
from playwright.async_api import async_playwright, Page

BASE = "http://localhost:5173"


async def overlay(page: Page, title: str, sub: str = "", dur: float = 2.5):
    t = title.replace("`", "").replace("\\", "")
    s = sub.replace("`", "").replace("\\", "")
    await page.evaluate(f"""(() => {{
        document.getElementById('dov')?.remove();
        const d = document.createElement('div'); d.id='dov';
        d.style.cssText='position:fixed;inset:0;z-index:99999;background:rgba(0,0,0,0.78);display:flex;align-items:center;justify-content:center;';
        d.innerHTML='<div style="text-align:center;color:#fff;padding:40px;"><h1 style="font-size:46px;font-weight:800;margin:0 0 12px;letter-spacing:-1px;">{t}</h1><p style="font-size:21px;opacity:.8;margin:0;font-weight:300;">{s}</p></div>';
        document.body.appendChild(d);
    }})()""")
    await asyncio.sleep(dur)
    await page.evaluate("document.getElementById('dov')?.remove()")
    await asyncio.sleep(0.3)


async def badge(page: Page, text: str, dur: float = 2.5):
    t = text.replace("`", "").replace("\\", "")
    await page.evaluate(f"""(() => {{
        document.getElementById('dbg')?.remove();
        const b = document.createElement('div'); b.id='dbg';
        b.style.cssText='position:fixed;top:14px;left:50%;transform:translateX(-50%);z-index:99999;background:#4f46e5;color:#fff;padding:10px 26px;border-radius:999px;font-size:15px;font-weight:600;box-shadow:0 4px 20px rgba(79,70,229,.4);';
        b.textContent="{t}";
        document.body.appendChild(b);
    }})()""")
    await asyncio.sleep(dur)
    await page.evaluate("document.getElementById('dbg')?.remove()")
    await asyncio.sleep(0.2)


async def close_modal(page: Page):
    """Try to close any open modal."""
    try:
        # Try clicking X button inside modal
        x_btn = page.locator('.fixed.inset-0 button').first
        if await x_btn.is_visible(timeout=500):
            # Click the top-right area where X usually is
            box = await page.locator('.fixed.inset-0').first.bounding_box()
            if box:
                await page.mouse.click(box["x"] + 5, box["y"] + 5)
                await asyncio.sleep(0.5)
                return
    except Exception:
        pass
    # Fallback: navigate away
    try:
        await page.evaluate("document.querySelector('.fixed.inset-0')?.remove()")
    except Exception:
        pass


async def click(page: Page, sel: str, timeout: int = 3000) -> bool:
    try:
        await page.locator(sel).first.click(timeout=timeout)
        return True
    except Exception:
        return False


async def record_demo():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, slow_mo=25)
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            record_video_dir="/home/rogerkorantenng/dev/Hackathons/Shipit/demo_video/",
            record_video_size={"width": 1440, "height": 900},
        )
        page = await context.new_page()
        print("Recording full demo...")

        # ── INTRO ─────────────────────────────────────────────────
        await page.goto(BASE)
        await page.wait_for_load_state("networkidle")
        await overlay(page, "ShipIt", "AI-Powered Project Management with Autonomous Agent Fleet", 3.5)

        # ── LOGIN ─────────────────────────────────────────────────
        await badge(page, "Quick Login - No passwords needed", 2)
        await page.locator('input[placeholder="e.g. alex_dev"]').click()
        await page.type('input[placeholder="e.g. alex_dev"]', "Roger Koranteng", delay=40)
        await asyncio.sleep(0.4)
        await page.locator('button:has-text("Get Started")').click()
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(1.5)

        # ── DASHBOARD ─────────────────────────────────────────────
        await badge(page, "Dashboard - 3 Projects, 35 Tasks, 12 Completed", 3)
        await asyncio.sleep(2)

        # ── BOARD: ShipIt Platform ────────────────────────────────
        await overlay(page, "Kanban Board", "Drag-and-drop task management with 4 columns", 2.5)
        await page.locator('text="ShipIt Platform"').first.click()
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)
        await badge(page, "ShipIt Platform - 15 tasks across 5 team members", 2.5)
        await asyncio.sleep(1)
        await page.mouse.wheel(0, 300)
        await asyncio.sleep(1.5)
        await page.mouse.wheel(0, -300)
        await asyncio.sleep(1)

        # ── CREATE TASK ───────────────────────────────────────────
        await badge(page, "Creating a new task", 1.5)
        if await click(page, 'button:has-text("New Task")'):
            await asyncio.sleep(0.8)
            try:
                await page.locator('.fixed input[type="text"]').first.fill("Implement real-time WebSocket notifications")
                await asyncio.sleep(0.4)
                await page.locator('.fixed textarea').first.fill("Push live updates to connected clients on task changes and agent events.")
                await asyncio.sleep(0.4)
                await page.locator('.fixed button[type="submit"]').first.click(timeout=2000)
            except Exception:
                pass
            await asyncio.sleep(1)
            await close_modal(page)
        await asyncio.sleep(0.5)

        # ── AI BREAKDOWN ──────────────────────────────────────────
        await overlay(page, "AI Task Breakdown", "Automatically decompose complex tasks into subtasks", 2.5)
        if await click(page, 'button:has-text("AI Breakdown")'):
            await asyncio.sleep(1)
            try:
                ta = page.locator('textarea').first
                await ta.fill("Build a complete user authentication system with OAuth2 social login, JWT tokens, email verification, and rate limiting")
                await asyncio.sleep(1.5)
            except Exception:
                pass
            await badge(page, "AI analyzes and generates actionable subtasks", 2)
            await close_modal(page)
        await asyncio.sleep(0.5)

        # ── MEETING NOTES ─────────────────────────────────────────
        await badge(page, "AI Meeting Notes - Extract tasks from meeting text", 2)
        if await click(page, 'button:has-text("Meeting Notes")'):
            await asyncio.sleep(0.8)
            try:
                ta = page.locator('textarea').first
                await ta.fill("Roger will handle the deployment pipeline by Friday. Ama to finish the Figma integration. We need to block the WebSocket feature until auth is done.")
                await asyncio.sleep(1.5)
            except Exception:
                pass
            await close_modal(page)
        await asyncio.sleep(0.5)

        # ── SPRINT PLAN ──────────────────────────────────────────
        await badge(page, "AI Sprint Planning - Auto-assign based on capacity", 2)
        if await click(page, 'button:has-text("Sprint Plan")'):
            await asyncio.sleep(1.5)
            await close_modal(page)
        await asyncio.sleep(0.5)

        # ── PRIORITY SCORE ────────────────────────────────────────
        await badge(page, "AI Priority Scoring - Data-driven task ranking", 2)
        if await click(page, 'button:has-text("Priority Score")'):
            await asyncio.sleep(1.5)
            await close_modal(page)
        await asyncio.sleep(0.5)

        # ── STANDUP ───────────────────────────────────────────────
        await badge(page, "AI Standup - Auto-generated daily standup notes", 2)
        if await click(page, 'button:has-text("Standup")'):
            await asyncio.sleep(1.5)
            await close_modal(page)
        await asyncio.sleep(0.5)

        # ── BLOCKERS ──────────────────────────────────────────────
        await badge(page, "AI Blocker Detection - Find stuck tasks automatically", 2)
        if await click(page, 'button:has-text("Blockers")'):
            await asyncio.sleep(1.5)
            await close_modal(page)
        await asyncio.sleep(0.5)

        # ── DIGEST ────────────────────────────────────────────────
        await badge(page, "AI Daily Digest - Project health summary", 2)
        if await click(page, 'button:has-text("Digest")'):
            await asyncio.sleep(1.5)
            await close_modal(page)
        await asyncio.sleep(0.5)

        # ── ANALYTICS ─────────────────────────────────────────────
        await badge(page, "Analytics Dashboard - Workload, velocity, completion rates", 2)
        if await click(page, 'button:has-text("Analytics")'):
            await asyncio.sleep(1.5)
            await close_modal(page)
        await asyncio.sleep(0.5)

        # ── JIRA SYNC ────────────────────────────────────────────
        await overlay(page, "Jira Integration", "Bidirectional sync - export, import, sprints, status mapping", 2.5)
        if await click(page, 'button:has-text("Jira Sync")'):
            await asyncio.sleep(1.5)
            await badge(page, "One config shared across all team members", 2)
            await asyncio.sleep(1)
            await close_modal(page)
        await asyncio.sleep(0.5)

        # ── GAMIFICATION (XP bar + badges visible in header) ─────
        await badge(page, "Gamification - XP, Levels, Streaks, and Badges", 2)
        await asyncio.sleep(1)

        # ── VIBE CHECK / PULSE ────────────────────────────────────
        await badge(page, "Vibe Check - Team energy and mood tracking", 2)
        await asyncio.sleep(1)

        # ── MULTIPLE PROJECTS ─────────────────────────────────────
        await overlay(page, "Multiple Projects", "Each with its own board, team, sprints, and AI tools", 2.5)

        await page.goto(BASE)
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(1)
        await page.locator('text="Mobile App v2"').first.click()
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(1.5)
        await badge(page, "Mobile App v2 - 10 tasks, 3 members", 2)
        await asyncio.sleep(1.5)

        await page.goto(BASE)
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(0.8)
        await page.locator('text="Data Pipeline"').first.click()
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(1.5)
        await badge(page, "Data Pipeline - Real-time ETL, 10 tasks", 2)
        await asyncio.sleep(1.5)

        # ── AGENT FLEET ──────────────────────────────────────────
        await overlay(page, "Autonomous Agent Fleet", "8 AI agents that automate your entire dev workflow", 3)

        await page.goto(f"{BASE}/agents")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        await badge(page, "Product Intelligence - Analyzes Jira tickets, extracts requirements", 2.5)
        await asyncio.sleep(1.5)

        await badge(page, "Design Sync - Monitors Figma changes, generates CSS specs", 2.5)
        await asyncio.sleep(1.5)

        await badge(page, "Code Orchestration - Creates branches, MRs, assigns reviewers", 2.5)
        await asyncio.sleep(1.5)

        # Scroll to see more agents
        await page.mouse.wheel(0, 200)
        await asyncio.sleep(0.5)

        await badge(page, "Security Compliance - AI-powered SAST on every MR diff", 2.5)
        await asyncio.sleep(1.5)

        await badge(page, "Test Intelligence - Generates test suggestions and coverage reports", 2.5)
        await asyncio.sleep(1.5)

        await badge(page, "Review Coordination - Assigns reviewers, tracks SLAs, auto-merges", 2.5)
        await asyncio.sleep(1.5)

        await page.mouse.wheel(0, 200)
        await asyncio.sleep(0.5)

        await badge(page, "Deployment Orchestrator - CI/CD, release notes, rollback monitoring", 2.5)
        await asyncio.sleep(1.5)

        await badge(page, "Analytics Insights - Velocity metrics, bottleneck detection, sprint predictions", 2.5)
        await asyncio.sleep(1.5)

        # ── TRIGGER AGENTS LIVE ───────────────────────────────────
        await overlay(page, "Triggering Agents Live", "Watch agents process events in real-time", 2.5)

        await page.mouse.wheel(0, -400)
        await asyncio.sleep(0.5)

        # Click trigger buttons on visible agents
        trigger_btns = page.locator('button:has-text("Trigger Manually")')
        count = await trigger_btns.count()
        for i in range(min(count, 4)):
            try:
                await trigger_btns.nth(i).click(timeout=1500)
                await asyncio.sleep(0.8)
            except Exception:
                break

        await asyncio.sleep(2)
        await badge(page, "Events flowing through the bus in real-time", 2.5)

        # Scroll down to event log
        await page.mouse.wheel(0, 500)
        await asyncio.sleep(2)
        await badge(page, "Event Log - Every agent action is tracked and auditable", 2.5)
        await asyncio.sleep(2)

        # ── SERVICE CONNECTIONS ───────────────────────────────────
        await page.mouse.wheel(0, -600)
        await asyncio.sleep(1)

        await overlay(page, "Service Connections", "GitLab - Figma - Slack - Datadog - Sentry", 2.5)
        await asyncio.sleep(1)

        # Try to reveal credentials
        await badge(page, "Stored credentials with secure reveal toggle", 2)
        try:
            await page.locator('button[title="Show credentials"]').first.click(timeout=2000)
            await asyncio.sleep(2)
            await badge(page, "Full API tokens revealed on click - masked by default", 2.5)
            await asyncio.sleep(1)
        except Exception:
            await asyncio.sleep(1)

        # ── PIPELINE FLOW ─────────────────────────────────────────
        await overlay(page, "End-to-End Agent Pipeline", "Jira Ticket → Requirements → Code → Security → Tests → Review → Deploy → Analytics", 3.5)

        # ── ARCHITECTURE ──────────────────────────────────────────
        await page.evaluate("""(() => {
            document.getElementById('dov')?.remove();
            const o = document.createElement('div'); o.id='dov';
            o.style.cssText='position:fixed;inset:0;z-index:99999;background:rgba(15,15,35,.93);display:flex;align-items:center;justify-content:center;';
            o.innerHTML=`<div style="text-align:center;color:#fff;padding:40px;max-width:900px;">
                <h1 style="font-size:36px;font-weight:800;margin:0 0 28px;">Architecture</h1>
                <pre style="font-size:15px;line-height:1.7;text-align:left;color:#a5b4fc;background:rgba(255,255,255,.05);padding:24px 32px;border-radius:12px;margin:0;">
  ┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
  │   React +    │────>│   FastAPI    │────>│  8 AI Agents     │
  │  Tailwind    │ SSE │  Backend     │     │  (Event Bus)     │
  │  Frontend    │<────│  + SQLite    │<────│  + Claude AI     │
  └──────────────┘     └──────────────┘     └──────────────────┘
                              │                      │
                       ┌──────┴──────┐        ┌──────┴──────┐
                       │   Jira      │        │  GitLab     │
                       │   Sync      │        │  Figma      │
                       │             │        │  Slack      │
                       └─────────────┘        │  Datadog    │
                                              │  Sentry     │
                                              └─────────────┘</pre></div>`;
            document.body.appendChild(o);
        })()""")
        await asyncio.sleep(5)
        await page.evaluate("document.getElementById('dov')?.remove()")
        await asyncio.sleep(0.3)

        # ── TECH STACK ────────────────────────────────────────────
        await page.evaluate("""(() => {
            const o = document.createElement('div'); o.id='dov';
            o.style.cssText='position:fixed;inset:0;z-index:99999;background:rgba(15,15,35,.93);display:flex;align-items:center;justify-content:center;';
            o.innerHTML=`<div style="text-align:center;color:#fff;padding:40px;max-width:800px;">
                <h1 style="font-size:36px;font-weight:800;margin:0 0 28px;">Tech Stack</h1>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;text-align:left;">
                    <div style="background:rgba(255,255,255,.06);padding:20px;border-radius:12px;">
                        <h3 style="color:#818cf8;font-size:13px;margin:0 0 8px;text-transform:uppercase;letter-spacing:1px;">Frontend</h3>
                        <p style="font-size:18px;margin:0;line-height:1.6;">React 18 + TypeScript<br>Tailwind CSS + Vite</p>
                    </div>
                    <div style="background:rgba(255,255,255,.06);padding:20px;border-radius:12px;">
                        <h3 style="color:#818cf8;font-size:13px;margin:0 0 8px;text-transform:uppercase;letter-spacing:1px;">Backend</h3>
                        <p style="font-size:18px;margin:0;line-height:1.6;">FastAPI + SQLAlchemy<br>Async Python + SQLite</p>
                    </div>
                    <div style="background:rgba(255,255,255,.06);padding:20px;border-radius:12px;">
                        <h3 style="color:#818cf8;font-size:13px;margin:0 0 8px;text-transform:uppercase;letter-spacing:1px;">AI / Agents</h3>
                        <p style="font-size:18px;margin:0;line-height:1.6;">Gradient ADK + Claude<br>8 Autonomous Agents</p>
                    </div>
                    <div style="background:rgba(255,255,255,.06);padding:20px;border-radius:12px;">
                        <h3 style="color:#818cf8;font-size:13px;margin:0 0 8px;text-transform:uppercase;letter-spacing:1px;">Integrations</h3>
                        <p style="font-size:18px;margin:0;line-height:1.6;">GitLab + Jira + Figma<br>Slack + Datadog + Sentry</p>
                    </div>
                </div></div>`;
            document.body.appendChild(o);
        })()""")
        await asyncio.sleep(5)
        await page.evaluate("document.getElementById('dov')?.remove()")
        await asyncio.sleep(0.3)

        # ── FINAL DASHBOARD ───────────────────────────────────────
        await page.goto(BASE)
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        # ── OUTRO ─────────────────────────────────────────────────
        await page.evaluate("""(() => {
            const o = document.createElement('div'); o.id='dov';
            o.style.cssText='position:fixed;inset:0;z-index:99999;background:linear-gradient(135deg,#1e1b4b,#312e81,#1e1b4b);display:flex;align-items:center;justify-content:center;';
            o.innerHTML=`<div style="text-align:center;color:#fff;padding:40px;">
                <h1 style="font-size:56px;font-weight:800;margin:0 0 16px;letter-spacing:-2px;">ShipIt</h1>
                <p style="font-size:24px;opacity:.8;margin:0 0 8px;font-weight:300;">Ship faster with AI-powered project management</p>
                <p style="font-size:16px;opacity:.5;margin:24px 0 0;">Built for the DigitalOcean Gradient AI Hackathon</p>
            </div>`;
            document.body.appendChild(o);
        })()""")
        await asyncio.sleep(4)

        # Finalize
        video_path = await page.video.path()
        await context.close()
        await browser.close()

        print(f"\nDone! Video: {video_path}")
        print(f"Convert: ffmpeg -i {video_path} -c:v libx264 -crf 23 demo.mp4")


if __name__ == "__main__":
    asyncio.run(record_demo())
