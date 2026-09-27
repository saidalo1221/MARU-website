from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.models.enums import CustomerType, UserRole

EmailStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, to_lower=True, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"),
]


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    customer_type: CustomerType = CustomerType.RETAIL


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    mfa_code: str | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    first_name: str | None
    last_name: str | None
    phone: str | None
    role: UserRole
    customer_type: CustomerType
    is_active: bool
    email_verified: bool
    mfa_enabled: bool


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MfaSetupOut(BaseModel):
    secret: str
    provisioning_uri: str


class MfaCodeRequest(BaseModel):
    code: str


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class AdminVerifyRequest(BaseModel):
    email: EmailStr
    code: str


class AdminPromoteRequest(BaseModel):
    email: EmailStr
    role: UserRole
