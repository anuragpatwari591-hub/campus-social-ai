from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.auth.security import hash_password, verify_password, create_access_token
from app.auth.deps import get_current_user
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserPublic, ProfileUpdate
from app.services.anonymous_identity import generate_anonymous_profile

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter_by(username=payload.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        username=payload.username,
        campus_id=payload.campus_id,
        branch=payload.branch,
        year_of_study=payload.year_of_study,
    )
    db.add(user)
    db.flush()  # assign user.id before creating dependent rows

    generate_anonymous_profile(db, user)

    from app.models.user import UserInterest
    for interest in payload.interests:
        db.add(UserInterest(user_id=user.id, interest=interest.strip().lower()))

    db.commit()
    db.refresh(user)

    token = create_access_token(subject=str(user.id), role=user.role.value)
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        # Same error for "no such user" and "wrong password" so login can't be
        # used to enumerate registered emails.
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if user.is_suspended:
        raise HTTPException(status_code=403, detail="Account suspended")

    token = create_access_token(subject=str(user.id), role=user.role.value)
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user))


@router.get("/me", response_model=UserPublic)
def me(current_user: User = Depends(get_current_user)):
    return UserPublic.model_validate(current_user)


@router.patch("/me", response_model=UserPublic)
def update_me(payload: ProfileUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.bio is not None:
        current_user.bio = payload.bio[:300]
    if payload.is_discoverable is not None:
        current_user.is_discoverable = payload.is_discoverable
    db.commit()
    db.refresh(current_user)
    return UserPublic.model_validate(current_user)
