from sqlalchemy import BigInteger, Column, DateTime, DECIMAL, Enum as SAEnum, ForeignKey, String, func

from app.database import Base
from app.models.enums import PaymentStatus


class Payment(Base):
    """One payment attempt for an order (PRD ТЗ№3 §31, ТЗ№4 §23). A retry after a failed attempt is a
    new row, so the history of attempts stays. Rows are written only by app/services/payment_ledger.py,
    driven by the order status changes; Payme/Click keep their protocol tables, refunds stay in `refunds`."""

    __tablename__ = "payments"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(BigInteger, ForeignKey("orders.id"), nullable=False, index=True)
    provider = Column(String(50), nullable=False)
    provider_transaction_id = Column(String(255), nullable=True)
    amount = Column(DECIMAL(12, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(SAEnum(PaymentStatus, native_enum=False, length=24), nullable=False, default=PaymentStatus.CREATED)
    idempotency_key = Column(String(80), nullable=False, unique=True)  # "order-<id>-<attempt>"
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
