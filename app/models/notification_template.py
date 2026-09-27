from sqlalchemy import BigInteger, Boolean, Column, DateTime, String, Text, UniqueConstraint, func

from app.database import Base


class NotificationTemplate(Base):
    """PRD ТЗ№4 §42: templates must not be hardcoded in the backend. Backs
    app/services/notifications/templates.py, which EmailNotifier consults
    before falling back to its built-in copy — so this table is additive,
    not a hard dependency; notifications keep working with zero rows here."""

    __tablename__ = "notification_templates"
    __table_args__ = (
        UniqueConstraint("event", "locale", "channel", name="uq_notification_template_event_locale_channel"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # e.g. "order_created", "order_status_changed", "password_reset", "email_verification".
    event = Column(String(50), nullable=False)
    locale = Column(String(5), nullable=False)  # ru | uz | en (app/services/i18n.py ALLOWED_LOCALES)
    channel = Column(String(20), nullable=False, default="email")  # email today; sms/whatsapp/telegram later
    subject = Column(String(255), nullable=True)  # unused for channels without a subject line
    body = Column(Text, nullable=False)  # Python str.format() placeholders, e.g. "{order_number}"
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
