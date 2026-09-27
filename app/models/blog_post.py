from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import relationship

from app.database import Base


class BlogPost(Base):
    """Blog article (PRD ТЗ№3 §40). Base fields hold the default-language
    (English) copy; app/models/blog_post_translation.py overrides
    title/excerpt/content per locale, same pattern as ProductTranslation."""

    __tablename__ = "blog_posts"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    category_id = Column(BigInteger, ForeignKey("blog_categories.id"), nullable=False)

    slug = Column(String(255), nullable=False, unique=True)
    title = Column(String(255), nullable=False)
    excerpt = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    cover_image_url = Column(String(500), nullable=True)
    author_name = Column(String(100), nullable=True)

    # A post is only ever returned by the public /blog/* endpoints once both
    # of these are set — is_published alone isn't enough (PRD gives no
    # "schedule a post" requirement, but published_at doubles as sort order
    # and this avoids a post going live from a stale/blank timestamp).
    is_published = Column(Boolean, nullable=False, default=False)
    published_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    category = relationship("BlogCategory", back_populates="posts")
