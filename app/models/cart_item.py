from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class CartItem(Base):
    """A line in a cart. Deliberately has no price column — cart prices are
    computed live from SKU/pricing rules; only OrderItem freezes a price (PRD section 53)."""

    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint("cart_id", "sku_id", name="uq_cart_items_cart_sku"),
        CheckConstraint("quantity > 0", name="ck_cart_items_quantity_positive"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    cart_id = Column(BigInteger, ForeignKey("carts.id"), nullable=False)
    sku_id = Column(BigInteger, ForeignKey("skus.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    cart = relationship("Cart", back_populates="items")
    sku = relationship("SKU")
