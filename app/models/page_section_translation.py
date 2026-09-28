from sqlalchemy import BigInteger, Column, ForeignKey, String, Text, UniqueConstraint

from app.database import Base


class PageSectionTranslation(Base):
    """Per-locale override of PageSection.title/body."""

    __tablename__ = "page_section_translations"
    __table_args__ = (
        UniqueConstraint("section_id", "locale", name="uq_page_section_translations_section_locale"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    section_id = Column(BigInteger, ForeignKey("page_sections.id", ondelete="CASCADE"), nullable=False)
    locale = Column(String(10), nullable=False)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
