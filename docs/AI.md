# AI Integration

## Provider abstraction

```python
class AIProvider(ABC):
    def generate_text(self, prompt, style="casual", max_words=60) -> str: ...
    def generate_image(self, prompt) -> str: ...       # returns a URL
    def generate_sticker(self, prompt) -> str: ...       # returns a URL
    def moderate_content(self, text) -> dict: ...          # {"flagged": bool, "categories": [...]}
    def generate_embedding(self, text) -> list[float]: ...
```

(`backend/app/ai/base.py`)

Every AI feature in the app calls `app.ai.get_ai_provider()` and uses this
interface — never a vendor SDK directly inside a route. That buys three
things:

1. **The provider can be swapped with one environment variable**
   (`AI_PROVIDER=mock` → `AI_PROVIDER=openai`), with zero code changes to
   routers, schemas or the frontend.
2. **API keys stay server-side.** `AI_API_KEY` lives in `backend/.env` and is
   read by `OpenAIProvider`; the browser only ever receives generated
   results.
3. **The whole platform demos offline.** The default `MockAIProvider`
   (`ai/mock_provider.py`) needs no API key and no internet access — it uses
   deterministic templates (seeded by a hash of the prompt, so the same
   prompt+style always produces the same output, which is useful for
   grading/demoing consistently) plus a keyword-based moderation check.

`OpenAIProvider` (`ai/openai_provider.py`) implements the same interface
against the real OpenAI HTTP API using plain `httpx` calls (not the full
vendor SDK), so the request/response shape is fully visible in one file for
a viva walkthrough, rather than hidden inside a library.

## AI Creation Studio features

| Feature | Endpoint | Notes |
|---|---|---|
| AI Text / Caption | `POST /api/ai/text` | style: funny, casual, professional, genz, short, emotional |
| AI Image | `POST /api/ai/image` | mock provider returns a deterministic placeholder image |
| AI Sticker | `POST /api/ai/sticker` | same pipeline as image, different prompt framing |
| AI Meme text | `POST /api/ai/meme` | short, funny-style text generation |
| Campus Assistant | `POST /api/ai/assistant` | see below — **not** free-form generation |

Every generated result is returned to the frontend for the user to review;
nothing is auto-published. The AI Creation Studio UI (`frontend/ai-studio.html`)
always shows a "Result (review before using)" section with a copy/use action,
never a direct "post" button on the raw output.

## The Campus Assistant is rule-based, not a chatbot

`POST /api/ai/assistant` deliberately does **not** hand the question to the
generative model. Instead it pattern-matches the question ("event", "communit",
"trend"/"digest") and answers by **querying real application data** — upcoming
`Event` rows, `Community` rows, recent `Post` rows — and returns a `source`
field labelling exactly where the answer came from
(`application_data:events`, `user_generated_content:posts`, ...). This is a
direct implementation of the spec's requirement that the assistant "must
clearly distinguish application data, user-generated content, and
AI-generated suggestions" and never present an anonymous rumor as a verified
fact.

## Moderation pipeline

```
Rule-based keyword filter  +  AI moderation provider  +  User reports  +  Admin review
```

`services/moderation.py::evaluate_text` combines a keyword-based check
(`security/sanitize.py`: abuse keywords, phone numbers, emails) with
`provider.moderate_content(text)`. It's called:
- **at post-creation time** (`routers/posts.py`) — a flagged post is stored
  with `is_flagged=True` and surfaced in the admin dashboard, **not**
  deleted automatically;
- **on AI-generated text before it's returned to the user**
  (`routers/ai_studio.py::generate_text`) — flagged generations are rejected
  outright (`422`) rather than shown.

Nothing is auto-deleted purely from a moderation score. High-risk content
stays visible to human moderators via `GET /api/moderation/reports` and is
only removed through `POST /api/moderation/actions`, which requires a
moderator/admin role and is itself recorded in `ModerationAction` for audit.

## Recommendation / matching algorithm

```
Match Score = w_interests · interest_similarity
            + w_college   · college_similarity
            + w_community · community_similarity
            + w_activity  · activity_similarity
```

Every term is a value in `[0, 1]`:

- `interest_similarity` — Jaccard similarity (`|A ∩ B| / |A ∪ B|`) between
  the two users' `UserInterest` sets.
- `college_similarity` — `1.0` if both users share a `campus_id`, else `0`.
- `community_similarity` — Jaccard similarity between the two users' joined
  `Community` ids.
- `activity_similarity` — `1 - |activity(A) - activity(B)|`, where activity
  is a user's post count normalized to `[0, 1]` (capped at 20 posts).

The weights (`w_*`) sum to 1 and are stored per mode (friendship, study
buddy, gaming, ...) in `RecommendationWeight`, seeded to `0.4 / 0.2 / 0.2 /
0.2`. The score and its full breakdown are shown to the user directly
(`frontend/matching.html`) — "46% match, 67% interest similarity, 0% same
campus, ..." — so there is no black box: every number on screen traces back
to this formula (`services/recommendation.py::compute_match_score`).

### Self-learning / feedback loop

```
User decides "connect" or "skip" on a match
        ↓
record_match_feedback() reads which factors scored highest for that match
        ↓
Nudges that mode's weights up (on connect) or down (on skip),
proportional to how much each factor contributed
        ↓
Weights are re-normalized back to sum to 1
        ↓
Future match scores reflect the adjustment
```

This is a deliberately simple, explainable moving-average update — **not**
gradient descent over a neural network — chosen so it can be fully explained
and re-derived by hand in a viva, while still satisfying the "system
improves from feedback" objective from the spec. It is not an autonomous
system that rewrites its own code or security rules; it only ever adjusts
four bounded numeric weights in one database table.

## What a real AI upgrade would look like

See `docs/FUTURE_SCOPE.md` — swapping in a real hosted LLM/image model,
embedding-based semantic search (the `generate_embedding` method already
exists on the interface for this), and a learned ranking model in place of
the hand-weighted formula are all natural next steps that don't require
touching the router/schema layer, by design.
