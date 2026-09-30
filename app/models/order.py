import enum

from sqlalchemy import BigInteger, Column, DateTime, DECIMAL, ForeignKey, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.enums import OrderStatus


class OrderType(str, enum.Enum):
    INDIVIDUAL = "individual"
    COMPANY = "company"


class Order(Base):
    """Snapshots pricing and checkout details directly (PRD section 53: changing
    current prices must not rewrite historical orders); no live FK to Address/Company."""

    __tablename__ = "orders"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_number = Column(String(50), nullable=False, unique=True)

    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    # Sent only in the checkout response for guest orders.  It is required to
    # read, cancel, or poll a guest order without exposing it by sequential ID.
    guest_order_token = Column(String(64), nullable=True, unique=True)
    # Client-chosen `Idempotency-Key` from checkout: a retried request with the
    # same key returns this order instead of failing on the already-used cart.
    idempotency_key = Column(String(64), nullable=True, unique=True)
    cart_id = Column(BigInteger, ForeignKey("carts.id"), nullable=True)
    promo_code_id = Column(BigInteger, ForeignKey("promo_codes.id"), nullable=True)
    promo_code_snapshot = Column(String(50), nullable=True)

    status = Column(SAEnum(OrderStatus, native_enum=False, length=20), nullable=False, default=OrderStatus.NEW)
    # Stock is reserved as soon as the order is created (not only at payment,
    # PRD ТЗ№3 §19/§63); this is when that reservation lapses if nobody pays.
    # NULL once the order leaves a reserving status (paid-and-beyond, or a
    # terminal status that already released the stock).
    reservation_expires_at = Column(DateTime, nullable=True)

    customer_type_snapshot = Column(String(20), nullable=False)
    currency = Column(String(3), nullable=False)
    subtotal_amount = Column(DECIMAL(12, 2), nullable=False)
    discount_amount = Column(DECIMAL(12, 2), nullable=False, default=0)
    tax_amount = Column(DECIMAL(12, 2), nullable=False, default=0)
    delivery_amount = Column(DECIMAL(12, 2), nullable=False, default=0)
    total_amount = Column(DECIMAL(12, 2), nullable=False)

    order_type = Column(SAEnum(OrderType, native_enum=False, length=20), nullable=False, default=OrderType.INDIVIDUAL)

    # Checkout snapshot (PRD section 9).
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(30), nullable=False)
    email = Column(String(255), nullable=False)
    country = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)
    address_line = Column(String(255), nullable=False)
    postal_code = Column(String(20), nullable=False)
    delivery_method = Column(String(50), nullable=False)
    payment_method = Column(String(50), nullable=False)

    # Acquisition channel for CRM push (PRD section 26).
    source = Column(String(20), nullable=False, default="website")

    # Company snapshot, populated only when order_type == COMPANY.
    company_name = Column(String(255), nullable=True)
    company_reg_number = Column(String(100), nullable=True)
    company_tax_number = Column(String(100), nullable=True)
    company_address = Column(String(255), nullable=True)
    contact_person = Column(String(255), nullable=True)

    # Wide enough for Stripe client_secrets / Payme's base64 checkout URLs.
    payment_reference = Column(String(255), nullable=True)
    # Bitrix24 deal id, set after the first successful CRM push so later
    # pushes (status changes) update the same deal instead of duplicating it.
    crm_deal_id = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    # JSON of first/last-touch marketing attribution captured by the storefront
    # (utm_*, referrer, landing_page; PRD ТЗ№4 §18). See order_service.clean_attribution.
    attribution = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    status_history = relationship(
        "OrderStatusHistory",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderStatusHistory.created_at",
    )
    shipments = relationship(
        "Shipment",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="Shipment.id",
    )
    user = relationship("User")
    promo_code = relationship("PromoCode")
