from apps.users.schemas import UserCreateBase, UserResponseBase

class OrganizationCreate(UserCreateBase):
    name: str
    city: str
    description: str | None = None
    logo_key: str | None = None

class OrganizationResponse(UserResponseBase):
    name: str
    city: str
    description: str | None