from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, String, func
from sqlalchemy.orm import relationship

from app.database import Base


class Cart(Base):
    __tablename__ = "carts"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    token = Column(String(64), nullable=True, unique=True)
    currency = Column(String(3), nullable=False, default="USD")
    is_active = Column(Boolean, nullable=False, default=True)
    converted_at = Column(DateTime, nullable=True)
    # Set when the "you left something in your cart" e-mail went out (one per cart; app/tasks/abandoned_carts.py).
    abandoned_email_sent_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Active lines only: every pricing/shipping/checkout consumer reads this, so
    # saved-for-later lines are excluded from them automatically.
    items = relationship(
        "CartItem",
        primaryjoin="and_(Cart.id == CartItem.cart_id, CartItem.saved_for_later.is_(False))",
        back_populates="cart",
        cascade="all, delete-orphan",
        overlaps="saved_items",
    )
    saved_items = relationship(
        "CartItem",
        primaryjoin="and_(Cart.id == CartItem.cart_id, CartItem.saved_for_later.is_(True))",
        viewonly=True,
        overlaps="items,cart",
    )
