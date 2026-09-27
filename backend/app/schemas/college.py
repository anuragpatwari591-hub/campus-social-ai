from pydantic import BaseModel


class CampusOut(BaseModel):
    id: int
    name: str
    institution_id: int

    model_config = {"from_attributes": True}


class InstitutionOut(BaseModel):
    id: int
    name: str
    short_name: str | None
    institution_type: str
    city: str
    region: str
    country: str
    is_verified: bool
    campuses: list[CampusOut] = []

    model_config = {"from_attributes": True}


class InstitutionSearchResult(BaseModel):
    id: int
    name: str
    short_name: str | None
    city: str
    country: str
    matched_alias: str | None = None
