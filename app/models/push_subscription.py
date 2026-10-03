from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, func

from app.database import Base


class PushSubscription(Base):
    """One browser (or phone home-screen app) of a signed-in customer that agreed to web push notifications.
    `endpoint`, `p256dh` and `auth` come from the browser's PushSubscription and are all the push service needs."""

    __tablename__ = "push_subscriptions"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    endpoint = Column(String(500), nullable=False, unique=True)
    p256dh = Column(String(255), nullable=False)
    auth = Column(String(100), nullable=False)
    user_agent = Column(String(200), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
