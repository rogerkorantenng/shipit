# ShipIt

**AI-powered project management with a fleet of 9 autonomous agents that automate the entire software delivery lifecycle.**

Built for the [DigitalOcean Gradient AI Hackathon](https://dorahacks.io/hackathon/gradient-ai).

![Dashboard](https://raw.githubusercontent.com/rogerkorantenng/shipit/main/screenshots/01_dashboard.png)

---

## What is ShipIt?

ShipIt is more than a project board. It's an intelligent platform where AI agents actively drive your work forward — from the moment a Jira ticket lands to the second code ships to production.

You manage your tasks on a Kanban board. Behind the scenes, 9 specialized AI agents handle requirements analysis, branch creation, security scanning, test generation, code review, deployment, and analytics — all communicating through an async event bus and powered by **Gradient AI with Claude**.

---

## Features

### Kanban Board with Drag & Drop

Organize tasks across four columns — To Do, In Progress, Done, and Blocked. Drag tasks between columns to update status. Complete a task and get a confetti celebration.

![Kanban Board](https://raw.githubusercontent.com/rogerkorantenng/shipit/main/screenshots/03_kanban_board.png)

---

### AI Task Breakdown

Select any task and click **AI Breakdown**. Claude analyzes it and decomposes it into subtasks with priorities, effort estimates, and assignee suggestions. One click to apply them all to your board.

![AI Breakdown](https://raw.githubusercontent.com/rogerkorantenng/shipit/main/screenshots/04_ai_breakdown.png)

---

### AI Sprint Planning

Click **Sprint Plan** and Claude analyzes your team's capacity, current workload, and task priorities. It suggests which tasks to pull into the sprint, which to defer, and calculates utilization. It even writes the sprint goal.

![Sprint Plan](https://raw.githubusercontent.com/rogerkorantenng/shipit/main/screenshots/05_sprint_plan.png)

---

### Standup Report Generator

One click generates a per-member standup report — what each person did yesterday, what they're doing today, and what's blocking them. Pulled directly from your board state. No more morning standups where nobody remembers what they did.

![Standup Report](https://raw.githubusercontent.com/rogerkorantenng/shipit/main/screenshots/06_standup_report.png)

---

### AI Priority Scoring

Claude evaluates every task on your board and recommends re-prioritization with reasoning. It catches things humans miss — like a medium-priority task that's actually blocking three other tasks.

![Priority Score](https://raw.githubusercontent.com/rogerkorantenng/shipit/main/screenshots/07_priority_score.png)

---

### Team Analytics

Real-time analytics showing status distribution, priority breakdown, workload per member, and completion rates. AI generates insights about your team's performance and identifies improvement areas.

![Analytics](https://raw.githubusercontent.com/rogerkorantenng/shipit/main/screenshots/08_analytics.png)

---

### Blocker Detection

AI scans your board for blocked tasks, identifies root causes, rates severity, and suggests concrete actions to unblock. Catches dependency chains and resource conflicts that aren't obvious at a glance.

![Blockers](https://raw.githubusercontent.com/rogerkorantenng/shipit/main/screenshots/13_blockers.png)

---

### Gamification System

Every completed task earns XP (scaled by priority). Level up, earn 11 achievement badges, and compete on the team leaderboard. Badges include streak-based (3/7/14-day streaks), milestone (XP thresholds), volume (task counts), and the Sprint Shipper badge for clearing all sprint tasks.

![Badges](https://raw.githubusercontent.com/rogerkorantenng/shipit/main/screenshots/09_badges.png)

---

### Jira Integration

Connect your Jira instance for bidirectional sync. Import existing Jira issues, export local tasks back, and keep statuses synchronized. Sprint sync works too — pull Jira sprints into ShipIt and manage them from one place.

![Jira](https://raw.githubusercontent.com/rogerkorantenng/shipit/main/screenshots/10_jira_panel.png)

---

### Autonomous Agent Fleet

The centerpiece of ShipIt — 9 specialized AI agents that communicate through an async event bus to automate the entire software delivery pipeline.

![Agent Fleet](https://raw.githubusercontent.com/rogerkorantenng/shipit/main/screenshots/11_agents_fleet.png)

Each agent subscribes to specific event types and publishes its own events, creating automated chains:

| # | Agent | What It Does |
|---|-------|-------------|
| 1 | **Product Intelligence** | Analyzes Jira tickets → extracts user stories, tags complexity, estimates effort |
| 2 | **Design Sync** | Monitors Figma → generates CSS/component specs, creates GitLab issues |
| 3 | **Code Orchestration** | Creates feature branches, generates boilerplate, opens MRs, assigns reviewers |
| 4 | **Security & Compliance** | AI-based SAST on every push — catches SQL injection, XSS, secrets, blocks merges on critical vulns |
| 5 | **Test Intelligence** | Generates unit/integration test suggestions, identifies coverage gaps and edge cases |
| 6 | **Review Coordination** | Assigns reviewers by expertise, tracks SLAs, sends reminders, can auto-merge |
| 7 | **Deployment Orchestrator** | Triggers CI/CD, generates release notes, monitors post-deploy health, auto-rollback |
| 8 | **Analytics & Insights** | Velocity metrics, cycle time, bottleneck detection, improvement suggestions |
| 9 | **Slack Notifier** | Delivers all agent notifications to Slack channels |

---

### Agent Event Log

Every agent action is logged with correlation IDs for full tracing. The event log shows clean, human-readable details — vulnerability cards with severity badges, test suggestions as lists, deploy status with health checks.

![Event Log](https://raw.githubusercontent.com/rogerkorantenng/shipit/main/screenshots/12_event_log.png)

---

## Architecture

```
                        +-------------------+
                        |   React + TS      |
                        |   Frontend        |
                        +--------+----------+
                                 |
                        +--------v----------+
                        |  FastAPI Backend   |
                        |  (async Python)    |
                        +--------+----------+
                                 |
              +------------------+------------------+
              |                  |                   |
     +--------v------+  +-------v--------+  +-------v--------+
     | Gradient AI    |  |  SQLite/PG DB  |  |  Event Bus     |
     | (Claude)       |  |  12 models     |  |  40+ event     |
     |                |  |                |  |  types          |
     +----------------+  +----------------+  +-------+--------+
                                                     |
              +------+------+------+------+------+------+------+------+
              |      |      |      |      |      |      |      |      |
            Ag.1   Ag.2   Ag.3   Ag.4   Ag.5   Ag.6   Ag.7   Ag.8   Ag.9
              |      |      |      |      |      |      |      |      |
              v      v      v      v      v      v      v      v      v
            Jira  Figma  GitLab GitLab GitLab GitLab GitLab   DB   Slack
                                                      Sentry
                                                      Datadog
```

**End-to-end pipeline:**
```
Jira ticket created
  → Agent 1 analyzes requirements, extracts stories
    → Agent 3 creates branch, scaffolds code, opens MR
      → Agent 4 scans for security vulnerabilities
      → Agent 5 generates test suggestions
        → Agent 6 assigns reviewers, tracks SLA
          → Agent 7 deploys, monitors health, auto-rollback if needed
            → Agent 8 reports metrics, detects bottlenecks
```

---

## How We Use Gradient AI

Every AI feature in ShipIt is powered by Gradient with Claude:

| Feature | How Gradient Is Used |
|---------|---------------------|
| Task Breakdown | Claude decomposes tasks into subtasks with effort estimates |
| Sprint Planning | Claude analyzes capacity and recommends sprint assignments |
| Standup Reports | Claude generates per-member standup updates from board state |
| Priority Scoring | Claude evaluates tasks and recommends re-prioritization |
| Requirements Analysis | Agent 1 uses Claude to extract stories and acceptance criteria |
| Security Scanning | Agent 4 uses Claude for SAST — SQL injection, XSS, OWASP Top 10 |
| Test Generation | Agent 5 uses Claude to suggest unit tests, integration tests, edge cases |
| Review Analysis | Agent 6 uses Claude to assess PR complexity and auto-merge eligibility |
| Release Notes | Agent 7 uses Claude to generate release notes from commits |
| Bottleneck Detection | Agent 8 uses Claude to identify process bottlenecks |
| Design-to-Code | Agent 2 uses Claude to generate technical specs from Figma designs |
| Burnout Detection | Claude analyzes team mood/energy trends from Pulse data |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Tailwind CSS, Vite |
| Backend | FastAPI (async), Python 3.11+ |
| Database | SQLAlchemy (async) + SQLite (dev) / PostgreSQL (prod) |
| AI | Gradient AI Platform — Claude Haiku 4.5 + Sonnet |
| Agents | Custom async event bus, 9 agents, pub/sub |
| Integrations | GitLab, Figma, Slack, Datadog, Sentry, Jira |
| Deployment | Docker Compose, DigitalOcean App Platform |

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- [Gradient API key](https://cloud.digitalocean.com/ai)

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Edit .env with your GRADIENT_API_KEY
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### With Docker

```bash
docker compose up --build
```

Open http://localhost:5173 (dev) or http://localhost:3000 (Docker).

---

## Project Structure

```
shipit/
├── frontend/src/
│   ├── pages/          # Dashboard, Projects, Board, Agents
│   ├── components/     # 25+ UI components
│   └── services/       # API client
├── backend/app/
│   ├── api/            # 11 route modules, 50+ endpoints
│   ├── agents/         # 9 agents + event bus + registry
│   ├── adapters/       # GitLab, Figma, Slack, Monitoring
│   ├── models/         # 12 SQLAlchemy models
│   └── services/       # AI, gamification, Jira, activity
├── agent/              # Gradient ADK agent
├── extension/          # Chrome extension
└── docker-compose.yml
```

---

## Team

**Roger Koranteng** — Full-stack development, AI integration, agent architecture

## License

MIT
