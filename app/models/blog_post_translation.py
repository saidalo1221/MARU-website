from sqlalchemy import BigInteger, Column, ForeignKey, String, Text, UniqueConstraint

from app.database import Base


class BlogPostTranslation(Base):
    """Per-locale override of BlogPost.title/excerpt/content (PRD section 15)."""

    __tablename__ = "blog_post_translations"
    __table_args__ = (
        UniqueConstraint("post_id", "locale", name="uq_blog_post_translations_post_locale"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    post_id = Column(BigInteger, ForeignKey("blog_posts.id", ondelete="CASCADE"), nullable=False)
    locale = Column(String(10), nullable=False)
    # Optional per-locale slug (falls back to BlogPost.slug when unset) so an
    # admin can give a post a native-language URL per translation.
    slug = Column(String(255), nullable=True)
    title = Column(String(255), nullable=False)
    excerpt = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
