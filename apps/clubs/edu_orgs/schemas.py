from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class EducationalOrganizationBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    city: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    departments: list[str] = Field(default_factory=list)
    logo_key: Optional[str] = None
    website: Optional[str] = None
    social_links: dict[str, str] = Field(default_factory=dict)


class EducationalOrganizationCreate(EducationalOrganizationBase):
    pass


class EducationalOrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    departments: Optional[list[str]] = None
    logo_key: Optional[str] = None
    website: Optional[str] = None
    social_links: Optional[dict[str, str]] = None


class EducationalOrganizationResponse(EducationalOrganizationBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
