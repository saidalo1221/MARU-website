from sqlalchemy import BigInteger, Column, DateTime, String, func
from sqlalchemy.orm import relationship

from app.database import Base


class BlogCategory(Base):
    """Blog category (PRD ТЗ№3 §40: Blog Home / Categories / Article / Related
    Articles). Flat, unlike the product Category tree — PRD gives blog
    categories no hierarchy requirement."""

    __tablename__ = "blog_categories"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    posts = relationship("BlogPost", back_populates="category")
