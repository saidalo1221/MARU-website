from sqlalchemy import BigInteger, Column, DateTime, DECIMAL, ForeignKey, Integer, String, func

from app.database import Base


class ClickTransaction(Base):
    """Click's own transaction record (PRD section 13, Uzbekistan local
    payment). Like Payme, Click's server calls OUR merchant webhook (Prepare
    then Complete actions) rather than us polling them.
    action: 0=prepared, 1=completed, -1=cancelled."""

    __tablename__ = "click_transactions"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    click_trans_id = Column(String(50), nullable=False, unique=True)
    order_id = Column(BigInteger, ForeignKey("orders.id"), nullable=False)

    amount = Column(DECIMAL(12, 2), nullable=False)
    action = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
