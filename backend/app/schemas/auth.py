"""Auth-related request/response DTOs."""

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class PharmacyRegistration(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    license_number: str = Field(min_length=2, max_length=80)
    address: str = Field(min_length=2, max_length=255)
    phone: str = Field(min_length=4, max_length=40)


class DistributorRegistration(BaseModel):
    company_name: str = Field(min_length=2, max_length=160)
    license_number: str = Field(min_length=2, max_length=80)
    address: str = Field(min_length=2, max_length=255)
    phone: str = Field(min_length=4, max_length=40)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=120)
    role: UserRole
    # Exactly one of these must be present, matching the role.
    pharmacy: PharmacyRegistration | None = None
    distributor: DistributorRegistration | None = None


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class CurrentUser(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    pharmacy_id: int | None = None
    distributor_id: int | None = None
