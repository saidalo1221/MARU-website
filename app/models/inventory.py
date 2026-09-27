from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from app.database import Base


class Inventory(Base):
    """Stock ledger for a SKU at one warehouse (PRD ТЗ№3 §19/§28: unique
    index is SKU + Warehouse, not SKU alone, once multiple warehouses exist).
    Formula: Available = Stock - Reserved."""

    __tablename__ = "inventory"
    __table_args__ = (
        UniqueConstraint("sku_id", "warehouse_id", name="uq_inventory_sku_warehouse"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    sku_id = Column(BigInteger, ForeignKey("skus.id"), nullable=False)
    warehouse_id = Column(BigInteger, ForeignKey("warehouses.id"), nullable=False)

    stock = Column(Integer, nullable=False, default=0)
    reserved = Column(Integer, nullable=False, default=0)
    incoming = Column(Integer, nullable=False, default=0)
    min_stock = Column(Integer, nullable=False, default=0)

    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    sku = relationship("SKU", back_populates="inventories")
    warehouse = relationship("Warehouse")

    @hybrid_property
    def available(self):
        return self.stock - self.reserved
