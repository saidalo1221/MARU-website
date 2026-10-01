from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    DECIMAL,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class SKU(Base):
    """Sellable unit tied to a single product variant (PRD sections 4, 6, 18).
    Carries its own barcode, pricing tiers and box/packaging specification."""

    __tablename__ = "skus"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    variant_id = Column(BigInteger, ForeignKey("product_variants.id"), nullable=False)

    sku_code = Column(String(100), nullable=False, unique=True)
    barcode = Column(String(50), nullable=True, unique=True)

    # Pricing tiers (PRD section 21).
    retail_price = Column(DECIMAL(12, 2), nullable=False)
    wholesale_price = Column(DECIMAL(12, 2), nullable=True)
    distributor_price = Column(DECIMAL(12, 2), nullable=True)
    export_price = Column(DECIMAL(12, 2), nullable=True)
    special_price = Column(DECIMAL(12, 2), nullable=True)
    # What one unit costs us, in `currency` (PRD ТЗ№1 §60 gross margin). Internal: never in a public schema.
    cost_price = Column(DECIMAL(12, 2), nullable=True)
    currency = Column(String(3), nullable=False, default="USD")

    # Unit packaging specification (PRD section 18).
    unit_weight_g = Column(Integer, nullable=True)
    box_quantity = Column(Integer, nullable=True)
    box_weight_g = Column(Integer, nullable=True)
    box_length_mm = Column(Integer, nullable=True)
    box_width_mm = Column(Integer, nullable=True)
    box_height_mm = Column(Integer, nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    variant = relationship("ProductVariant", back_populates="skus")
    inventories = relationship("Inventory", back_populates="sku", cascade="all, delete-orphan")
    # Quantity-break prices (PRD ТЗ№2 §15); app/services/pricing.py applies them.
    quantity_tiers = relationship(
        "QuantityPriceTier",
        order_by="QuantityPriceTier.min_quantity",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def available_quantity(self) -> int:
        """Aggregate across every active warehouse (PRD ТЗ№3 §68) — this
        does not say which warehouse would actually fulfill an order; see
        app/services/order_service.py for that (single-warehouse-per-line
        selection, not split fulfillment)."""
        return sum(inv.available for inv in self.inventories if inv.warehouse is None or inv.warehouse.is_active)
