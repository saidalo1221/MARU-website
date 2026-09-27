from sqlalchemy import BigInteger, Column, DateTime, DECIMAL, Enum as SAEnum, ForeignKey, String, Text, func
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.enums import RefundStatus


class Refund(Base):
    """One row per refund attempt against an order (PRD ТЗ№3 §31/§67,
    ТЗ№4 §28). An order can have several COMPLETED refunds (partial refunds)
    as long as their sum never exceeds the order total; see
    app/services/refund_service.py for that invariant."""

    __tablename__ = "refunds"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(BigInteger, ForeignKey("orders.id"), nullable=False)

    amount = Column(DECIMAL(12, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    reason = Column(Text, nullable=True)

    status = Column(SAEnum(RefundStatus, native_enum=False, length=20), nullable=False, default=RefundStatus.PENDING)
    # Snapshot of order.payment_method at refund time — the provider actually
    # asked to move the money, not necessarily today's gateway configuration.
    provider = Column(String(20), nullable=False)
    provider_refund_id = Column(String(255), nullable=True)
    failure_reason = Column(Text, nullable=True)

    created_by_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    order = relationship("Order")
