from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from apps.employment.enums import EntityType, MatchConfidence, MatchStatus, ProfileChangeSource, ReactionAction, ReactionSource, VacancyStatus


class TgCheckRequest(BaseModel):
    telegram_id: str
    telegram_username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class TgCheckResponse(BaseModel):
    telegram_id: str
    is_blocked: bool
    is_linked: bool
    available_roles: list[str]


class OrganizationEmailValidateRequest(BaseModel):
    email: EmailStr


class EmailValidateResponse(BaseModel):
    email: EmailStr
    available: bool


class EmploymentOrganizationRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str
    city: str
    description: Optional[str] = None
    website: Optional[str] = None
    telegram_id: Optional[str] = None


class VacancyShort(BaseModel):
    id: int
    position_title: str
    status: VacancyStatus

    model_config = ConfigDict(from_attributes=True)


class OrganizationMeResponse(BaseModel):
    id: int
    email: EmailStr
    name: str
    city: str
    vacancies: list[VacancyShort]


class CandidateRegisterRequest(BaseModel):
    email: Optional[EmailStr] = None
    description_json: dict[str, Any] = Field(default_factory=dict)
    links: list[str] = Field(default_factory=list)
    category: Optional[str] = None
    city: Optional[str] = None
    resume_text: Optional[str] = None
    telegram_id: Optional[str] = None

    @model_validator(mode="after")
    def normalize_legacy(self) -> "CandidateRegisterRequest":
        if not self.email and self.mail:
            self.email = self.mail
        if not self.email:
            raise ValueError("email is required")
        return self


class CandidateUpdateRequest(BaseModel):
    description_json: Optional[dict[str, Any]] = None
    links: Optional[list[str]] = None
    category: Optional[str] = None
    city: Optional[str] = None
    resume_text: Optional[str] = None


class CandidateResponse(BaseModel):
    id: int
    email: EmailStr
    description_json: dict[str, Any]
    links: list[str]
    category: Optional[str]
    city: Optional[str]
    resume_text: Optional[str]
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class CandidateHistoryResponse(BaseModel):
    version_no: int
    snapshot_json: dict[str, Any]
    change_source: ProfileChangeSource
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VacancyCreateRequest(BaseModel):
    position_title: Optional[str] = None
    role_search: Optional[str] = None
    description_json: dict[str, Any] = Field(default_factory=dict)
    city: Optional[str] = None
    employment_type: Optional[str] = None
    is_remote: bool = False

    @model_validator(mode="after")
    def normalize_legacy(self) -> "VacancyCreateRequest":
        if not self.position_title and self.role_search:
            self.position_title = self.role_search
        if not self.position_title:
            raise ValueError("position_title is required")
        return self


class VacancyUpdateRequest(BaseModel):
    position_title: Optional[str] = None
    role_search: Optional[str] = None
    description_json: Optional[dict[str, Any]] = None
    city: Optional[str] = None
    employment_type: Optional[str] = None
    is_remote: Optional[bool] = None


class VacancyStatusUpdateRequest(BaseModel):
    status: VacancyStatus


class VacancyResponse(BaseModel):
    id: int
    organization_id: int
    position_title: str
    description_json: dict[str, Any]
    status: VacancyStatus
    city: Optional[str]
    employment_type: Optional[str]
    is_remote: bool

    model_config = ConfigDict(from_attributes=True)


class RecommendationItem(BaseModel):
    entity_id: int
    match_score: float
    match_percent_display: int
    confidence: MatchConfidence
    explanation: dict[str, Any]


class ReactionRequest(BaseModel):
    initiator_entity_type: EntityType
    initiator_entity_id: int
    target_entity_type: EntityType
    target_entity_id: int
    vacancy_id: Optional[int] = None
    action: ReactionAction
    source: ReactionSource = ReactionSource.WEB


class ReactionResponse(BaseModel):
    reaction_id: int
    match_id: Optional[int] = None
    match_status: Optional[MatchStatus] = None
    idempotent_replay: bool = False


class MatchResponse(BaseModel):
    id: int
    candidate_id: int
    organization_id: int
    vacancy_id: int
    status: MatchStatus
    matched_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class MatchStatusUpdateRequest(BaseModel):
    status: MatchStatus
