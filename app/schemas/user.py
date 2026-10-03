from typing import Annotated, Optional

import re

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.models.enums import CustomerType, UserRole

EmailStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, to_lower=True, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"),
]


def normalize_phone(value: Optional[str]) -> Optional[str]:
    """Stores phones as digits with an optional leading + (E.164 shape, PRD ТЗ№4 §80);
    spaces, dashes and brackets typed by the user are dropped. Blank becomes None."""
    value = (value or "").strip()
    if not value:
        return None
    cleaned = re.sub(r"[\s\-().]", "", value)
    if not re.fullmatch(r"\+?\d{7,15}", cleaned):
        raise ValueError("phone must have 7-15 digits, optionally starting with +")
    return cleaned


def normalize_required_phone(value: str) -> str:
    phone = normalize_phone(value)
    if phone is None:
        raise ValueError("phone is required")
    return phone


# Customers may sign in with their email or their phone number (PRD ТЗ№2 §26).
LoginIdentifier = Annotated[str, StringConstraints(strip_whitespace=True, to_lower=True, min_length=3, max_length=255)]


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    customer_type: CustomerType = CustomerType.RETAIL

    _phone = field_validator("phone")(normalize_phone)


class ProfileUpdate(BaseModel):
    """Self-service profile edit; the email is changed through support, not here."""

    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def _blank_is_none(cls, value):
        value = (value or "").strip()
        return value or None

    _phone = field_validator("phone")(normalize_phone)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class UserLogin(BaseModel):
    email: LoginIdentifier  # an email address or a phone number
    password: str
    mfa_code: Optional[str] = None
    # Opaque per-browser token the frontend generates once and persists in
    # localStorage — lets login() recognize a device it already challenged.
    device_id: Optional[str] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    phone: Optional[str]
    role: UserRole
    customer_type: CustomerType
    is_active: bool
    email_verified: bool
    mfa_enabled: bool


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginResult(BaseModel):
    """Response of POST /auth/login: either a normal Token (known device),
    or device_verification_required=True (a code was emailed; the frontend
    must then call /auth/login/verify-device)."""

    access_token: Optional[str] = None
    token_type: str = "bearer"
    device_verification_required: bool = False


class VerifyDeviceRequest(BaseModel):
    email: LoginIdentifier  # same identifier the login used
    code: str
    device_id: str


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
