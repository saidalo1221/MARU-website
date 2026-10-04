import enum
import json

from sqlalchemy import BigInteger, Boolean, Column, DateTime, DECIMAL, Enum as SAEnum, ForeignKey, Integer, String, Text, func
from sqlalchemy.types import TypeDecorator

from app.database import Base


class PromoDiscountType(str, enum.Enum):
    PERCENT = "percent"
    FIXED = "fixed"


class IntList(TypeDecorator):
    """A list of ints kept as JSON text; None / empty means "no restriction"."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return json.dumps(sorted(set(int(v) for v in value))) if value else None

    def process_result_value(self, value, dialect):
        return json.loads(value) if value else None


class StrList(TypeDecorator):
    """A list of strings kept as JSON text; None / empty means "no restriction"."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return json.dumps(sorted({str(v).strip() for v in value if str(v).strip()}), ensure_ascii=False) if value else None

    def process_result_value(self, value, dialect):
        return json.loads(value) if value else None


class PromoCode(Base):
    """A code with a min order amount, expiry window and usage cap, optionally limited to certain
    products / categories, to delivery countries, to named customer accounts (PRD section 23) and to a
    number of uses per customer."""

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

    # Targeting: when either list is set the discount applies only to lines whose product is listed
    # or sits in a listed category (or one of its sub-categories).
    product_ids = Column(IntList, nullable=True)
    category_ids = Column(IntList, nullable=True)
    max_uses_per_customer = Column(Integer, nullable=True)
    # Who can use it: only these delivery countries (names, any case) and/or only these customer account ids.
    countries = Column(StrList, nullable=True)
    customer_ids = Column(IntList, nullable=True)

    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class PromoRedemption(Base):
    """One use of a promo code by an order; powers the per-customer limit. A customer is identified
    by account id when signed in, otherwise by checkout e-mail."""

    __tablename__ = "promo_redemptions"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    promo_code_id = Column(BigInteger, ForeignKey("promo_codes.id"), nullable=False, index=True)
    order_id = Column(BigInteger, ForeignKey("orders.id"), nullable=False)
    user_id = Column(BigInteger, nullable=True, index=True)
    email = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
