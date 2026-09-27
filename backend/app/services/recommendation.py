"""
Explainable, B.Tech-level matching / recommendation algorithm.

    Match Score = w_interests * interest_similarity
                + w_college   * college_similarity
                + w_community * community_similarity
                + w_activity  * activity_similarity

Every term is in [0, 1] and the weights sum to 1, so the final score is also
in [0, 1] and can be shown to the user directly as "82% Interest Match" --
no black-box model, every number on screen is traceable to a formula.

Self-learning: RecommendationWeight rows start at sensible defaults (see
seed_data/seed.py) and are nudged after every "connect"/"skip" decision in
`record_match_feedback`. This is a simple, transparent moving-average update
-- not gradient descent over a neural net -- which keeps it explainable for
a viva while still satisfying the "system improves from feedback" objective.
"""
import json

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.user import User, UserInterest, Block
from app.models.social import Community, CommunityMember, MatchMode, Match, Connection
from app.models.content import Post
from app.models.ai import RecommendationWeight

DEFAULT_WEIGHTS = {"w_interests": 0.4, "w_college": 0.2, "w_community": 0.2, "w_activity": 0.2}
LEARNING_RATE = 0.03


def get_weights(db: Session, mode: str) -> RecommendationWeight:
    weight = db.query(RecommendationWeight).filter_by(mode=mode).first()
    if not weight:
        weight = RecommendationWeight(mode=mode, **DEFAULT_WEIGHTS)
        db.add(weight)
        db.commit()
        db.refresh(weight)
    return weight


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def _user_interests(db: Session, user_id: int) -> set[str]:
    rows = db.query(UserInterest.interest).filter_by(user_id=user_id).all()
    return {r[0].lower() for r in rows}


def _user_communities(db: Session, user_id: int) -> set[int]:
    rows = db.query(CommunityMember.community_id).filter_by(user_id=user_id).all()
    return {r[0] for r in rows}


def _activity_score(db: Session, user_id: int) -> float:
    """A simple 0..1 proxy for how active a user is (post count, capped)."""
    count = db.query(Post).filter_by(author_id=user_id).count()
    return min(count / 20.0, 1.0)


def compute_match_score(db: Session, user: User, candidate: User, mode: str) -> tuple[float, dict]:
    weights = get_weights(db, mode)

    interests_a, interests_b = _user_interests(db, user.id), _user_interests(db, candidate.id)
    interest_sim = _jaccard(interests_a, interests_b)

    college_sim = 1.0 if (user.campus_id and user.campus_id == candidate.campus_id) else 0.0

    communities_a, communities_b = _user_communities(db, user.id), _user_communities(db, candidate.id)
    community_sim = _jaccard(communities_a, communities_b)

    activity_a, activity_b = _activity_score(db, user.id), _activity_score(db, candidate.id)
    activity_sim = 1.0 - abs(activity_a - activity_b)

    score = (
        weights.w_interests * interest_sim
        + weights.w_college * college_sim
        + weights.w_community * community_sim
        + weights.w_activity * activity_sim
    )

    breakdown = {
        "interest_similarity": round(interest_sim, 3),
        "college_similarity": round(college_sim, 3),
        "community_similarity": round(community_sim, 3),
        "activity_similarity": round(activity_sim, 3),
        "weights": {
            "interests": weights.w_interests,
            "college": weights.w_college,
            "community": weights.w_community,
            "activity": weights.w_activity,
        },
    }
    return round(min(score, 1.0), 3), breakdown


def find_candidates(db: Session, user: User, mode: str, limit: int = 10) -> list[tuple[User, float, dict]]:
    if not user.is_discoverable:
        return []

    blocked_ids = {b.blocked_id for b in db.query(Block).filter_by(blocker_id=user.id).all()}
    blocked_ids |= {b.blocker_id for b in db.query(Block).filter_by(blocked_id=user.id).all()}

    candidates_q = (
        db.query(User)
        .filter(User.id != user.id, User.is_discoverable == True, User.is_active == True)  # noqa: E712
    )
    if mode == MatchMode.DATING.value:
        candidates_q = candidates_q.filter(User.is_adult_verified == True)  # noqa: E712

    results = []
    for candidate in candidates_q.all():
        if candidate.id in blocked_ids:
            continue
        score, breakdown = compute_match_score(db, user, candidate, mode)
        results.append((candidate, score, breakdown))

    results.sort(key=lambda r: r[1], reverse=True)
    return results[:limit]


def record_match_feedback(db: Session, match: Match, decision: str) -> None:
    """
    Nudges the mode's weights based on the outcome. If the user connected on
    a match that scored high mainly on (say) shared interests, the interest
    weight is reinforced slightly; a skip nudges it down slightly. Weights
    are re-normalized to keep summing to 1, so the score stays explainable.
    """
    match.decision = decision
    db.add(match)

    weights = get_weights(db, match.mode.value if hasattr(match.mode, "value") else match.mode)
    breakdown = json.loads(match.score_breakdown) if match.score_breakdown else {}
    direction = 1 if decision == "connect" else -1

    factor_map = {
        "w_interests": breakdown.get("interest_similarity", 0),
        "w_college": breakdown.get("college_similarity", 0),
        "w_community": breakdown.get("community_similarity", 0),
        "w_activity": breakdown.get("activity_similarity", 0),
    }
    for field, contribution in factor_map.items():
        current = getattr(weights, field)
        adjustment = LEARNING_RATE * direction * contribution
        setattr(weights, field, max(0.05, current + adjustment))

    total = sum(getattr(weights, f) for f in factor_map)
    for field in factor_map:
        setattr(weights, field, round(getattr(weights, field) / total, 4))

    db.add(weights)
    db.commit()
