from datetime import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

from app.models.enums import OrderStatus, ShipmentStatus

CarrierName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
TrackingNumber = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


def _check_http_url(value: Optional[str]) -> Optional[str]:
    # The URL is rendered as a link on the storefront, so anything other than
    # http(s) (e.g. javascript:) must be rejected here.
    if value is None or value == "":
        return None
    value = value.strip()
    if len(value) > 500 or not value.lower().startswith(("http://", "https://")):
        raise ValueError("tracking_url must be an http(s) URL of at most 500 characters")
    return value


class ShipmentCreate(BaseModel):
    # MARU delivers its own parcels (Uzbekistan); other names are still allowed.
    carrier: CarrierName = "MARU"
    tracking_number: Optional[TrackingNumber] = None
    tracking_url: Optional[str] = None
    location: Optional[str] = None
    note: Optional[str] = None

    _url = field_validator("tracking_url")(_check_http_url)


class ShipmentUpdate(BaseModel):
    carrier: Optional[CarrierName] = None
    tracking_number: Optional[TrackingNumber] = None
    tracking_url: Optional[str] = None

    _url = field_validator("tracking_url")(_check_http_url)


class ShipmentEventCreate(BaseModel):
    status: ShipmentStatus
    location: Optional[str] = None
    note: Optional[str] = None
    occurred_at: Optional[datetime] = None


class ShipmentEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: ShipmentStatus
    location: Optional[str]
    note: Optional[str]
    occurred_at: datetime


class ShipmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    carrier: str
    tracking_number: Optional[str]
    tracking_url: Optional[str]
    status: ShipmentStatus
    shipped_at: Optional[datetime]
    delivered_at: Optional[datetime]
    events: list[ShipmentEventOut]


class TrackOrderRequest(BaseModel):
    order_number: str
    email: str


class TrackOrderOut(BaseModel):
    """Deliberately narrow: the lookup is authenticated only by order number +
    email, so it exposes progress, not addresses, prices or items."""

    model_config = ConfigDict(from_attributes=True)

    order_number: str
    status: OrderStatus
    created_at: datetime
    shipments: list[ShipmentOut]
