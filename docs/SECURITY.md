# Security

## Authentication & session management

- Passwords are hashed with **bcrypt** (via `passlib`) before storage —
  `User.hashed_password` never contains a plaintext or reversibly-encrypted
  password. `auth/security.py::hash_password` / `verify_password`.
- Login issues a **JWT** signed with `JWT_SECRET_KEY` (HS256), containing the
  user id and role, expiring after `ACCESS_TOKEN_EXPIRE_MINUTES`
  (`auth/security.py::create_access_token`).
- The login endpoint returns the *same* `401` for "no such account" and
  "wrong password" — this stops an attacker from using login attempts to
  discover which emails are registered (account enumeration).
- Every protected route depends on `auth/deps.py::get_current_user`, which
  decodes the JWT, loads the user, and rejects the request if the user is
  inactive or suspended (`403`).

## Authorization (RBAC)

Three roles: `student`, `moderator`, `admin` (`models/user.py::UserRole`).
`auth/deps.py::require_roles(*roles)` is a FastAPI dependency factory used as:

```python
require_moderator = require_roles(UserRole.MODERATOR, UserRole.ADMIN)
require_admin = require_roles(UserRole.ADMIN)
```

Routers apply these per-endpoint — e.g. `/api/admin/*` requires `require_admin`,
`/api/moderation/reports` (viewing the queue) requires `require_moderator`,
content deletion checks "are you the author OR a moderator/admin" inline.
This is verified by tests (`tests/test_moderation_and_admin.py`): a student
gets `403` from every admin/moderator-only endpoint.

## Anonymous identity protection

```
Real User (private: email, password hash)
     │  User.id (internal only)
     ▼
AnonymousProfile ("Anonymous Fox #4821" — the only thing ever shown publicly)
     │
     ▼
Public Post / Comment / Room message
```

- The anonymous persona is generated once at registration
  (`services/anonymous_identity.py::generate_anonymous_profile`) and reused
  for every anonymous post that user makes — public, but never traceable to
  a username from the API response.
- The **only** way to resolve a persona back to a real account is
  `POST /api/moderation/identity-reveal/{anonymous_profile_id}`, which:
  requires moderator/admin role, requires a documented `reason` string, and
  writes an `IdentityAccessLog` row (`accessed_by`, `anonymous_profile_id`,
  `reason`, timestamp) **before** returning the real user — so every reveal
  is permanently auditable, satisfying the spec's "record sensitive
  moderation access in an audit log" requirement.

## Input validation & injection defenses

- **SQL injection**: every database query in this project goes through the
  SQLAlchemy ORM (`db.query(...)`, `db.get(...)`) — there is no string-built
  SQL anywhere in the codebase, so user input is always sent as a bound
  parameter, never concatenated into a query.
- **XSS**: all free-text user input (post text, comments, community
  names/descriptions, room titles/messages, event/opportunity/marketplace
  text) is passed through `security/sanitize.py::sanitize_text`, which
  HTML-escapes it (`&lt;script&gt;` instead of `<script>`) before it's
  stored. The frontend also escapes on render (`js/api.js::escapeHtml`) as a
  second layer. Verified by `tests/test_posts.py::test_xss_input_is_escaped`.
- **Pydantic schemas** (`schemas/*.py`) validate every request body: password
  strength (8+ chars, letters + numbers), username format, non-empty post
  text with a max length, poll option counts, AI prompt length bounds, etc.
  Invalid input never reaches a router's business logic — it's rejected with
  `422` before that.

## File upload security

`security/uploads.py::save_upload`:
- Rejects any `content_type` not on an explicit allowlist
  (`ALLOWED_IMAGE_TYPES`/`ALLOWED_VIDEO_TYPES` in config).
- Enforces a max file size (`MAX_UPLOAD_SIZE_MB`) and rejects empty files.
- **Never uses the client-supplied filename** for the path on disk — every
  uploaded file is renamed to a random UUID with an extension derived from
  its (validated) content type, which eliminates path traversal
  (`../../etc/passwd`) and overwrite attacks entirely.

## Rate limiting

`security/rate_limit.py::RateLimitMiddleware` — an in-memory sliding-window
limiter keyed by the caller's bearer token (or IP if unauthenticated).
Deliberately simple (a `dict` of `deque`s, no Redis) because a single-process
demo deployment doesn't need a distributed limiter, and the mechanism is easy
to explain end-to-end in a viva.

## AI-specific security

- **API keys never reach the frontend.** All AI calls happen inside FastAPI
  route handlers (`routers/ai_studio.py`) through `app.ai.get_ai_provider()`;
  the browser only ever sees the generated *result*, never a provider key.
- **Per-user daily request limits** (`AI_DAILY_REQUEST_LIMIT_PER_USER`,
  checked in `ai_studio.py::_check_and_log`) prevent one account from
  exhausting quota/budget.
- **Prompt length is validated** by Pydantic (max 500 chars) before it ever
  reaches a provider call.
- **Generated content is moderated** before being handed back to the user —
  `ai_studio.py::generate_text` runs the AI's own output through
  `services/moderation.py::evaluate_text` and refuses to return flagged
  content (`422`).
- **Usage is logged without retaining full prompts** — `AIRequest.prompt_excerpt`
  stores only the first 120 characters, for auditing/rate-limit purposes, not
  full conversation replay.
- The AI providers (`ai/mock_provider.py`, `ai/openai_provider.py`) only ever
  return text/an image URL — there is no code path that lets generated
  content execute as a shell command or modify application logic.

## Privacy & user controls

- `User.is_discoverable` — a user can opt out of the matching system
  entirely (`PATCH /api/auth/me`); `services/recommendation.py::find_candidates`
  returns nothing for a non-discoverable user and never surfaces them as a
  candidate to others.
- `Block` — blocking another user prevents direct messages between the two
  (`routers/messaging.py`) and removes them from each other's match
  candidates.
- `Report` — every content type (post, comment, reel, story, user, message)
  can be reported; reports feed the moderation queue, they never trigger an
  automatic takedown by themselves.
- Email, password hash and internal numeric user id are never included in
  any response that isn't the authenticated user's own `/api/auth/me` (or an
  admin-only endpoint).

## What's explicitly *not* claimed

Per the project's own ground rules: this is a B.Tech demo, not a hardened
production system. CORS is currently permissive (`allow_origins=["*"]`) for
local/demo convenience — a real deployment would restrict this to a known
frontend origin. The rate limiter is per-process and in-memory, not
distributed. See `docs/FUTURE_SCOPE.md` for what a production hardening pass
would add.
