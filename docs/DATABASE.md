# Database Design

Relational database (PostgreSQL), accessed exclusively through the
SQLAlchemy ORM (`backend/app/models/`). 43 tables, grouped below by domain
with their key relationships. Every foreign key relationship listed here is
enforced at the schema level (`ForeignKey(...)` in SQLAlchemy → a real `FK`
constraint in Postgres).

## College directory (geo hierarchy)

```
Country (1) ──< (many) Region ──< (many) City ──< (many) Institution ──< (many) Campus
                                                        │
                                                        └──< (many) InstitutionAlias
```

- **Why a 5-level hierarchy instead of one flat "colleges" table?** It mirrors
  how the data is naturally structured (a country has many states, a state
  has many cities, a city has many institutions, an institution can have
  multiple physical campuses) and lets search/browse be scoped at any level
  ("show me all institutions in India" is one `JOIN`, not a string match).
- `InstitutionAlias` is what makes "IIT KGP" resolve to "Indian Institute of
  Technology Kharagpur" — see `docs/AI.md`... actually see
  `backend/app/routers/colleges.py` for the exact search algorithm (it's not
  AI, just SQL `ILIKE` + a fuzzy fallback).

## Identity & anonymity

```
User (1) ──1:1── AnonymousProfile
User (1) ──< (many) UserInterest
User (1) ──< (many) Block (as blocker or blocked)
User (1) ──< (many) Notification
```

- `User.hashed_password` — never a plaintext password, always a bcrypt hash.
- `AnonymousProfile.display_name` (e.g. `"Anonymous Fox #4821"`) is generated
  once at registration (`services/anonymous_identity.py`) and reused for
  every anonymous post/comment/room-message that user makes. The *only* link
  from the public persona back to the real account is the foreign key
  `AnonymousProfile.user_id`, which the API never returns for anonymous
  content, and which can only be resolved by a moderator through a dedicated
  endpoint that writes to `IdentityAccessLog` (see `docs/SECURITY.md`).

## Content

```
Post (1) ──< (many) PostMedia
Post (1) ──< (many) Comment
Post (1) ──1:1── Poll ──< (many) PollOption ──< (many) PollVote
Reel (1) ──< (many) Comment   (via Comment.reel_id)
Story (1) ──< (many) StoryView
Reaction        -- polymorphic: (target_type, target_id) instead of one FK per content type,
                   so the same table serves posts, comments, reels and stories
```

- `Post.is_anonymous` + `Post.category` (an enum: trending, funny, confession,
  relationships, academic, campus, events, food, sports, questions) implement
  the "Tea" feature on the same table as normal posts, rather than a
  duplicate parallel schema — a normal post is just `is_anonymous=False`.
- `Reaction` and `Report` use a **polymorphic association**
  (`target_type` + `target_id` columns instead of a separate foreign key per
  content type) so "like a post" and "like a reel" share one table and one
  API shape, instead of four near-identical `post_reactions`,
  `reel_reactions`, ... tables.

## Social graph

```
Community (1) ──< (many) CommunityMember
Room (1) ──< (many) RoomMember, RoomMessage
Match          -- a computed, ranked candidate: user_id, candidate_id, score, score_breakdown (JSON)
Connection     -- a mutual, accepted relationship: requester_id, addressee_id, status
Conversation (1) ──< (many) ConversationParticipant, Message
```

- `Match` rows are a **log of what the algorithm showed the user and what
  they decided**, not just "the current match list" — that history is what
  `services/recommendation.py` reads to nudge `RecommendationWeight` after a
  connect/skip decision (see `docs/AI.md`).

## Moderation

```
Report ──< (many) ModerationAction (via report_id, optional)
IdentityAccessLog   -- audit trail for every anonymous-identity reveal
```

## AI usage

```
AIRequest        -- one row per AI Studio call: type, provider, model, truncated prompt, success
AIFeedback        -- optional: was the generated content actually used, and how it was rated
RecommendationWeight  -- the current, explainable weight profile per matching mode
```

`AIRequest.prompt_excerpt` is truncated to 120 characters by design — the
spec explicitly calls out not retaining full prompts indefinitely.

## Campus life & monetization

```
Event (1) ──< (many) EventRegistration
Opportunity, MarketplaceListing   -- straightforward CRUD, scoped by campus_id
Sponsor (1) ──< (many) Campaign   -- simulated budget/impressions, no real payment processing
```

## Design decisions worth defending in a viva

1. **Why not one giant `content` table with a `type` column for
   posts/reels/stories?** Each has different fields (a Reel needs
   `video_url`/`thumbnail_url`, a Poll needs options and votes) — forcing
   them into one table would mean dozens of always-`NULL` columns per row.
   Separate tables with a shared *pattern* (polymorphic reactions/reports)
   gets the reuse without the sparse-table problem.
2. **Why store `score_breakdown` as a JSON string on `Match` instead of four
   more columns?** It's a snapshot of *why* a score was what it was at that
   moment, purely for display/audit/feedback — not something the database
   ever needs to filter or join on, so a serialized blob is the simpler,
   honest choice for that field.
3. **Indexes**: `User.email`, `User.username`, `Post.created_at`,
   `Institution.name` and `InstitutionAlias.alias` are indexed — the columns
   actually used in `WHERE`/`ORDER BY` on the hot paths (login, feed
   pagination, college search).
