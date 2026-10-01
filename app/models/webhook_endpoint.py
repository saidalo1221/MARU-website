from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, String, Text, func

from app.database import Base

# Events a subscriber can ask for (PRD ТЗ№1 §37). "*" = all of them.
EVENTS = (
    "order.created",
    "order.paid",
    "order.cancelled",
    "order.shipped",
    "order.delivered",
    "payment.success",
    "payment.failed",
    "inventory.updated",
)


class WebhookEndpoint(Base):
    """A URL the platform calls when something happens (order created, paid, shipped...), signed with the
    endpoint's secret (see app/services/outbound_webhooks.py). Deliveries are background jobs, so they are
    retried and can be re-run from the admin jobs panel."""

    __tablename__ = "webhook_endpoints"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    url = Column(String(500), nullable=False)
    description = Column(String(200), nullable=True)
    secret = Column(String(64), nullable=False)
    events = Column(Text, nullable=False, default="*")  # "*" or comma-separated event names
    is_active = Column(Boolean, nullable=False, default=True)

    last_delivery_at = Column(DateTime, nullable=True)
    last_status_code = Column(Integer, nullable=True)
    last_error = Column(String(300), nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
