from sqlalchemy import BigInteger, Column, ForeignKey, String, Text, UniqueConstraint

from app.database import Base


class AboutSectionTranslation(Base):
    """Per-locale override of AboutSection.title/body."""

    __tablename__ = "about_section_translations"
    __table_args__ = (
        UniqueConstraint("section_id", "locale", name="uq_about_section_translations_section_locale"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    section_id = Column(BigInteger, ForeignKey("about_sections.id", ondelete="CASCADE"), nullable=False)
    locale = Column(String(10), nullable=False)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
