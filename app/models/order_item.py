from sqlalchemy import BigInteger, Column, DateTime, DECIMAL, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.database import Base


class OrderItem(Base):
    """Snapshots price/name at time of purchase (PRD section 53) — never
    dereferences live Product/SKU data for display; sku_id is a safety-net
    FK only (ON DELETE SET NULL), not used to render the order."""

    __tablename__ = "order_items"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(BigInteger, ForeignKey("orders.id"), nullable=False)
    sku_id = Column(BigInteger, ForeignKey("skus.id", ondelete="SET NULL"), nullable=True)
    # Which warehouse this line's stock was reserved from (PRD ТЗ№3 §68) —
    # set by app/services/order_service.py::_reserve_stock(). Not a snapshot
    # like the *_snapshot fields: it's operational/fulfillment data, not
    # customer-facing pricing history, so it's fine for it to just point at
    # the live Warehouse row.
    warehouse_id = Column(BigInteger, ForeignKey("warehouses.id", ondelete="SET NULL"), nullable=True)

    sku_code_snapshot = Column(String(100), nullable=False)
    product_name_snapshot = Column(String(255), nullable=False)
    variant_name_snapshot = Column(String(255), nullable=True)

    unit_price = Column(DECIMAL(12, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    line_total = Column(DECIMAL(12, 2), nullable=False)
    # This line's share of the order discount and tax (they add up to the order totals).
    discount_amount = Column(DECIMAL(12, 2), nullable=False, default=0, server_default="0")
    tax_amount = Column(DECIMAL(12, 2), nullable=False, default=0, server_default="0")
    currency = Column(String(3), nullable=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    order = relationship("Order", back_populates="items")
