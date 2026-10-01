import enum
import json

from sqlalchemy import (
    BigInteger, Column, DateTime, Enum as SAEnum, ForeignKey, SmallInteger, Text, UniqueConstraint, func,
)

from sqlalchemy.types import TypeDecorator

from app.database import Base


class ReviewStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class UrlList(TypeDecorator):
    """A list of strings kept as JSON text; None / empty means "none"."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return json.dumps(list(value)) if value else None

    def process_result_value(self, value, dialect):
        return json.loads(value) if value else []


class Review(Base):
    """Verified-purchase review (PRD ТЗ№3 §36): only customers with a paid order
    containing the product may review it; reviews are moderated before display."""

    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_review_user_product"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    rating = Column(SmallInteger, nullable=False)
    content = Column(Text, nullable=True)
    # Photos the reviewer attached (PRD ТЗ№1 §32); files uploaded through POST /reviews/images.
    image_urls = Column(UrlList, nullable=True)
    status = Column(SAEnum(ReviewStatus, native_enum=False, length=20), nullable=False, default=ReviewStatus.PENDING)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
