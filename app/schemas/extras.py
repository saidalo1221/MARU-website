from typing import Optional
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import RefundStatus
from app.models.quote_request import QuoteStatus
from app.models.review import ReviewStatus
from app.schemas.user import EmailStr
from app.services.i18n import ALLOWED_LOCALES


class QuoteCreate(BaseModel):
    request_type: str = Field(default="quote", pattern="^(quote|wholesale|distributor)$")
    name: str = Field(min_length=1, max_length=200)
    company: Optional[str] = Field(default=None, max_length=255)
    country: str = Field(min_length=1, max_length=100)
    city: Optional[str] = Field(default=None, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=30)
    products: Optional[str] = None
    quantity: Optional[str] = Field(default=None, max_length=100)
    comment: Optional[str] = None


class QuoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rfq_number: Optional[str]
    request_type: str
    status: QuoteStatus
    name: str
    company: Optional[str]
    country: str
    city: Optional[str]
    email: str
    phone: Optional[str]
    products: Optional[str]
    quantity: Optional[str]
    comment: Optional[str]
    proposed_price: Optional[Decimal]
    currency: Optional[str]
    valid_until: Optional[datetime]
    manager_notes: Optional[str]
    crm_lead_id: Optional[str]
    order_id: Optional[int]
    created_at: datetime


class ConvertQuoteToOrderRequest(BaseModel):
    """The RFQ form (PRD ТЗ№2 §32) never collects a shipping address, so the
    admin supplies it here at conversion time. first_name/last_name default
    to a naive split of QuoteRequest.name (first word / remainder) when
    omitted — pass them explicitly if that split would be wrong."""

    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    address_line: str = Field(min_length=1, max_length=255)
    postal_code: str = Field(min_length=1, max_length=20)
    delivery_method: str = Field(default="*", max_length=50)
    # Quotes are negotiated B2B deals, not online checkouts — default to an
    # offline settlement method rather than one of the online gateways.
    payment_method: str = Field(default="invoice", max_length=50)


class QuoteUpdate(BaseModel):
    status: Optional[QuoteStatus] = None
    proposed_price: Optional[Decimal] = Field(default=None, gt=0)
    currency: Optional[str] = Field(default=None, min_length=3, max_length=3)
    valid_until: Optional[datetime] = None
    manager_notes: Optional[str] = None


class WishlistItemOut(BaseModel):
    sku_id: int
    sku_code: str
    product_name: str
    product_slug: str
    price: Decimal
    currency: str
    available: int
    in_stock: bool


class AddressIn(BaseModel):
    label: Optional[str] = Field(default=None, max_length=50)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=1, max_length=30)
    country: str = Field(min_length=1, max_length=100)
    region: Optional[str] = Field(default=None, max_length=100)
    city: str = Field(min_length=1, max_length=100)
    address_line: str = Field(min_length=1, max_length=255)
    postal_code: str = Field(min_length=1, max_length=20)
    is_default: bool = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None


    @field_validator("region")
    @classmethod
    def _blank_region_is_none(cls, value):
        value = (value or "").strip()
        return value or None


class AddressOut(AddressIn):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    content: Optional[str] = Field(default=None, max_length=5000)


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    rating: int
    content: Optional[str]
    status: ReviewStatus
    created_at: datetime


class ReviewSummary(BaseModel):
    average_rating: Optional[float]
    count: int
    reviews: list[ReviewOut]


class ReviewModeration(BaseModel):
    status: ReviewStatus


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int]
    action: str
    entity: str
    entity_id: Optional[str]
    old_value: Optional[str]
    new_value: Optional[str]
    created_at: datetime


class RefundCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    reason: Optional[str] = None


class RefundOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    amount: Decimal
    currency: str
    reason: Optional[str]
    status: RefundStatus
    provider: str
    provider_refund_id: Optional[str]
    failure_reason: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class VerifyEmailRequest(BaseModel):
    token: str


class NotificationTemplateIn(BaseModel):
    event: str = Field(min_length=1, max_length=50)
    locale: str = Field(pattern="^(" + "|".join(ALLOWED_LOCALES) + ")$")
    channel: str = Field(default="email", max_length=20)
    subject: Optional[str] = Field(default=None, max_length=255)
    body: str = Field(min_length=1)
    is_active: bool = True


class NotificationTemplateUpdate(BaseModel):
    subject: Optional[str] = Field(default=None, max_length=255)
    body: Optional[str] = Field(default=None, min_length=1)
    is_active: Optional[bool] = None


class NotificationTemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event: str
    locale: str
    channel: str
    subject: Optional[str]
    body: str
    is_active: bool
    updated_at: datetime
