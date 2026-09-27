from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, Text, func

from app.database import Base


class AnalyticsEvent(Base):
    """Server-side capture of PRD ТЗ№4 §46/§49's GA4-shaped events
    (sign_up, login, add_to_cart, begin_checkout, purchase, generate_lead,
    add_to_wishlist, ...). This is the capture point only — it does NOT push
    to GA4/Meta/GTM: those need the vendor's Measurement Protocol API secret
    / access token, which hasn't been chosen (see TODO.md). `properties` is
    a JSON string (event-specific fields), same pattern as AuditLog's
    old_value/new_value — kept schemaless since PRD's event list keeps
    growing and each event's payload shape differs."""

    __tablename__ = "analytics_events"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    event_name = Column(String(50), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    # Cart token / order guest token / anything identifying an anonymous
    # visitor across events, when there's no user_id yet.
    session_id = Column(String(64), nullable=True)
    properties = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
