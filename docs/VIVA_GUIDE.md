# Viva Guide — anticipated questions & short answers

### "Why FastAPI instead of Flask/Django?"
Pydantic models give free request validation and auto-generated interactive
docs (`/docs`) without extra boilerplate, which matters for demoing a large
API surface quickly. The routing/dependency-injection style is still close
enough to Flask that it doesn't introduce a steep learning curve.

### "Why PostgreSQL and not MySQL?"
Both would work equally well for this schema. Postgres was chosen because
it's free, well-documented, has strong constraint/transaction support, and
the same SQLAlchemy models would work unchanged against MySQL — only the
`DATABASE_URL` and driver package (`psycopg2` → `pymysql`) would need to
change. That portability is exactly why the ORM was used instead of raw SQL.

### "How does authentication work, end to end?"
Register → password hashed with bcrypt, stored, never in plaintext. Login →
password verified against the hash, a JWT is issued containing the user id
and role, signed with a server-side secret. Every subsequent request sends
`Authorization: Bearer <token>`; `get_current_user` decodes it, loads the
user from the database, and rejects the request if the token is invalid,
expired, or the account is suspended.

### "How do you prevent SQL injection?"
By never writing raw SQL. Every query goes through the SQLAlchemy ORM
(`db.query(Model).filter(...)`), which parameterizes all values
automatically — user input is always sent to Postgres as a bound parameter,
never string-concatenated into a query.

### "How does the anonymous 'Tea' feature actually hide identity?"
Each user gets one `AnonymousProfile` (a persona like "Anonymous Fox #4821")
generated at registration. Anonymous posts are stored with the real
`author_id` internally (so the owner can still manage their own post), but
every API response for anonymous content substitutes the persona's display
name — the real username is never serialized. The only way back to the real
account is a moderator-only endpoint that logs the access.

### "What stops a moderator from abusing the identity-reveal feature?"
Nothing stops the *database action* — a moderator with legitimate access can
always look things up — but every reveal call requires a documented `reason`
string and is written to `IdentityAccessLog` (who, which persona, why, when)
before the real user is returned. That audit trail is the accountability
mechanism, matching how real moderation systems are usually built (not
prevention, but non-repudiable logging).

### "Is the AI actually doing anything, or is it fake?"
It's real, through a provider abstraction. The default `MockAIProvider`
generates deterministic template-based text/placeholder images entirely
offline (no API key needed for demoing), and `OpenAIProvider` implements the
exact same interface against a real hosted model — switching between them is
one environment variable (`AI_PROVIDER`). The moderation, rate-limiting and
"user must approve before publishing" flow around the AI is identical either
way.

### "Explain the matching score formula."
`score = 0.4·interest_similarity + 0.2·college_similarity + 0.2·community_similarity + 0.2·activity_similarity`,
each term normalized to `[0,1]` (Jaccard similarity for interests/communities,
a same-campus boolean, and a normalized activity-level difference). The
weights are stored per matching mode and nudged slightly after every
connect/skip decision, but the formula itself is always visible — the app
shows the full breakdown to the user, not just a final percentage.

### "Is that 'self-learning' really machine learning?"
No — and the docs are explicit about that. It's a bounded, explainable
moving-average adjustment to four weights that always sum to 1. It's the
right level of "adaptive" for a demonstrable, defensible B.Tech project
without claiming a learned model that doesn't exist.

### "How would this scale to real production traffic?"
It wouldn't, as-is, and the docs don't claim otherwise (`docs/FUTURE_SCOPE.md`).
The rate limiter is in-memory/per-process; there's no caching layer, no CDN
for media, no horizontal scaling story, no distributed job queue for
video/image processing. The architecture is intentionally modular
(routers → services → ORM, and a swappable AI provider) so those pieces
could be added later without a rewrite — but they are not implemented here.

### "What's the biggest security gap you're aware of?"
CORS is currently wide open (`allow_origins=["*"]`) for local demo
convenience, and the rate limiter can be reset by restarting the process
since it's in-memory. Both are called out explicitly in `docs/SECURITY.md`
rather than glossed over.

### "Why did you build Reels/Stories as simple file upload + playback instead of a real video pipeline?"
Building a transcoding/adaptive-bitrate pipeline is disproportionate to a
B.Tech course's scope and wouldn't be something a viva panel expects a
student to have built solo. The schema and API are designed so that piece
could be swapped in later (the `video_url` field doesn't care how it was
produced) without changing anything else.
