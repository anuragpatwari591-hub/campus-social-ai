# Future Scope & Known Limitations

This build intentionally stops short of a commercial-grade platform. What
follows is implemented vs. explicitly deferred, so nothing here is
overstated in a report or demo.

## Implemented in this build

- Registration/login, JWT auth, role-based access (student/moderator/admin)
- Global college directory (countries → regions → cities → institutions →
  campuses) with exact/alias/fuzzy search, seeded with ~60 real institutions
- Campus pages, home feed, anonymous "Tea" feed with categories
- Comments, reactions, polls with anonymous voting
- Reels and Stories (upload + playback; see limitations below)
- AI Creation Studio: text/caption, image, sticker, meme generation, and a
  data-grounded Campus Assistant — through a swappable provider abstraction
- Explainable matching/recommendation with a simple feedback-adaptive
  weighting scheme
- Direct messaging, communities, temporary text-based rooms
- Events, opportunities, marketplace listings
- Reporting, moderator review queue, moderation actions, audit-logged
  anonymous-identity reveal
- Admin dashboard with live analytics (never fabricated numbers), user/role
  management, sponsor & campaign management (simulated budget)
- Automated tests (pytest) covering the main flows and key negative/security
  cases

## Explicitly out of scope (and why)

| Feature | What's here now | What a production version would add |
|---|---|---|
| Video processing | Direct upload + `<video>` playback | Transcoding, adaptive bitrate, thumbnail generation, CDN delivery |
| Rooms | Polling-based text chat (refetch every few seconds) | WebSocket-based real-time messaging; optional audio/video (the schema already separates `Room`/`RoomMember`/`RoomMessage` so this can be layered in without a schema change) |
| AI image generation | Deterministic offline placeholder by default | A real hosted image model (the `OpenAIProvider` implementation already supports this — just needs an API key) |
| Recommendation | Hand-weighted, feedback-nudged formula | A learned ranking model trained on real interaction data at scale |
| Monetization | Sponsor/Campaign tables + admin CRUD, simulated budget field | A real payment gateway, billing, invoicing, fraud checks |
| Rate limiting | In-memory, per-process sliding window | A distributed limiter (e.g. Redis-backed) for multi-instance deployments |
| CORS | Permissive (`*`) for local/demo convenience | Locked to the actual deployed frontend origin(s) |
| Deployment | Local dev server (uvicorn) | Containerized, load-balanced, managed database, secrets manager, HTTPS termination, monitoring/alerting |
| College directory | ~60 seeded institutions across India and internationally | A full official dataset (e.g. AISHE for India, IPEDS for the US) — the schema already supports adding more without any change |
| Mobile | Responsive web (works on mobile browsers) | Native iOS/Android apps |
| Institutional verification | Admin can mark an institution "verified" manually | A real verification workflow (domain-based email verification, official registration document upload) |

## Honesty notes

- Analytics in the admin dashboard are always computed live from the
  database — there is no hard-coded or simulated statistic anywhere in that
  view.
- The AI moderation/recommendation systems are explainable rule-based and
  formula-based systems, not trained machine learning models — this is
  called out directly rather than implied to be more sophisticated than it
  is.
- No claim is made that this system has been load-tested or would support
  "millions of users" — it has been tested with the automated test suite and
  manual/browser-driven smoke testing only.
