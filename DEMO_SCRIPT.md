# ShipIt Demo Script

**Total Time:** ~3.5 minutes
**Tip:** Speak naturally, don't rush. Pause briefly when switching screens so viewers can follow.

---

## INTRO (0:00 - 0:15)

> "Hey everyone, this is ShipIt - an AI-powered project management platform built for the DigitalOcean Gradient AI Hackathon."
>
> "ShipIt helps development teams ship faster by combining smart project management with a fleet of 9 autonomous AI agents that automate the entire software delivery lifecycle - from ticket creation all the way to deployment."

---

## 1. DASHBOARD & LOGIN (0:15 - 0:30)

*Show the Dashboard page*

> "Starting on the dashboard - you log in with just your name, no passwords needed for the hackathon demo. You can see all your projects at a glance with task statistics - how many are in progress, completed, or blocked."
>
> "We have three demo projects here - the ShipIt Platform itself, a Mobile App, and a Data Pipeline project."

*Click into the ShipIt Platform project*

---

## 2. KANBAN BOARD (0:30 - 1:00)

*Show the Board page with columns*

> "This is the Kanban board - four columns: To Do, In Progress, Done, and Blocked. You can drag and drop tasks between columns, and when you complete a task you get a confetti celebration."

*Drag a task to Done to show confetti*

> "Every action earns XP in our gamification system. Let me show that."

*Click the Badge Panel button*

> "We have 11 achievement badges - streak-based ones like 'On Fire' for 3 days in a row, milestone badges like 'Centurion' for 50 tasks, and a team leaderboard with XP rankings."

*Close badge panel*

---

## 3. AI FEATURES (1:00 - 1:45)

> "Now here's where it gets interesting - the AI features. ShipIt uses Gradient with Claude to power all of these."

### AI Task Breakdown
*Click "AI Breakdown" on a task*

> "AI Breakdown takes any task and decomposes it into subtasks with priorities, effort estimates, and assignee suggestions. It understands the context of your project."

*Show the breakdown results*

### Meeting Notes
*Click "Meeting Notes"*

> "Paste in raw meeting notes and the AI extracts actionable tasks automatically - with priorities and assignments. No more action items falling through the cracks."

*Show results briefly*

### Sprint Planning
*Click "Sprint Plan"*

> "AI Sprint Planning analyzes your team's capacity and suggests which tasks to pull into the sprint, which to defer, and calculates utilization. It even generates a sprint goal."

*Show the plan*

### Standup Report
*Click "Standup Report"*

> "One click generates a standup report for each team member - what they did, what they're doing, and what's blocking them. It pulls this directly from the board state."

### Priority Scoring
*Click "Priority Score"*

> "Priority scoring uses AI to analyze every task and recommend re-prioritization with reasoning - like flagging a task as high priority because it's blocking other work."

---

## 4. JIRA INTEGRATION (1:45 - 2:00)

*Click "Jira Sync" button*

> "ShipIt integrates with Jira for teams already using it. You connect your Jira instance, and we do bidirectional sync - import existing issues, export new tasks back to Jira, and keep statuses in sync. Sprints sync too."

*Show the Jira connection panel briefly*

---

## 5. PULSE - TEAM WELLBEING (2:00 - 2:10)

*Show the Pulse widget on the board*

> "Pulse is our team wellbeing tracker. Each team member logs their daily energy and mood on a 1-to-5 scale. The AI analyzes trends to detect burnout risk and suggest interventions - because shipping fast shouldn't come at the cost of your team's health."

---

## 6. AGENT FLEET (2:10 - 3:15)

*Navigate to the Agents page*

> "Now the centerpiece of ShipIt - the autonomous Agent Fleet. We built 9 specialized AI agents that communicate through an async event bus to automate the entire software delivery pipeline."

*Point to the agent grid*

> "Let me walk through each one:"

> "**Product Intelligence** - When a Jira ticket comes in, this agent analyzes it, extracts user stories, tags complexity, and estimates effort."

> "**Design Sync** - Watches Figma for design changes and generates technical implementation notes - CSS specs, component breakdowns, and creates GitLab issues automatically."

> "**Code Orchestration** - Creates feature branches, generates boilerplate code, PR templates, and auto-assigns reviewers."

> "**Security & Compliance** - Performs AI-based static analysis on every code push - catches SQL injection, XSS, secrets in code, and blocks merges on critical vulnerabilities."

> "**Test Intelligence** - Analyzes code changes and generates unit test suggestions, integration tests, and identifies edge cases and coverage gaps."

> "**Review Coordination** - Assigns the right reviewers based on expertise, tracks SLAs, sends reminders, and can auto-merge when all checks pass."

> "**Deployment Orchestrator** - Validates deployment readiness, triggers CI/CD pipelines, generates release notes from commits, monitors post-deploy health via Datadog and Sentry, and auto-rolls back if errors spike."

> "**Analytics & Insights** - Collects velocity metrics, detects bottlenecks, and generates executive summaries with improvement suggestions."

> "**Slack Notifier** - Delivers all agent notifications to your Slack channels."

### Event Log
*Scroll to the event log*

> "The event log shows everything happening in real time. When I trigger an agent, you can see the chain reaction - one agent's output feeds into the next. Each event expands to show clean, human-readable details - vulnerability cards with severity badges, test suggestions, review assignments, deploy status."

*Expand a few events to show the sanitized details*

### Service Connections
*Show the connection panel*

> "Teams connect their own GitLab, Figma, Slack, Datadog, and Sentry instances per project. Each connection can be tested independently."

---

## 7. ARCHITECTURE WRAP-UP (3:15 - 3:30)

> "Under the hood: React and TypeScript on the frontend, FastAPI with async SQLAlchemy on the backend, and all AI powered by Gradient with Claude."
>
> "The agent system uses an in-process async event bus with 40-plus event types, correlation IDs for tracing, and per-agent metrics and configuration."
>
> "ShipIt takes your team from ticket to deployed - automatically, intelligently, and safely. Thanks for watching!"

---

## KEY TALKING POINTS (if asked questions)

- **Why agents?** Manual handoffs between tools is where delivery slows down. Agents automate the glue between Jira, GitLab, Figma, and monitoring tools.
- **Why Gradient?** Gradient's Claude integration handles everything from simple task breakdown to complex security scanning - all through one API.
- **What makes it different?** Most PM tools are passive. ShipIt actively drives work forward through the pipeline.
- **Scale?** The event bus is in-process async - no Redis needed. Agents are independently configurable and can be enabled/disabled per project.
- **Security?** Service credentials are stored encrypted per-project, masked in the UI with reveal-on-demand, and never logged.
