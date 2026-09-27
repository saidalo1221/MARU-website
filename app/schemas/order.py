from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.models.enums import OrderStatus
from app.models.order import OrderType

EmailStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, to_lower=True, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"),
]

# Acquisition channels CRM push must distinguish (PRD section 26).
OrderSource = Literal[
    "website", "instagram", "facebook", "google", "marketplace", "whatsapp", "telegram", "direct", "referral"
]

# Wired-up gateways (app/services/payment/registry.py). Uzum Pay isn't listed
# yet — its merchant API wasn't implemented (see session notes for why).
PaymentMethod = Literal["payme", "click", "stripe", "paypal"]


class CheckoutRequest(BaseModel):
    order_type: OrderType = OrderType.INDIVIDUAL

    first_name: str
    last_name: str
    phone: str
    email: EmailStr
    country: str
    city: str
    address_line: str
    postal_code: str
    delivery_method: str
    payment_method: PaymentMethod
    source: OrderSource = "website"
    promo_code: str | None = None

    company_name: str | None = None
    company_reg_number: str | None = None
    company_tax_number: str | None = None
    company_address: str | None = None
    contact_person: str | None = None


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku_id: int | None
    warehouse_id: int | None
    sku_code_snapshot: str
    product_name_snapshot: str
    variant_name_snapshot: str | None
    unit_price: Decimal
    quantity: int
    line_total: Decimal
    currency: str


class OrderStatusHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    from_status: OrderStatus | None
    to_status: OrderStatus
    note: str | None
    created_at: datetime


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    note: str | None = None


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_number: str
    status: OrderStatus
    order_type: OrderType
    currency: str
    subtotal_amount: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    delivery_amount: Decimal
    total_amount: Decimal
    first_name: str
    last_name: str
    email: str
    country: str
    city: str
    source: str
    payment_method: str
    created_at: datetime
    items: list[OrderItemOut]
    status_history: list[OrderStatusHistoryOut]


PaymentReferenceKind = Literal["redirect_url", "client_secret", "provider_order_id"]


class PaymentInitiationOut(BaseModel):
    method: PaymentMethod
    reference_kind: PaymentReferenceKind
    reference: str


class CheckoutOut(OrderOut):
    """The one response allowed to contain a payment reference and guest
    access token. Neither is included in normal order-history responses."""

    payment: PaymentInitiationOut
    guest_order_token: str | None = None


class PaymentMethodOut(BaseModel):
    id: str
    display_name: str
    enabled: bool
    reference_kind: PaymentReferenceKind | None = None
    reason: str | None = None
