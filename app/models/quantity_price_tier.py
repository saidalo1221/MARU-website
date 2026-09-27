from sqlalchemy import BigInteger, Column, DECIMAL, ForeignKey, Integer, UniqueConstraint, func, DateTime

from app.database import Base


class QuantityPriceTier(Base):
    """Per-SKU quantity-break pricing (PRD section 22 example: 1-9/10-49/50-199/200+).
    If a SKU has no tiers, pricing falls back to the customer's tier column on SKU."""

    __tablename__ = "quantity_price_tiers"
    __table_args__ = (
        UniqueConstraint("sku_id", "min_quantity", name="uq_quantity_price_tiers_sku_min_qty"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    sku_id = Column(BigInteger, ForeignKey("skus.id"), nullable=False)
    min_quantity = Column(Integer, nullable=False)
    price = Column(DECIMAL(12, 2), nullable=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
