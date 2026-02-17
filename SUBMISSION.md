# ShipIt - AI-Powered Project Management with Autonomous Agent Fleet

## What is ShipIt?

ShipIt is an AI-powered project management platform that automates the entire software delivery lifecycle using a fleet of 9 autonomous AI agents. From the moment a Jira ticket is created to the second code is deployed in production, ShipIt's agents handle requirements analysis, code scaffolding, security scanning, test generation, review coordination, deployment orchestration, and more - all powered by **Gradient AI with Claude**.

Teams don't just manage work in ShipIt - the platform actively drives work forward through the pipeline.

## Demo


**Screenshots:**

| Dashboard | Kanban Board | Agent Fleet |
|-----------|-------------|-------------|
| ![Dashboard](https://raw.githubusercontent.com/rogerkorantenng/shipit/main/demo_dashboard.png) | ![Board](https://raw.githubusercontent.com/rogerkorantenng/shipit/main/demo_shipit_platform.png) | ![Agents](https://raw.githubusercontent.com/rogerkorantenng/shipit/main/demo_agents.png) |

| Mobile App Project | Data Pipeline Project |
|-------------------|----------------------|
| ![Mobile App](https://raw.githubusercontent.com/rogerkorantenng/shipit/main/demo_mobile_app_v2.png) | ![Data Pipeline](https://raw.githubusercontent.com/rogerkorantenng/shipit/main/demo_data_pipeline.png) |

## How We Use Gradient AI

Gradient powers every intelligent feature in ShipIt through Claude (Haiku and Sonnet models):

| Feature | Gradient Usage |
|---------|---------------|
| **Task Breakdown** | Claude decomposes tasks into subtasks with priorities and effort estimates |
| **Meeting Notes Extraction** | Claude parses raw meeting text into structured, actionable tasks |
| **Sprint Planning** | Claude analyzes team capacity and recommends sprint assignments |
| **Standup Reports** | Claude generates per-member standup updates from board state |
| **Priority Scoring** | Claude evaluates tasks and recommends re-prioritization with reasoning |
| **Requirements Analysis** | Agent 1 uses Claude to extract user stories, acceptance criteria, and complexity from Jira tickets |
| **Security Scanning (SAST)** | Agent 4 uses Claude for AI-based static analysis - detecting SQL injection, XSS, secrets, and OWASP Top 10 vulnerabilities in code diffs |
| **Test Generation** | Agent 5 uses Claude to generate unit test suggestions, integration tests, and identify edge cases from code changes |
| **Review Complexity Analysis** | Agent 6 uses Claude to assess PR complexity, estimate review time, and determine auto-merge eligibility |
| **Release Notes** | Agent 7 uses Claude to generate human-readable release notes from commit history |
| **Bottleneck Detection** | Agent 8 uses Claude to identify process bottlenecks and suggest improvements |
| **Design-to-Code Notes** | Agent 2 uses Claude to generate technical implementation specs from Figma design data |
| **Pulse Insights** | Claude analyzes team mood/energy trends to detect burnout risk |

All AI calls go through Gradient's agent endpoint with structured JSON output parsing and graceful fallbacks.

## Architecture

```
                        +-------------------+
                        |    React + TS     |
                        |    Frontend       |
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
     |  Gradient AI   |  |  SQLite/PG DB  |  |  Event Bus     |
     |  (Claude)      |  |                |  |  (async pub/   |
     |                |  |  12 models     |  |   sub, 40+     |
     +----------------+  +----------------+  |   event types) |
                                             +-------+--------+
                                                     |
                    +--------+--------+--------+-----+----+--------+--------+--------+
                    |        |        |        |          |        |        |        |
                 Agent 1  Agent 2  Agent 3  Agent 4   Agent 5  Agent 6  Agent 7  Agent 8
                 Product  Design   Code     Security  Test     Review   Deploy   Analytics
                    |        |        |        |          |        |        |        |
                    v        v        v        v          v        v        v        v
                  Jira    Figma   GitLab   GitLab     GitLab   GitLab   GitLab   Database
                                                                        Sentry
                                                                        Datadog
                                                         +--------+
                                                         | Agent 9 |
                                                         | Slack   |
                                                         +----+----+
                                                              |
                                                              v
                                                           Slack API
```

### Agent Pipeline (End-to-End Flow)

```
Jira Ticket Created
  --> Agent 1: Product Intelligence --> analyzes requirements, extracts stories
    --> Agent 3: Code Orchestration --> creates branch, generates boilerplate, opens MR
      --> Agent 4: Security Compliance --> scans code, blocks if critical vulns
      --> Agent 5: Test Intelligence --> generates test suggestions
        --> Agent 6: Review Coordination --> assigns reviewers, tracks SLA
          --> Agent 7: Deployment Orchestrator --> deploys, monitors health
            --> Agent 8: Analytics & Insights --> reports metrics

Figma Design Changed
  --> Agent 2: Design Sync --> generates implementation notes
    --> Agent 3: Code Orchestration --> creates branch for design work

All agents --> Agent 9: Slack Notifier --> team notifications
```

## Features

### Core Project Management
- **Kanban Board** - Drag-and-drop task management across 4 status columns (To Do, In Progress, Done, Blocked)
- **Sprint Management** - Full sprint lifecycle: planning, active, completed. AI-powered capacity planning
- **Team Management** - Add members, assign tasks, track workload
- **Activity Feed** - Complete audit trail of all project actions

### AI-Powered Actions (Gradient Claude)
- **AI Task Breakdown** - Decompose any task into subtasks with priorities and effort estimates
- **Meeting Notes Extraction** - Paste meeting notes, get structured tasks automatically
- **AI Sprint Planning** - Capacity-aware sprint assignment suggestions
- **Standup Reports** - One-click standup generation per team member
- **Priority Scoring** - AI-recommended re-prioritization with reasoning
- **Daily Digest** - Summarized project activity, stuck tasks, at-risk items
- **Blocker Analysis** - AI-detected blockers with severity and suggestions

### 9 Autonomous AI Agents
| # | Agent | What It Does |
|---|-------|-------------|
| 1 | **Product Intelligence** | Analyzes Jira tickets, extracts user stories, tags complexity, estimates effort |
| 2 | **Design Sync** | Monitors Figma changes, generates CSS/component specs, creates GitLab issues |
| 3 | **Code Orchestration** | Creates feature branches, generates boilerplate, opens MRs, assigns reviewers |
| 4 | **Security & Compliance** | AI-based SAST on code diffs, blocks merges on critical vulnerabilities |
| 5 | **Test Intelligence** | Generates unit/integration test suggestions, identifies coverage gaps and edge cases |
| 6 | **Review Coordination** | Assigns reviewers by expertise, tracks SLAs, sends reminders, auto-merges |
| 7 | **Deployment Orchestrator** | Triggers CI/CD, generates release notes, monitors post-deploy health, auto-rollback |
| 8 | **Analytics & Insights** | Velocity metrics, cycle time analysis, bottleneck detection, improvement suggestions |
| 9 | **Slack Notifier** | Delivers all agent notifications to Slack channels |

### Async Event Bus
- 40+ event types across Jira, GitLab, Figma, and agent domains
- In-process async pub/sub (no external dependencies)
- Correlation IDs for full event chain tracing
- Per-agent metrics: events processed, errors, average latency
- Human-readable event log with type-specific rendering

### Integrations
- **Jira** - Bidirectional sync (import/export tasks, sprints, statuses)
- **GitLab** - Branches, merge requests, pipelines, code diffs, comments
- **Figma** - File monitoring, component extraction, design comparisons
- **Slack** - Channel notifications, DMs, thread replies
- **Datadog** - Monitor status checks for post-deploy health
- **Sentry** - Error tracking for deployment health verification

### Gamification System
- **XP & Leveling** - Earn XP for completing tasks (scaled by priority), level up progressively
- **11 Achievement Badges** - Streak badges (3/7/14-day), milestone badges (XP thresholds), volume badges (task counts), Sprint Shipper
- **Team Leaderboard** - Ranked XP standings across the project

### Team Wellbeing (Pulse)
- Daily energy & mood tracking (1-5 scale)
- 30-day history with trends
- Team aggregate view
- AI-powered burnout risk detection and recommendations

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, TypeScript, Tailwind CSS, Vite |
| **Backend** | FastAPI (async), Python 3.11+ |
| **Database** | SQLAlchemy (async) + SQLite (dev) / PostgreSQL (prod) |
| **AI** | Gradient AI Platform (Claude Haiku 4.5 + Sonnet) |
| **Agent System** | Custom async event bus, 9 agents, pub/sub architecture |
| **External APIs** | GitLab REST v4, Figma REST, Slack Web API, Datadog, Sentry |
| **Deployment** | Docker Compose, DigitalOcean App Platform |

## Running Locally

### Prerequisites
- Python 3.11+
- Node.js 18+
- Gradient AI API key

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

### Environment Variables

```env
# Required
GRADIENT_API_KEY=your_gradient_api_key
GRADIENT_WORKSPACE_ID=your_workspace_id
GRADIENT_AGENT_ENDPOINT=your_agent_endpoint

# Optional (for agent integrations)
SLACK_BOT_TOKEN=xoxb-...
SLACK_DEFAULT_CHANNEL=#general
```

Per-project service connections (GitLab, Figma, Slack, Datadog, Sentry) are configured through the Agents UI - no environment variables needed.

## Project Structure

```
shipit/
  frontend/
    src/
      pages/          # 4 route pages (Dashboard, Projects, Board, Agents)
      components/     # 25+ UI components
      services/       # API client layer
      types.ts        # TypeScript interfaces
  backend/
    app/
      api/            # 11 API route modules (50+ endpoints)
      agents/         # 9 agent implementations + event bus + registry
      adapters/       # 4 external service adapters
      models/         # 12 SQLAlchemy models
      services/       # 6 business logic services
      db/             # Database initialization
  agent/              # Gradient ADK agent (tutor persona)
  extension/          # Chrome extension
  docker-compose.yml  # Container orchestration
```

## What Makes ShipIt Different

Most project management tools are **passive** - they store data and display it. ShipIt is **active**:

1. **Agents drive work forward** - A Jira ticket doesn't just sit there. It gets analyzed, a branch gets created, code gets scaffolded, security gets scanned, reviewers get assigned, and deployment happens - automatically.

2. **AI understands context** - Every AI feature uses your actual project data. Sprint planning knows your team's real capacity. Priority scoring considers blocking relationships. Security scanning reads the actual code diff.

3. **No tool-switching tax** - Jira, GitLab, Figma, Slack, Datadog, and Sentry all feed into one event stream. Your team sees everything in one place.

4. **Human-in-the-loop by default** - Agents are configurable per project. Every action is logged with correlation IDs. Critical decisions (like blocking a merge) create visible, reviewable events.

## Team

- **Roger Koranteng** - Full-stack development, AI integration, agent architecture

## Built For

[DigitalOcean Gradient AI Hackathon](https://www.digitalocean.com)

---

*Built with Gradient AI (Claude) on DigitalOcean*
