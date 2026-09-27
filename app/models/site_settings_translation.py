from sqlalchemy import BigInteger, Column, ForeignKey, String, Text, UniqueConstraint

from app.database import Base


class SiteSettingsTranslation(Base):
    """Per-locale override of SiteSettings.address/about_title/about_body.
    phone/email/latitude/longitude aren't translatable, so they stay on the
    base row only."""

    __tablename__ = "site_settings_translations"
    __table_args__ = (
        UniqueConstraint("site_settings_id", "locale", name="uq_site_settings_translations_settings_locale"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    site_settings_id = Column(BigInteger, ForeignKey("site_settings.id", ondelete="CASCADE"), nullable=False)
    locale = Column(String(10), nullable=False)
    address = Column(String(500), nullable=True)
    about_title = Column(String(255), nullable=True)
    about_body = Column(Text, nullable=True)
