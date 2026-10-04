from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, UniqueConstraint, func

from app.database import Base


class StockAlert(Base):
    """"Email me when this SKU is back in stock" (PRD ТЗ№2 §20). One row per
    (sku, email); `notified_at` is set by app/tasks/notify_back_in_stock.py and
    cleared again if the same address asks for the same SKU later."""

    __tablename__ = "stock_alerts"
    __table_args__ = (
        UniqueConstraint("sku_id", "email", name="uq_stock_alerts_sku_email"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    sku_id = Column(BigInteger, ForeignKey("skus.id"), nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    email = Column(String(255), nullable=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    notified_at = Column(DateTime, nullable=True)
