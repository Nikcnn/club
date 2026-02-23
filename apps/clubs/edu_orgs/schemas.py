from typing import Optional, Dict, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict




class EducationalOrganizationBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    city: str
    description: Optional[str] = None
    department: List[str] = None
    logo_key: Optional[str] = None
    website: Optional[str] = None
    social_links: Optional[Dict[str, str]] = Field(default_factory=dict)

class EducationalOrganizationUpdate(BaseModel):
    name: Optional[str] = Field(..., min_length=2, max_length=100)
    city: Optional[str]
    description: Optional[str] = None
    department: List[str] = None
    logo_key: Optional[str] = None
    website: Optional[str] = None
    social_links: Optional[Dict[str, str]] = Field(default_factory=dict)


