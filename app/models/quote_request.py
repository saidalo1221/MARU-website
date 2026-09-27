import enum

from sqlalchemy import BigInteger, Column, DateTime, DECIMAL, Enum as SAEnum, ForeignKey, String, Text, func

from app.database import Base


class QuoteStatus(str, enum.Enum):
    NEW = "new"
    IN_REVIEW = "in_review"
    OFFERED = "offered"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class QuoteRequest(Base):
    """B2B Request a Quote / distributor application (PRD ТЗ№2 §32-33, ТЗ№4 §16)."""

    __tablename__ = "quote_requests"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    rfq_number = Column(String(30), nullable=True, unique=True)
    request_type = Column(String(20), nullable=False, default="quote")  # quote | wholesale | distributor
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    # Set once by app/services/quote_service.py:convert_quote_to_order() —
    # also prevents converting the same accepted quote into a second order.
    order_id = Column(BigInteger, ForeignKey("orders.id"), nullable=True)

    name = Column(String(200), nullable=False)
    company = Column(String(255), nullable=True)
    country = Column(String(100), nullable=False)
    city = Column(String(100), nullable=True)
    email = Column(String(255), nullable=False)
    phone = Column(String(30), nullable=True)
    products = Column(Text, nullable=True)
    quantity = Column(String(100), nullable=True)
    comment = Column(Text, nullable=True)
    source = Column(String(20), nullable=False, default="website")

    status = Column(SAEnum(QuoteStatus, native_enum=False, length=20), nullable=False, default=QuoteStatus.NEW)
    proposed_price = Column(DECIMAL(12, 2), nullable=True)
    currency = Column(String(3), nullable=True)
    valid_until = Column(DateTime, nullable=True)
    manager_notes = Column(Text, nullable=True)
    crm_lead_id = Column(String(50), nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
