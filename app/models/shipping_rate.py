from sqlalchemy import Boolean, Column, DateTime, DECIMAL, BigInteger, String, UniqueConstraint, func

from app.database import Base

# "*" is a wildcard sentinel matching any country / any delivery method, used as
# a fallback tier so admins can configure one default rate instead of every
# country x method combination up front (PRD section 17).
ANY = "*"


class ShippingRate(Base):
    """Delivery cost rate table (PRD sections 17-18): flat base fee plus a
    per-kg fee, looked up by (country, delivery_method) with "*" fallbacks."""

    __tablename__ = "shipping_rates"
    __table_args__ = (
        UniqueConstraint("country", "delivery_method", name="uq_shipping_rates_country_method"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    country = Column(String(100), nullable=False)
    delivery_method = Column(String(50), nullable=False)

    currency = Column(String(3), nullable=False, default="USD")
    base_fee = Column(DECIMAL(12, 2), nullable=False, default=0)
    per_kg_fee = Column(DECIMAL(12, 2), nullable=False, default=0)

    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
