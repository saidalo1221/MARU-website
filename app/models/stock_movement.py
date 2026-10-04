from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, func

from app.database import Base


class StockMovement(Base):
    """One stock transfer between warehouses or a manual stock correction (PRD ТЗ№1 §33: warehouse movements).
    Sales and reservations are not listed here: they are in the order history. `quantity` is always positive
    for a transfer; for an adjustment it is the change (can be negative)."""

    __tablename__ = "stock_movements"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    movement_type = Column(String(20), nullable=False)  # "transfer" | "adjustment"
    sku_id = Column(BigInteger, ForeignKey("skus.id"), nullable=False, index=True)
    from_warehouse_id = Column(BigInteger, ForeignKey("warehouses.id"), nullable=True)
    to_warehouse_id = Column(BigInteger, ForeignKey("warehouses.id"), nullable=True)
    quantity = Column(Integer, nullable=False)
    note = Column(String(300), nullable=True)
    created_by_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
