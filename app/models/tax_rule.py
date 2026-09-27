from sqlalchemy import BigInteger, Boolean, Column, DateTime, DECIMAL, String, UniqueConstraint, func

from app.database import Base

# Same wildcard convention as ShippingRate (app/models/shipping_rate.py):
# "*" matches any country / any customer type, used as a fallback tier.
ANY = "*"


class TaxRule(Base):
    """PRD ТЗ№3 §41: tax is looked up by (country, customer_type, tax_type)
    with "*" fallbacks, same shape as ShippingRate. rate is a percentage
    (12.50 means 12.5%), applied to the post-discount, pre-shipping subtotal
    (PRD §69's pricing pipeline: ... Discount -> Tax -> Shipping -> Total)."""

    __tablename__ = "tax_rules"
    __table_args__ = (
        UniqueConstraint("country", "customer_type", "tax_type", name="uq_tax_rules_country_customer_type_tax_type"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    country = Column(String(100), nullable=False)
    customer_type = Column(String(20), nullable=False)  # a CustomerType value, or "*"
    tax_type = Column(String(30), nullable=False, default="vat")

    rate = Column(DECIMAL(5, 2), nullable=False, default=0)  # percentage, e.g. 12.00

    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
