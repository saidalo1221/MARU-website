from sqlalchemy import BigInteger, Column, Date, DateTime, DECIMAL, ForeignKey, String, func

from app.database import Base


class MarketingSpend(Base):
    """Advertising money spent in a month, entered by hand in the admin dashboard (PRD ТЗ№1 §60: CAC and
    ROAS need the cost side, which only the marketing team knows). Amounts are in USD."""

    __tablename__ = "marketing_spend"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    month = Column(Date, nullable=False, index=True)  # first day of the month
    channel = Column(String(60), nullable=False)  # e.g. "Google Ads", "Instagram"
    amount_usd = Column(DECIMAL(12, 2), nullable=False)
    created_by_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
