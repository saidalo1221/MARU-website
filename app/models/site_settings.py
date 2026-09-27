from sqlalchemy import BigInteger, Column, DateTime, Float, String, Text, func

from app.database import Base


class SiteSettings(Base):
    """Singleton row (id=1) holding the storefront's contact/location/about
    content, editable from the admin panel instead of being hardcoded in the
    frontend. Base fields hold the default-language (English) copy;
    SiteSettingsTranslation overrides the translatable ones per locale, same
    pattern as ProductTranslation."""

    __tablename__ = "site_settings"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    phone = Column(String(30), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(String(500), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    about_title = Column(String(255), nullable=True)
    about_body = Column(Text, nullable=True)

    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
