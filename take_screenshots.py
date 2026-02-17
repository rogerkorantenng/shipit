"""Take detailed screenshots of every ShipIt feature for documentation."""

import asyncio
import os
from playwright.async_api import async_playwright

BASE = "http://localhost:5173"
OUT = "/home/rogerkorantenng/dev/Hackathons/Shipit/screenshots"
os.makedirs(OUT, exist_ok=True)


async def setup_page(browser):
    """Create a fresh page with user session."""
    ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
    page = await ctx.new_page()
    await page.goto(BASE, wait_until="domcontentloaded")
    await page.wait_for_timeout(1000)
    await page.evaluate("""() => {
        localStorage.setItem('user', JSON.stringify({id: 1, name: 'Roger'}));
    }""")
    return page, ctx


async def safe_click(page, selector, timeout=5000):
    """Click if element exists, return True if clicked."""
    try:
        el = page.locator(selector)
        if await el.count() > 0:
            await el.first.click(timeout=timeout)
            return True
    except Exception:
        pass
    return False


async def dismiss_modals(page):
    """Try to close any open modals."""
    for _ in range(3):
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(300)


async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()

        # ── 1. Dashboard ──
        print("1/14  Dashboard")
        page, ctx = await setup_page(browser)
        await page.goto(BASE, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        await page.screenshot(path=f"{OUT}/01_dashboard.png")
        await ctx.close()

        # ── 2. Projects ──
        print("2/14  Projects")
        page, ctx = await setup_page(browser)
        await page.goto(f"{BASE}/projects", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        await page.screenshot(path=f"{OUT}/02_projects.png")
        await ctx.close()

        # ── 3. Kanban Board ──
        print("3/14  Kanban Board")
        page, ctx = await setup_page(browser)
        await page.goto(f"{BASE}/projects/1", wait_until="domcontentloaded")
        await page.wait_for_timeout(2500)
        await page.screenshot(path=f"{OUT}/03_kanban_board.png")
        await ctx.close()

        # ── 4. AI Breakdown ──
        print("4/14  AI Breakdown")
        page, ctx = await setup_page(browser)
        await page.goto(f"{BASE}/projects/1", wait_until="domcontentloaded")
        await page.wait_for_timeout(2500)
        if await safe_click(page, 'button:has-text("AI Breakdown")'):
            await page.wait_for_timeout(6000)
            await page.screenshot(path=f"{OUT}/04_ai_breakdown.png")
        await ctx.close()

        # ── 5. Sprint Plan ──
        print("5/14  Sprint Plan")
        page, ctx = await setup_page(browser)
        await page.goto(f"{BASE}/projects/1", wait_until="domcontentloaded")
        await page.wait_for_timeout(2500)
        if await safe_click(page, 'button:has-text("Sprint Plan")'):
            await page.wait_for_timeout(6000)
            await page.screenshot(path=f"{OUT}/05_sprint_plan.png")
        await ctx.close()

        # ── 6. Standup Report ──
        print("6/14  Standup Report")
        page, ctx = await setup_page(browser)
        await page.goto(f"{BASE}/projects/1", wait_until="domcontentloaded")
        await page.wait_for_timeout(2500)
        if await safe_click(page, 'button:has-text("Standup")'):
            await page.wait_for_timeout(6000)
            await page.screenshot(path=f"{OUT}/06_standup_report.png")
        await ctx.close()

        # ── 7. Priority Score ──
        print("7/14  Priority Score")
        page, ctx = await setup_page(browser)
        await page.goto(f"{BASE}/projects/1", wait_until="domcontentloaded")
        await page.wait_for_timeout(2500)
        if await safe_click(page, 'button:has-text("Priority")'):
            await page.wait_for_timeout(6000)
            await page.screenshot(path=f"{OUT}/07_priority_score.png")
        await ctx.close()

        # ── 8. Analytics ──
        print("8/14  Analytics")
        page, ctx = await setup_page(browser)
        await page.goto(f"{BASE}/projects/1", wait_until="domcontentloaded")
        await page.wait_for_timeout(2500)
        if await safe_click(page, 'button:has-text("Analytics")'):
            await page.wait_for_timeout(6000)
            await page.screenshot(path=f"{OUT}/08_analytics.png")
        await ctx.close()

        # ── 9. Badge Panel ──
        print("9/14  Badge Panel")
        page, ctx = await setup_page(browser)
        await page.goto(f"{BASE}/projects/1", wait_until="domcontentloaded")
        await page.wait_for_timeout(2500)
        if await safe_click(page, 'button:has-text("Badge")'):
            await page.wait_for_timeout(3000)
            await page.screenshot(path=f"{OUT}/09_badges.png")
        await ctx.close()

        # ── 10. Jira Panel ──
        print("10/14 Jira Panel")
        page, ctx = await setup_page(browser)
        await page.goto(f"{BASE}/projects/1", wait_until="domcontentloaded")
        await page.wait_for_timeout(2500)
        if await safe_click(page, 'button:has-text("Jira")'):
            await page.wait_for_timeout(3000)
            await page.screenshot(path=f"{OUT}/10_jira_panel.png")
        await ctx.close()

        # ── 11. Agents Fleet ──
        print("11/14 Agents Fleet")
        page, ctx = await setup_page(browser)
        await page.goto(f"{BASE}/agents", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        await page.screenshot(path=f"{OUT}/11_agents_fleet.png")
        # Full page too
        await page.screenshot(path=f"{OUT}/11b_agents_full.png", full_page=True)
        await ctx.close()

        # ── 12. Agent Event Log ──
        print("12/14 Agent Event Log")
        page, ctx = await setup_page(browser)
        await page.goto(f"{BASE}/agents", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        log_el = page.locator('text=Event Log')
        if await log_el.count() > 0:
            await log_el.first.scroll_into_view_if_needed()
            await page.wait_for_timeout(1000)
            await page.screenshot(path=f"{OUT}/12_event_log.png")
        await ctx.close()

        # ── 13. Blockers ──
        print("13/14 Blockers")
        page, ctx = await setup_page(browser)
        await page.goto(f"{BASE}/projects/1", wait_until="domcontentloaded")
        await page.wait_for_timeout(2500)
        if await safe_click(page, 'button:has-text("Blockers")'):
            await page.wait_for_timeout(6000)
            await page.screenshot(path=f"{OUT}/13_blockers.png")
        await ctx.close()

        # ── 14. Board full-page ──
        print("14/14 Board Full Page")
        page, ctx = await setup_page(browser)
        await page.goto(f"{BASE}/projects/1", wait_until="domcontentloaded")
        await page.wait_for_timeout(2500)
        await page.screenshot(path=f"{OUT}/14_board_full.png", full_page=True)
        await ctx.close()

        await browser.close()

    # List what was captured
    files = sorted(os.listdir(OUT))
    print(f"\nDone! {len(files)} screenshots saved:")
    for f in files:
        size = os.path.getsize(f"{OUT}/{f}")
        print(f"  {f} ({size//1024}KB)")


asyncio.run(run())
