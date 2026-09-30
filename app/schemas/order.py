from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.models.enums import OrderStatus
from app.models.order import OrderType
from app.schemas.shipment import ShipmentOut

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
    promo_code: Optional[str] = None

    company_name: Optional[str] = None
    company_reg_number: Optional[str] = None
    company_tax_number: Optional[str] = None
    company_address: Optional[str] = None
    contact_person: Optional[str] = None


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku_id: Optional[int]
    warehouse_id: Optional[int]
    sku_code_snapshot: str
    product_name_snapshot: str
    variant_name_snapshot: Optional[str]
    unit_price: Decimal
    quantity: int
    line_total: Decimal
    currency: str


class OrderStatusHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    from_status: Optional[OrderStatus]
    to_status: OrderStatus
    note: Optional[str]
    created_at: datetime


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    note: Optional[str] = None


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
    shipments: list[ShipmentOut] = []


PaymentReferenceKind = Literal["redirect_url", "client_secret", "provider_order_id"]


class PaymentInitiationOut(BaseModel):
    method: PaymentMethod
    reference_kind: PaymentReferenceKind
    reference: str


class CheckoutOut(OrderOut):
    """The one response allowed to contain a payment reference and guest
    access token. Neither is included in normal order-history responses."""

    payment: PaymentInitiationOut
    guest_order_token: Optional[str] = None


class PaymentMethodOut(BaseModel):
    id: str
    display_name: str
    enabled: bool
    reference_kind: Optional[PaymentReferenceKind] = None
    reason: Optional[str] = None
