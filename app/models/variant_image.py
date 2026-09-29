from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.database import Base


class VariantImage(Base):
    """One photo in a product variant's gallery (PRD section 6 extension:
    admin can add multiple images per color, shown as a big image + scrollable
    thumbnails on the product page). `ProductVariant.photo_url` stays as the
    single legacy cover photo; this table is the additional gallery."""

    __tablename__ = "variant_images"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    variant_id = Column(BigInteger, ForeignKey("product_variants.id"), nullable=False)

    image_url = Column(String(500), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    variant = relationship("ProductVariant", back_populates="images")
