from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.enums import OrderStatus


class OrderStatusHistory(Base):
    """Append-only audit trail (PRD sections 12, 44) — rows are never
    mutated or deleted, only inserted by set_order_status()."""

    __tablename__ = "order_status_history"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(BigInteger, ForeignKey("orders.id"), nullable=False)

    from_status = Column(SAEnum(OrderStatus, native_enum=False, length=20), nullable=True)
    to_status = Column(SAEnum(OrderStatus, native_enum=False, length=20), nullable=False)
    changed_by_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    note = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    order = relationship("Order", back_populates="status_history")
