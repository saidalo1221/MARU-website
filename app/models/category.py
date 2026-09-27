from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, func
from sqlalchemy.orm import relationship

from app.database import Base


class Category(Base):
    """Catalog category. Supports the hierarchy from PRD section 5:
    Category -> Series -> Product -> Variant -> SKU, via self-referencing parent_id."""

    __tablename__ = "categories"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    parent_id = Column(BigInteger, ForeignKey("categories.id"), nullable=True)

    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    parent = relationship("Category", remote_side=[id], backref="children")
    products = relationship("Product", back_populates="category")
