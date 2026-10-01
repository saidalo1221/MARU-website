"""Adapter interfaces for outside systems (PRD ТЗ№4 §1-5). The platform talks to ERP, marketplaces,
shipping and messaging only through these small interfaces; a connector for a concrete vendor
implements one and is registered with register_adapter(). Until a vendor is chosen every kind
resolves to a Null adapter that does nothing and says so in the log, so callers never need an
"is it configured?" check.

    from app.services.integrations.adapters import get_adapter
    get_adapter("erp").push_order(order)          # no-op today, real connector later
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.external_id import ExternalId

logger = logging.getLogger("maru.integrations")


class ERPAdapter(ABC):
    name = "erp"

    @abstractmethod
    def push_order(self, order) -> Optional[str]:
        """Sends a paid/confirmed order; returns the ERP's order id when it has one."""

    @abstractmethod
    def push_stock_levels(self, rows: list[dict]) -> None:
        """Optional outbound stock snapshot [{sku_code, stock}]."""


class MarketplaceAdapter(ABC):
    name = "marketplace"

    @abstractmethod
    def publish_listing(self, sku) -> Optional[str]: ...

    @abstractmethod
    def update_stock_and_price(self, sku, stock: int, price) -> None: ...


class ShippingAdapter(ABC):
    name = "shipping"

    @abstractmethod
    def create_shipment(self, order) -> Optional[str]:
        """Books a delivery with an outside carrier; returns its tracking number."""

    @abstractmethod
    def get_status(self, tracking_number: str) -> Optional[str]: ...


class MessagingAdapter(ABC):
    """SMS, WhatsApp and Telegram share one shape: a text to a recipient."""

    name = "messaging"

    @abstractmethod
    def send(self, recipient: str, text: str) -> bool: ...


def _skip(what: str):
    logger.info("%s skipped: no connector configured", what)
    return None


class NullERP(ERPAdapter):
    def push_order(self, order): return _skip("erp.push_order")
    def push_stock_levels(self, rows): return _skip("erp.push_stock_levels")


class NullMarketplace(MarketplaceAdapter):
    def publish_listing(self, sku): return _skip("marketplace.publish_listing")
    def update_stock_and_price(self, sku, stock, price): return _skip("marketplace.update_stock_and_price")


class NullShipping(ShippingAdapter):
    def create_shipment(self, order): return _skip("shipping.create_shipment")
    def get_status(self, tracking_number): return _skip("shipping.get_status")


class NullMessaging(MessagingAdapter):
    def send(self, recipient, text):
        _skip("messaging.send")
        return False


_NULLS = {"erp": NullERP(), "marketplace": NullMarketplace(), "shipping": NullShipping(),
          "sms": NullMessaging(), "whatsapp": NullMessaging(), "telegram": NullMessaging()}
_REGISTERED: dict[str, object] = {}


def register_adapter(kind: str, adapter) -> None:
    if kind not in _NULLS:
        raise ValueError(f"Unknown adapter kind {kind!r}; one of {sorted(_NULLS)}")
    _REGISTERED[kind] = adapter


def get_adapter(kind: str):
    return _REGISTERED.get(kind) or _NULLS[kind]


def is_configured(kind: str) -> bool:
    return kind in _REGISTERED


# --- external id mapping -------------------------------------------------------------------

def set_external_id(db: Session, system: str, entity: str, internal_id: int, external_id: str) -> ExternalId:
    """Records (or updates) the outside id of one of our records. Caller commits."""
    row = db.execute(
        select(ExternalId).where(
            ExternalId.system == system, ExternalId.entity == entity, ExternalId.internal_id == internal_id
        )
    ).scalar_one_or_none()
    if row is None:
        row = ExternalId(system=system, entity=entity, internal_id=internal_id, external_id=external_id)
        db.add(row)
    else:
        row.external_id = external_id
    db.flush()
    return row


def get_external_id(db: Session, system: str, entity: str, internal_id: int) -> Optional[str]:
    return db.execute(
        select(ExternalId.external_id).where(
            ExternalId.system == system, ExternalId.entity == entity, ExternalId.internal_id == internal_id
        )
    ).scalar_one_or_none()


def find_internal_id(db: Session, system: str, entity: str, external_id: str) -> Optional[int]:
    """Reverse lookup for inbound events: which of our records does this outside id belong to?"""
    return db.execute(
        select(ExternalId.internal_id).where(
            ExternalId.system == system, ExternalId.entity == entity, ExternalId.external_id == external_id
        )
    ).scalar_one_or_none()
