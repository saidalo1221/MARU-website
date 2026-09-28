from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.database import Base


class AboutSection(Base):
    """One block of the About Us page (PRD 'About us' content), in the order
    they appear (sort_order). Free-form and admin-managed — unlike the fixed
    'History/Company/Production/...' sections that used to be hardcoded in
    frontend/src/i18n/translations.js, admins can add, remove, and reorder
    these. Base fields hold the default-language copy; AboutSectionTranslation
    overrides per locale, same pattern as ProductTranslation."""

    __tablename__ = "about_sections"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    translations = relationship("AboutSectionTranslation", cascade="all, delete-orphan")
