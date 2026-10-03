from sqlalchemy import BigInteger, Column, DateTime, String, UniqueConstraint, func

from app.database import Base


class WebhookEvent(Base):
    """One accepted inbound webhook (PRD ТЗ№04 §50). The unique (provider, event_id) pair is the
    idempotency guard: a provider that redelivers the same event does not enqueue it twice."""

    __tablename__ = "webhook_events"
    __table_args__ = (
        UniqueConstraint("provider", "event_id", name="uq_webhook_events_provider_event"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    provider = Column(String(50), nullable=False)
    event_id = Column(String(120), nullable=False)
    job_id = Column(BigInteger, nullable=True)
    received_at = Column(DateTime, server_default=func.now(), nullable=False)
