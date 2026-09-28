from sqlalchemy import BigInteger, Column, ForeignKey, String, Text, UniqueConstraint

from app.database import Base


class ProductTranslation(Base):
    """Per-locale override of Product.name/description (PRD section 15)."""

    __tablename__ = "product_translations"
    __table_args__ = (
        UniqueConstraint("product_id", "locale", name="uq_product_translations_product_locale"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    locale = Column(String(10), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    shape = Column(String(100), nullable=True)
    purpose = Column(String(255), nullable=True)
    country_of_origin = Column(String(100), nullable=True)
