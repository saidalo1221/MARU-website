from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, String, func
from sqlalchemy.orm import relationship

from app.database import Base


class ProductVariant(Base):
    """A color variant of a product (PRD section 6), e.g. "Прозрачный" / "Белый".
    Each variant owns its own SKU(s), stock, price and photo."""

    __tablename__ = "product_variants"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_id = Column(BigInteger, ForeignKey("products.id"), nullable=False)

    name = Column(String(255), nullable=False)
    color = Column(String(100), nullable=False)
    color_hex = Column(String(7), nullable=True)
    photo_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    product = relationship("Product", back_populates="variants")
    skus = relationship("SKU", back_populates="variant", cascade="all, delete-orphan")
