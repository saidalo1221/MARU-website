from sqlalchemy import BigInteger, Boolean, Column, DateTime, String, Text, UniqueConstraint, func

from app.database import Base


class ContentOverride(Base):
    """Admin-edited replacement for one piece of built-in storefront text (a translation key such as
    "home.title") in one language. No row = the text that ships with the site is used."""

    __tablename__ = "content_overrides"
    __table_args__ = (
        UniqueConstraint("text_key", "locale", name="uq_content_overrides_key_locale"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    text_key = Column(String(120), nullable=False)
    locale = Column(String(5), nullable=False)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class SeoMeta(Base):
    """Admin-set search/social tags for one page path in one language. Empty fields fall back to what
    the page itself sets."""

    __tablename__ = "seo_meta"
    __table_args__ = (
        UniqueConstraint("path", "locale", name="uq_seo_meta_path_locale"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    path = Column(String(255), nullable=False)
    locale = Column(String(5), nullable=False)
    title = Column(String(255), nullable=True)
    description = Column(String(500), nullable=True)
    image_url = Column(String(500), nullable=True)
    noindex = Column(Boolean, nullable=False, default=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
