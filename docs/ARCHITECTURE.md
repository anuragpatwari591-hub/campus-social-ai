# Architecture

## System diagram

```
                        STUDENT SOCIAL PLATFORM
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
      SOCIAL                     AI                      CAMPUS
        │                         │                         │
  ┌─────┼─────┐            ┌──────┼──────┐           ┌──────┼──────┐
  │     │     │            │      │      │           │      │      │
 Tea  Reels Stories       Text  Image  Sticker      Events Clubs Rooms
        │                         │                         │
        └────────────┬────────────┘                         │
                      │                                      │
                  DISCOVERY  ───────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
    Matching        Search      Communities
        │
        └────────────┬────────────┘
                      │
               MONETIZATION
                      │
       Sponsors / Campaigns / Events / Marketplace
```

## Request flow

```
Browser (frontend/*.html, plain JS)
   │  fetch() with Authorization: Bearer <JWT>
   ▼
FastAPI app (backend/app/main.py)
   │  CORS + rate-limit middleware
   ▼
Router (backend/app/routers/*.py)
   │  Depends(get_current_user) → auth/RBAC check
   │  Pydantic schema → input validation
   ▼
Service layer (backend/app/services/*.py)      AI provider (backend/app/ai/*.py)
   │  anonymous identity, recommendation,            │  generate_text/image/sticker,
   │  moderation                                     │  moderate_content
   ▼                                                 ▼
SQLAlchemy ORM  ───────────────────────────►  PostgreSQL
   (parameterized queries only)
```

## Why this stack

| Layer | Choice | Why |
|---|---|---|
| API framework | **FastAPI** | Type-hinted request/response models (Pydantic) give free input validation and auto-generated docs at `/docs` — useful for a viva demo. Async-capable but the code stays synchronous/simple where it doesn't need to be. |
| Database | **PostgreSQL** | A real, production-grade relational database with proper foreign keys, constraints and transactions — directly maps to the ER diagram taught in a DBMS course. |
| ORM | **SQLAlchemy 2.0** | Declarative models read like the schema; every query is parameterized automatically (SQL injection defense) without writing raw SQL. |
| Auth | **JWT + bcrypt** (via `python-jose` + `passlib`) | Stateless tokens are simple to explain and test; bcrypt is a slow, salted hash designed to resist brute-forcing. |
| AI | **Provider abstraction + offline mock provider** | The whole platform is demoable with zero external dependencies or API keys, while the exact same code path works with a real model behind one environment variable. |
| Frontend | **Plain HTML/CSS/JS** | No build step, no framework internals to explain that aren't already covered by a B.Tech web development course; a shared stylesheet and two small JS helper files (`api.js`, `layout.js`) keep ~15 pages visually and behaviorally consistent. |

## Backend module layout

```
backend/app/
├── main.py            FastAPI app: middleware, router registration, startup
├── config.py           Settings loaded from environment variables
├── database.py         SQLAlchemy engine/session/Base
├── models/              One SQLAlchemy model module per domain (geo, user,
│                        content, social, moderation, ai, campus_life, monetization)
├── schemas/             Pydantic request/response models (mirrors models/)
├── routers/              One FastAPI router per feature area (auth, posts, reels, ...)
├── auth/                 Password hashing, JWT issuing/verification, RBAC dependencies
├── ai/                   AIProvider interface + MockAIProvider + OpenAIProvider
├── services/             Business logic that isn't a one-line DB query
│                        (anonymous_identity, recommendation, moderation)
├── security/             Rate limiting, input sanitization, upload validation
└── utils/                (reserved for shared helpers as the project grows)
```

Each router only talks to the database through SQLAlchemy models, and only
generates AI content through `app.ai.get_ai_provider()` — never a vendor SDK
call inline in a route handler. That separation is what makes it possible to
answer "how would you swap PostgreSQL for MySQL" or "how would you swap the
AI provider" in a viva without hand-waving: you'd change `config.py`/one
factory function, not scatter changes across the codebase.

## Frontend structure

```
frontend/
├── index.html, login.html, register.html      Public pages (no auth required)
├── home.html, tea.html, reels.html, ...        Authenticated app pages
├── css/style.css                                Shared design system (CSS variables, components)
└── js/
    ├── api.js       fetch() wrapper + JWT storage/attachment + small helpers
    ├── layout.js     Renders the shared top nav / bottom nav on every app page
    └── feed.js       Shared post-card rendering + like/comment/report wiring
```

Each page is a normal static HTML file that pulls in these three scripts and
calls the REST API directly with `fetch`. There is no client-side router or
virtual DOM — a full page load per navigation, which keeps the mental model
(and the viva explanation) simple: "this button calls this endpoint, which
returns this JSON, which is rendered with this template string."
