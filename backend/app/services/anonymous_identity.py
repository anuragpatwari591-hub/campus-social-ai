"""
Anonymous persona generation and controlled identity-reveal.

Design (see docs/SECURITY.md):

    User (private)  --1:1-->  AnonymousProfile (public persona, e.g. "Anonymous Fox #4821")

The persona is generated once at registration and reused for every anonymous
post/comment/room-message the user makes, so the *public* identity is stable
without ever exposing the *real* identity. Only `reveal_identity` (moderator/
admin only) can map a persona back to a user, and every such lookup is
written to IdentityAccessLog for audit.
"""
import random

from sqlalchemy.orm import Session

from app.models.user import User, AnonymousProfile, ANIMALS
from app.models.moderation import IdentityAccessLog


def generate_anonymous_profile(db: Session, user: User) -> AnonymousProfile:
    for _ in range(20):  # a handful of retries is enough to dodge a collision
        animal = random.choice(ANIMALS)
        number = random.randint(1000, 9999)
        display_name = f"Anonymous {animal} #{number}"
        exists = db.query(AnonymousProfile).filter_by(display_name=display_name).first()
        if not exists:
            profile = AnonymousProfile(user_id=user.id, display_name=display_name)
            db.add(profile)
            db.flush()
            return profile
    raise RuntimeError("Could not allocate a unique anonymous persona")


def reveal_identity(db: Session, moderator: User, anonymous_profile_id: int, reason: str) -> User | None:
    profile = db.get(AnonymousProfile, anonymous_profile_id)
    if not profile:
        return None
    db.add(IdentityAccessLog(accessed_by=moderator.id, anonymous_profile_id=profile.id, reason=reason))
    db.commit()
    return db.get(User, profile.user_id)
