# StudyDrip

**Your AI-powered study companion.** Upload course materials, chat with an adaptive AI tutor, take smart quizzes, and track your progress.

Built for the [DigitalOcean Gradient AI Hackathon](https://dorahacks.io/hackathon/gradient-ai).

## Features

- **Upload Course Materials** — Drop PDFs, docs, and notes. Your AI tutor learns your curriculum via Gradient Knowledge Bases (RAG).
- **Adaptive AI Tutor ("Drip")** — A 3-axis persona system that adjusts to your learning level, performance momentum, and teaching mode in real-time.
- **Smart Quizzes** — AI-generated quizzes from your materials with instant grading and explanations.
- **Progress Tracking** — Visual dashboard showing scores, mastered topics, weak areas, and learning level progression.
- **Streaming Chat** — Real-time SSE streaming for responsive tutoring conversations.

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│   React +    │────▶│   FastAPI    │────▶│  Gradient Agent  │
│  Tailwind    │ SSE │  Backend     │     │  (ADK + Claude)  │
│  Frontend    │◀────│  + SQLite    │◀────│  + Knowledge Base│
└──────────────┘     └──────────────┘     └──────────────────┘
```

| Layer | Tech |
|-------|------|
| Frontend | React 18, TypeScript, Tailwind CSS, Vite |
| Backend | FastAPI, SQLAlchemy (async), SQLite/PostgreSQL |
| AI Agent | Gradient ADK, LangGraph, Claude (Haiku + Sonnet) |
| Knowledge Base | Gradient Knowledge Bases (RAG) |
| Deployment | DigitalOcean App Platform + Gradient |

## Agent Persona: "Drip"

Drip uses a **3-axis adaptive persona** that adjusts in real-time:

| Axis | Options | Trigger |
|------|---------|---------|
| **Learning Level** | Beginner → Intermediate → Advanced | Quiz scores + assessment |
| **Momentum** | Struggling → Steady → Thriving | Rolling quiz average |
| **Teaching Mode** | Explain · Quiz · Socratic · Review | Student requests + context |

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- Gradient API key ([get one here](https://cloud.digitalocean.com/ai))

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Edit .env with your Gradient API key
uvicorn app.main:app --reload
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

## Gradient AI Features Used

| Feature | Usage |
|---------|-------|
| Gradient ADK | Agent deployed via `gradient agent deploy` |
| Knowledge Bases (RAG) | One KB per course — PDF/doc upload, semantic retrieval |
| Serverless Inference | Claude Haiku 4.5 (chat), Claude Sonnet 4.5 (quiz gen) |
| Function Calling | `search_kb`, `generate_quiz`, `update_progress`, `get_progress` |
| Streaming (SSE) | Real-time chat responses |

## Project Structure

```
studydrip/
├── agent/              # Gradient ADK agent
│   ├── agent.py        # Main tutor agent logic
│   ├── persona.py      # 3-axis adaptive persona
│   ├── tools.py        # Function calling tools
│   └── prompts.py      # System prompts & templates
├── backend/            # FastAPI backend
│   └── app/
│       ├── api/        # Route handlers
│       ├── models/     # SQLAlchemy models
│       ├── services/   # Business logic
│       └── db/         # Database setup
├── frontend/           # React + Tailwind
│   └── src/
│       ├── pages/      # Route pages
│       ├── components/ # Reusable UI
│       ├── hooks/      # Custom hooks
│       └── services/   # API client
└── docker-compose.yml
```

## License

MIT
