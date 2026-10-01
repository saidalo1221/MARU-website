from sqlalchemy import BigInteger, Column, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class SkuBundleItem(Base):
    """What is inside a set / pack SKU (PRD ТЗ№1 §7: "Pack 5" may hold different sizes and colours).
    The set is an ordinary SKU with its own code, price, tiers and stock (the pack is assembled and counted as
    its own item); this table only describes the contents so the product page can show them."""

    __tablename__ = "sku_bundle_items"
    __table_args__ = (
        UniqueConstraint("bundle_sku_id", "component_sku_id", name="uq_sku_bundle_items_pair"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    bundle_sku_id = Column(BigInteger, ForeignKey("skus.id", ondelete="CASCADE"), nullable=False, index=True)
    component_sku_id = Column(BigInteger, ForeignKey("skus.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)

    component = relationship("SKU", foreign_keys=[component_sku_id], lazy="joined")

    @property
    def sku_code(self) -> str:
        return self.component.sku_code

    @property
    def product_name(self) -> str:
        return self.component.variant.product.name

    @property
    def variant_name(self) -> str:
        return self.component.variant.name

    @property
    def color(self) -> str:
        return self.component.variant.color
