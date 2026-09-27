# Campus Social AI

**Every campus has a story.** An AI-assisted student social & campus discovery
platform, built as a B.Tech Information Technology software engineering
project.

Every college gets its own digital community: an anonymous "Tea" feed, a
normal social feed, Reels, 24-hour Stories, an AI Creation Studio, explainable
friend/study-buddy matching, campus communities, temporary discussion rooms,
direct messaging, events, opportunities, a marketplace, and an admin/
moderation dashboard — all backed by a real relational database and a real
(swappable) AI provider.

See `docs/` for the material you'll actually want for the report/viva:

| Doc | What it covers |
|---|---|
| `docs/ARCHITECTURE.md` | Why this stack, system diagram, request flow |
| `docs/DATABASE.md` | Schema, ER relationships, key design decisions |
| `docs/SECURITY.md` | Auth, RBAC, anonymous identity, OWASP-style defenses |
| `docs/AI.md` | The AI provider abstraction, moderation, recommendation algorithm |
| `docs/VIVA_GUIDE.md` | Anticipated viva questions with short, precise answers |
| `docs/FUTURE_SCOPE.md` | What's explicitly out of scope for this build, and why |

## Tech stack (and why)

- **Backend: Python + FastAPI** — a REST API that's easy to read top-to-bottom
  in a viva, with automatic interactive docs at `/docs` for free.
- **Database: PostgreSQL** via **SQLAlchemy ORM** — a real relational
  database with foreign keys/constraints, and the ORM means every query is
  parameterized (no hand-built SQL strings), which is the primary SQL
  injection defense.
- **Auth: JWT + bcrypt** — industry-standard, small enough to explain fully.
- **AI: a provider abstraction** (`backend/app/ai/`) with a default
  **offline mock provider** (no API key, no internet needed to demo) and an
  optional real OpenAI-compatible provider behind one environment variable.
- **Frontend: plain HTML/CSS/JavaScript** — no build step, every page can be
  opened and read directly; a shared `css/style.css` design system and
  `js/api.js`/`js/layout.js` keep it consistent without a framework.

## Project structure

```
campus-social-ai/
├── backend/            FastAPI app (models, schemas, routers, services, AI, security, tests)
├── frontend/            Static HTML/CSS/JS app (landing page + full product)
├── seed_data/           Global college directory + demo content seed script
├── docs/                 Architecture/security/AI/viva/future-scope docs
├── uploads/              Runtime media storage (gitignored)
├── .env.example
└── README.md
```

## Running it locally

### 1. Database

You need a PostgreSQL server reachable at the URL in your `.env` (or edit it
to match your setup). This project was developed and tested against
PostgreSQL 16.

```bash
sudo service postgresql start   # or however Postgres runs on your system
sudo -u postgres psql -c "CREATE USER campus_app WITH PASSWORD 'campus_dev_pw';"
sudo -u postgres psql -c "CREATE DATABASE campus_social OWNER campus_app;"
```

### 2. Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env    # edit if your DB credentials differ

# Seed the global college directory + demo accounts/content
python ../seed_data/seed.py

# Run the API (tables are also auto-created on startup)
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

Demo accounts created by the seed script:

| Role | Email | Password |
|---|---|---|
| Admin | admin@campus.ai | Admin12345 |
| Moderator | mod@campus.ai | Moderate123 |
| Student | aarav@campus.ai | Student123 |

### 3. Frontend

The frontend is static — any static file server works:

```bash
cd frontend
python3 -m http.server 5500
```

Open http://localhost:5500/index.html

### 4. Tests

```bash
cd backend && source .venv/bin/activate
python -m pytest tests/ -v
```

Tests run against an in-memory SQLite database (no Postgres required) so
they're fast and fully isolated from your dev data.

## What's implemented vs. simplified for this scope

This is an academic project: real features, honestly scoped. See
`docs/FUTURE_SCOPE.md` for the full list, but in short — Reels/Stories store
and serve uploaded media directly rather than transcoding it; rooms are
polling-based text chat rather than WebSocket/audio-video; the AI image
provider defaults to a deterministic offline placeholder unless a real
provider key is configured; and the sponsor/campaign system uses a simulated
budget with no real payment processing.
