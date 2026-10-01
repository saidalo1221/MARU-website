from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base

# PRD section 4: first-stage assortment is limited to these container sizes (ml).
ALLOWED_VOLUMES_ML = (350, 470, 800, 1000, 1900)


class Product(Base):
    """A sellable product, e.g. "MARU Food Container 1000 ml".
    Fields follow PRD section 4 (assortment / stored attributes)."""

    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint(
            f"volume_ml IN {ALLOWED_VOLUMES_ML}",
            name="ck_products_volume_ml",
        ),
        CheckConstraint("material = 'polypropylene'", name="ck_products_material"),
        CheckConstraint("badge_mode IN ('auto', 'manual')", name="ck_products_badge_mode"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    category_id = Column(BigInteger, ForeignKey("categories.id"), nullable=False)

    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True)

    # Container specification (PRD section 4).
    volume_ml = Column(Integer, nullable=False)
    material = Column(String(50), nullable=False, default="polypropylene")
    shape = Column(String(100), nullable=True)
    purpose = Column(String(255), nullable=True)

    # Physical dimensions of the container itself.
    length_mm = Column(Integer, nullable=True)
    width_mm = Column(Integer, nullable=True)
    height_mm = Column(Integer, nullable=True)
    weight_g = Column(Integer, nullable=True)

    description = Column(Text, nullable=True)
    country_of_origin = Column(String(100), nullable=True)
    min_order_quantity = Column(Integer, nullable=False, default=1)
    # Which tax treatment the product gets (PRD ТЗ№3 §74): standard | reduced | zero | exempt.
    # app/services/tax.py: zero and exempt are never taxed; reduced looks for a 'reduced' tax rule
    # and falls back to the general one; standard uses the general rule.
    tax_class = Column(String(20), nullable=False, default="standard", server_default="standard")

    # Product badges (New / Sale / Best Seller — see app/services/badges.py).
    # "auto" computes them from created_at/SKU special_price/sales volume;
    # "manual" uses the three override flags below instead. Out-of-stock is
    # always computed live — it's a factual availability state, not marketing.
    badge_mode = Column(String(10), nullable=False, default="auto", server_default="auto")
    badge_new = Column(Boolean, nullable=True)
    badge_sale = Column(Boolean, nullable=True)
    badge_bestseller = Column(Boolean, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    category = relationship("Category", back_populates="products")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
