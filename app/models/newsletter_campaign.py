from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, Text, func

from app.database import Base


class NewsletterCampaign(Base):
    """One e-mail an admin sent to the confirmed newsletter subscribers (PRD ТЗ№1 §33 marketing). Each recipient is a
    background job, so a long list never blocks the admin page and failures are retried; the counters show progress."""

    __tablename__ = "newsletter_campaigns"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    subject = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    locale = Column(String(5), nullable=True)  # only subscribers who signed up in this language; NULL = everyone
    recipients_total = Column(Integer, nullable=False, default=0)
    sent_count = Column(Integer, nullable=False, default=0)
    created_by_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
