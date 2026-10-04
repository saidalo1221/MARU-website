from sqlalchemy import BigInteger, Column, ForeignKey, String, Text, UniqueConstraint

from app.database import Base


class CategoryTranslation(Base):
    """Per-locale override of Category.name (PRD section 15). Locale is a plain
    string, not a DB enum, so adding a new language is just inserting rows —
    "перевод должен быть независимым от программного кода"."""

    __tablename__ = "category_translations"
    __table_args__ = (
        UniqueConstraint("category_id", "locale", name="uq_category_translations_category_locale"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    category_id = Column(BigInteger, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    locale = Column(String(10), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    seo_content = Column(Text, nullable=True)
