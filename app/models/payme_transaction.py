from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, func

from app.database import Base


class PaymeTransaction(Base):
    """Payme's own transaction record (PRD section 13, Uzbekistan local
    payment). Payme's protocol is inverted from Stripe/PayPal: Payme's
    server calls OUR merchant webhook (CheckPerformTransaction/
    CreateTransaction/PerformTransaction/CancelTransaction/CheckTransaction),
    so this table tracks transaction state exactly as their spec requires,
    kept separate from Order.status. state: 1=created, 2=performed,
    -1=cancelled (before perform), -2=cancelled (after perform)."""

    __tablename__ = "payme_transactions"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    payme_id = Column(String(50), nullable=False, unique=True)
    order_id = Column(BigInteger, ForeignKey("orders.id"), nullable=False)

    amount_tiyin = Column(BigInteger, nullable=False)
    # The timestamp sent by Payme in CreateTransaction.  GetStatement must
    # filter on this provider-side creation time, not on our local insert time.
    payme_time_ms = Column(BigInteger, nullable=False)
    state = Column(Integer, nullable=False, default=1)
    reason = Column(Integer, nullable=True)

    create_time_ms = Column(BigInteger, nullable=False)
    perform_time_ms = Column(BigInteger, nullable=False, default=0)
    cancel_time_ms = Column(BigInteger, nullable=False, default=0)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
