import enum

from sqlalchemy import BigInteger, Boolean, Column, DateTime, DECIMAL, Enum as SAEnum, Integer, String, func

from app.database import Base


class PromoDiscountType(str, enum.Enum):
    PERCENT = "percent"
    FIXED = "fixed"


class PromoCode(Base):
    """MVP scope only: a global code with a min order amount, expiry window,
    and usage cap. Per-product/per-country/per-customer targeting (PRD section 23)
    and per-customer usage caps are explicitly deferred."""

    __tablename__ = "promo_codes"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(50), nullable=False, unique=True)
    discount_type = Column(SAEnum(PromoDiscountType, native_enum=False, length=20), nullable=False)
    discount_value = Column(DECIMAL(12, 2), nullable=False)
    currency = Column(String(3), nullable=True)

    min_order_amount = Column(DECIMAL(12, 2), nullable=False, default=0)
    max_uses = Column(Integer, nullable=True)
    used_count = Column(Integer, nullable=False, default=0)

    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
