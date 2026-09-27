import re

from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    username: str
    campus_id: int | None = None
    branch: str | None = None
    year_of_study: int | None = None
    interests: list[str] = []

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("Password must contain both letters and numbers")
        return v

    @field_validator("username")
    @classmethod
    def username_format(cls, v: str) -> str:
        if not re.fullmatch(r"[a-zA-Z0-9_]{3,30}", v):
            raise ValueError("Username must be 3-30 characters: letters, numbers, underscore only")
        return v


class ProfileUpdate(BaseModel):
    bio: str | None = None
    is_discoverable: bool | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserPublic"


class UserPublic(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    campus_id: int | None
    bio: str | None
    avatar_url: str | None
    is_adult_verified: bool
    is_discoverable: bool

    model_config = {"from_attributes": True}


TokenResponse.model_rebuild()
