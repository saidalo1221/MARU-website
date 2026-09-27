from sqlalchemy import BigInteger, Column, DateTime, DECIMAL, String, func

from app.database import Base


class ExchangeRate(Base):
    """Fixed, admin-maintained FX rate against USD (PRD section 14). USD itself
    is the implicit base (1.0) and isn't stored here. A live/automatic rate
    feed can replace how these rows are populated later without changing how
    they're read (services/currency.py)."""

    __tablename__ = "exchange_rates"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    currency = Column(String(3), nullable=False, unique=True)
    units_per_usd = Column(DECIMAL(18, 6), nullable=False)

    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
