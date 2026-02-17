# ShipIt - AI-Powered Project Management with Autonomous Agent Fleet

## What is ShipIt?

ShipIt is an AI-powered project management platform that automates the entire software delivery lifecycle using a fleet of 9 autonomous AI agents. From the moment a Jira ticket is created to the second code is deployed in production, ShipIt's agents handle requirements analysis, code scaffolding, security scanning, test generation, review coordination, deployment orchestration, and more — all powered by **Gradient AI with Claude**.

Teams don't just manage work in ShipIt — the platform actively drives work forward through the pipeline.

![Dashboard Overview](https://raw.githubusercontent.com/rogerkorantenng/shipit/main/screenshots/01_dashboard.png)

---

## How It Works

### 1. Dashboard & Projects

When you log in, you see all your projects at a glance with real-time task statistics. Each project card shows how many tasks are in each status — giving you an instant health check across everything your team is working on.

![Projects](https://raw.githubusercontent.com/rogerkorantenng/shipit/main/screenshots/02_projects.png)

---

### 2. Kanban Board

Click into any project and you get a full Kanban board with four columns: **To Do**, **In Progress**, **Done**, and **Blocked**. Drag and drop tasks between columns. When you complete a task, you earn XP and get a confetti celebration.

The toolbar at the top gives you access to all AI-powered actions — each one is a single click away.

![Kanban Board](https://raw.githubusercontent.com/rogerkorantenng/shipit/main/screenshots/03_kanban_board.png)

---

### 3. AI Task Breakdown

Select any task and click **AI Breakdown**. Claude reads the task description, understands the context, and decomposes it into actionable subtasks — each with a priority level, effort estimate in hours, and suggested assignee. One click to apply them all to your board.

This turns a vague "Build user authentication" into 5-8 concrete, assignable subtasks in seconds.

![AI Breakdown](https://raw.githubusercontent.com/rogerkorantenng/shipit/main/screenshots/04_ai_breakdown.png)

---

### 4. AI Sprint Planning

Click **Sprint Plan** and Claude analyzes your entire team — who has capacity, what's already assigned, which tasks have the highest priority. It generates a sprint plan that:

- Assigns the right tasks to the right people
- Respects capacity limits (no one gets overloaded)
- Defers lower-priority work with explanations
- Calculates utilization percentage
- Writes the sprint goal

![Sprint Plan](https://raw.githubusercontent.com/rogerkorantenng/shipit/main/screenshots/05_sprint_plan.png)

---

### 5. Standup Report Generator

No more "what did I do yesterday?" moments. Click **Standup** and Claude generates a per-member report pulled directly from board activity:

- **Yesterday:** Tasks they moved to Done or In Progress
- **Today:** Tasks currently assigned and in progress
- **Blockers:** Any blocked tasks with context

Perfect for async teams or quick daily syncs.

![Standup Report](https://raw.githubusercontent.com/rogerkorantenng/shipit/main/screenshots/06_standup_report.png)

---

### 6. AI Priority Scoring

Claude evaluates every task on your board and recommends re-prioritization with clear reasoning. It catches things humans miss:

- A "medium" task that's actually blocking three high-priority tasks
- An "urgent" bug that's already been partially fixed
- Tasks that should be escalated based on due dates and dependencies

Each recommendation includes a confidence score and explanation.

![Priority Score](https://raw.githubusercontent.com/rogerkorantenng/shipit/main/screenshots/07_priority_score.png)

---

### 7. Team Analytics

Real-time analytics powered by AI insight generation:

- **Status distribution** — how tasks flow through your pipeline
- **Priority breakdown** — are you spending time on the right things?
- **Workload per member** — who's overloaded, who has capacity?
- **Completion rate** — trending up or down?
- **AI insights** — Claude identifies patterns and suggests process improvements

![Analytics](https://raw.githubusercontent.com/rogerkorantenng/shipit/main/screenshots/08_analytics.png)

---

### 8. Blocker Detection

AI scans your board for blocked tasks, identifies root causes, rates severity (critical/high/medium/low), and suggests concrete unblocking actions. It detects:

- Dependency chains (Task A blocks B blocks C)
- Resource conflicts (same person assigned to conflicting deadlines)
- Stale blockers (blocked for >3 days with no activity)

![Blockers](https://raw.githubusercontent.com/rogerkorantenng/shipit/main/screenshots/13_blockers.png)

---

### 9. Gamification

Every completed task earns XP scaled by priority (urgent = 40 XP, high = 30, medium = 20, low = 10). Features include:

- **Leveling system** — Level = floor(sqrt(XP/50)) + 1
- **11 achievement badges** — streak badges (3/7/14 days), milestone badges (100/500/1000 XP), volume badges (5/25/50 tasks), Sprint Shipper
- **Team leaderboard** — ranked XP standings
- **Streak tracking** — consecutive days with completions

![Badges](https://raw.githubusercontent.com/rogerkorantenng/shipit/main/screenshots/09_badges.png)

---

### 10. Jira Integration

Bidirectional sync with Jira:

- **Import** — Pull existing Jira issues into ShipIt
- **Export** — Push local tasks to Jira
- **Status sync** — Changes in either direction stay in sync
- **Sprint sync** — Pull Jira sprints and manage from one place
- **Meeting Notes** — Paste raw meeting text, Claude extracts tasks automatically

![Jira Panel](https://raw.githubusercontent.com/rogerkorantenng/shipit/main/screenshots/10_jira_panel.png)

---

### 11. The Agent Fleet

The centerpiece of ShipIt — **9 autonomous AI agents** that communicate through an async event bus with 40+ event types. Each agent subscribes to specific events and publishes its own, creating automated chains that handle the entire software delivery pipeline.

![Agent Fleet](https://raw.githubusercontent.com/rogerkorantenng/shipit/main/screenshots/11_agents_fleet.png)

#### The 9 Agents

| # | Agent | Subscribes To | What It Does |
|---|-------|--------------|-------------|
| 1 | **Product Intelligence** | Jira ticket created/updated | Analyzes requirements, extracts user stories, tags complexity, estimates effort |
| 2 | **Design Sync** | Figma design changed | Fetches components from Figma, generates CSS/component specs, creates GitLab issues |
| 3 | **Code Orchestration** | Issue assigned, requirements analyzed | Creates feature branches, generates boilerplate code, opens MRs, auto-assigns reviewers |
| 4 | **Security & Compliance** | PR opened, code pushed | AI-based SAST — catches SQL injection, XSS, secrets in code. Blocks merges on critical vulnerabilities |
| 5 | **Test Intelligence** | PR opened, security scan complete | Generates unit/integration test suggestions, identifies coverage gaps and edge cases |
| 6 | **Review Coordination** | PR ready for review, test report | Assigns reviewers by expertise, tracks review SLAs, sends reminders, can auto-merge |
| 7 | **Deployment Orchestrator** | PR merged to main | Validates readiness, triggers CI/CD, generates release notes, monitors post-deploy health via Datadog/Sentry, auto-rollback |
| 8 | **Analytics & Insights** | Metrics collected (scheduled) | Velocity metrics, cycle time, bottleneck detection, executive summaries, improvement suggestions |
| 9 | **Slack Notifier** | All notification events | Delivers notifications from every agent to Slack channels |

#### End-to-End Pipeline

```
Jira ticket created
  → Agent 1: Analyzes requirements, extracts stories
    → Agent 3: Creates branch, scaffolds code, opens MR
      → Agent 4: Scans for security vulnerabilities
      → Agent 5: Generates test suggestions
        → Agent 6: Assigns reviewers, tracks SLA
          → Agent 7: Deploys, monitors health, auto-rollback
            → Agent 8: Reports metrics, detects bottlenecks

All agents → Agent 9: Slack notifications
```

---

### 12. Agent Event Log

Every agent action is logged with correlation IDs for full event chain tracing. The event log renders clean, human-readable details instead of raw JSON:

- Vulnerability cards with severity badges and fix recommendations
- Test suggestions as structured lists with edge cases
- Review assignments with complexity scores and auto-merge eligibility
- Deploy status with health check results and release notes

![Event Log](https://raw.githubusercontent.com/rogerkorantenng/shipit/main/screenshots/12_event_log.png)

---

### 13. Service Connections

Teams connect their own instances per project — no shared credentials:

- **GitLab** — branches, MRs, pipelines, code diffs
- **Figma** — file monitoring, component extraction
- **Slack** — channel notifications, DMs
- **Datadog** — monitor status for post-deploy health
- **Sentry** — error tracking for deployment verification
- **Jira** — bidirectional task sync

Each connection can be tested independently. Credentials are masked in the UI with reveal-on-demand.

---

## How We Use Gradient AI

Every AI feature is powered by Gradient with Claude (Haiku 4.5 and Sonnet models):

| Feature | Gradient Usage |
|---------|---------------|
| Task Breakdown | Claude decomposes tasks into subtasks with priorities and effort estimates |
| Sprint Planning | Claude analyzes team capacity and recommends sprint assignments |
| Standup Reports | Claude generates per-member standup updates from board state |
| Priority Scoring | Claude evaluates tasks and recommends re-prioritization with reasoning |
| Meeting Notes | Claude parses raw meeting text into structured, actionable tasks |
| Daily Digest | Claude summarizes project activity, highlights stuck and at-risk tasks |
| Requirements Analysis | Agent 1 uses Claude to extract stories, acceptance criteria, complexity |
| Security Scanning (SAST) | Agent 4 uses Claude to detect SQL injection, XSS, secrets, OWASP Top 10 |
| Test Generation | Agent 5 uses Claude to suggest unit tests, integration tests, edge cases |
| Review Analysis | Agent 6 uses Claude to assess PR complexity and auto-merge eligibility |
| Release Notes | Agent 7 uses Claude to generate human-readable release notes from commits |
| Bottleneck Detection | Agent 8 uses Claude to identify process bottlenecks and suggest fixes |
| Design-to-Code | Agent 2 uses Claude to generate technical implementation specs from Figma data |
| Burnout Detection | Claude analyzes team mood/energy trends to detect burnout risk |

All AI calls go through Gradient's agent endpoint with structured JSON output parsing and graceful fallbacks.

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

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, TypeScript, Tailwind CSS, Vite |
| **Backend** | FastAPI (async), Python 3.11+ |
| **Database** | SQLAlchemy (async) + SQLite (dev) / PostgreSQL (prod) |
| **AI** | Gradient AI Platform — Claude Haiku 4.5 + Sonnet |
| **Agent System** | Custom async event bus, 9 agents, pub/sub architecture |
| **External APIs** | GitLab REST v4, Figma REST, Slack Web API, Datadog, Sentry |
| **Deployment** | Docker Compose, DigitalOcean App Platform |

---

## What Makes ShipIt Different

Most project management tools are **passive** — they store data and display it. ShipIt is **active**:

1. **Agents drive work forward** — A Jira ticket doesn't just sit there. It gets analyzed, a branch gets created, code gets scaffolded, security gets scanned, reviewers get assigned, and deployment happens — automatically.

2. **AI understands your context** — Every AI feature uses your actual project data. Sprint planning knows your team's real capacity. Priority scoring considers blocking relationships. Security scanning reads the actual code diff.

3. **No tool-switching tax** — Jira, GitLab, Figma, Slack, Datadog, and Sentry all feed into one event stream. Your team sees everything in one place.

4. **Human-in-the-loop** — Agents are configurable per project. Every action is logged with correlation IDs. Critical decisions (like blocking a merge) create visible, reviewable events.

---

## Running Locally

### Prerequisites
- Python 3.11+
- Node.js 18+
- Gradient API key

### Setup

```bash
# Clone
git clone https://github.com/rogerkorantenng/shipit.git
cd shipit

# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add your GRADIENT_API_KEY
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

---

## Project Structure

```
shipit/
├── frontend/src/
│   ├── pages/          # 4 pages: Dashboard, Projects, Board, Agents
│   ├── components/     # 25+ UI components
│   └── services/       # API client layer
├── backend/app/
│   ├── api/            # 11 route modules, 50+ endpoints
│   ├── agents/         # 9 agent implementations + event bus + registry
│   ├── adapters/       # GitLab, Figma, Slack, Monitoring adapters
│   ├── models/         # 12 SQLAlchemy data models
│   └── services/       # AI, gamification, Jira, activity services
├── agent/              # Gradient ADK agent
├── extension/          # Chrome extension
└── docker-compose.yml  # Container orchestration
```

---

## Team

**Roger Koranteng** — Full-stack development, AI integration, agent architecture

---

*Built with Gradient AI (Claude) on DigitalOcean*
