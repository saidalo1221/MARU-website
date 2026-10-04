import enum

from sqlalchemy import BigInteger, Column, DateTime, Enum as SAEnum, String, func

from app.database import Base


class NewsletterStatus(str, enum.Enum):
    PENDING = "pending"  # signed up, has not clicked the confirmation link yet
    CONFIRMED = "confirmed"
    UNSUBSCRIBED = "unsubscribed"


class NewsletterSubscriber(Base):
    """Double opt-in newsletter list (PRD ТЗ№2 §43). Only CONFIRMED rows may be
    mailed. `token` is the secret in both the confirm and unsubscribe links."""

    __tablename__ = "newsletter_subscribers"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True)
    locale = Column(String(5), nullable=False, default="en")
    status = Column(SAEnum(NewsletterStatus, native_enum=False, length=20), nullable=False, default=NewsletterStatus.PENDING)
    token = Column(String(64), nullable=False, unique=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    confirmed_at = Column(DateTime, nullable=True)
    unsubscribed_at = Column(DateTime, nullable=True)
