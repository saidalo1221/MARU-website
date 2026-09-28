from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.database import Base

# Static "support" pages an admin can attach free-form content sections to —
# same shape/pattern as AboutSection, just scoped by `page` instead of being
# its own dedicated table per page.
PAGE_KEYS = ("delivery", "payment", "returns", "faq", "contact")


class PageSection(Base):
    """One free-form content block on a support page (Delivery/Payment/
    Returns/FAQ/Contact), ordered within that page by sort_order. Base
    fields hold the default-language copy; PageSectionTranslation overrides
    per locale — same pattern as AboutSection/AboutSectionTranslation."""

    __tablename__ = "page_sections"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    page = Column(String(30), nullable=False)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    translations = relationship("PageSectionTranslation", cascade="all, delete-orphan")
