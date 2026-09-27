from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import RefundStatus
from app.models.quote_request import QuoteStatus
from app.models.review import ReviewStatus
from app.schemas.user import EmailStr
from app.services.i18n import ALLOWED_LOCALES


class QuoteCreate(BaseModel):
    request_type: str = Field(default="quote", pattern="^(quote|wholesale|distributor)$")
    name: str = Field(min_length=1, max_length=200)
    company: str | None = Field(default=None, max_length=255)
    country: str = Field(min_length=1, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    products: str | None = None
    quantity: str | None = Field(default=None, max_length=100)
    comment: str | None = None


class QuoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rfq_number: str | None
    request_type: str
    status: QuoteStatus
    name: str
    company: str | None
    country: str
    city: str | None
    email: str
    phone: str | None
    products: str | None
    quantity: str | None
    comment: str | None
    proposed_price: Decimal | None
    currency: str | None
    valid_until: datetime | None
    manager_notes: str | None
    crm_lead_id: str | None
    order_id: int | None
    created_at: datetime


class ConvertQuoteToOrderRequest(BaseModel):
    """The RFQ form (PRD ТЗ№2 §32) never collects a shipping address, so the
    admin supplies it here at conversion time. first_name/last_name default
    to a naive split of QuoteRequest.name (first word / remainder) when
    omitted — pass them explicitly if that split would be wrong."""

    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    address_line: str = Field(min_length=1, max_length=255)
    postal_code: str = Field(min_length=1, max_length=20)
    delivery_method: str = Field(default="*", max_length=50)
    # Quotes are negotiated B2B deals, not online checkouts — default to an
    # offline settlement method rather than one of the online gateways.
    payment_method: str = Field(default="invoice", max_length=50)


class QuoteUpdate(BaseModel):
    status: QuoteStatus | None = None
    proposed_price: Decimal | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    valid_until: datetime | None = None
    manager_notes: str | None = None


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
    label: str | None = Field(default=None, max_length=50)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=1, max_length=30)
    country: str = Field(min_length=1, max_length=100)
    city: str = Field(min_length=1, max_length=100)
    address_line: str = Field(min_length=1, max_length=255)
    postal_code: str = Field(min_length=1, max_length=20)
    is_default: bool = False
    latitude: float | None = None
    longitude: float | None = None


class AddressOut(AddressIn):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    content: str | None = Field(default=None, max_length=5000)


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    rating: int
    content: str | None
    status: ReviewStatus
    created_at: datetime


class ReviewSummary(BaseModel):
    average_rating: float | None
    count: int
    reviews: list[ReviewOut]


class ReviewModeration(BaseModel):
    status: ReviewStatus


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    action: str
    entity: str
    entity_id: str | None
    old_value: str | None
    new_value: str | None
    created_at: datetime


class RefundCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    reason: str | None = None


class RefundOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    amount: Decimal
    currency: str
    reason: str | None
    status: RefundStatus
    provider: str
    provider_refund_id: str | None
    failure_reason: str | None
    created_at: datetime
    completed_at: datetime | None


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
    subject: str | None = Field(default=None, max_length=255)
    body: str = Field(min_length=1)
    is_active: bool = True


class NotificationTemplateUpdate(BaseModel):
    subject: str | None = Field(default=None, max_length=255)
    body: str | None = Field(default=None, min_length=1)
    is_active: bool | None = None


class NotificationTemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event: str
    locale: str
    channel: str
    subject: str | None
    body: str
    is_active: bool
    updated_at: datetime
