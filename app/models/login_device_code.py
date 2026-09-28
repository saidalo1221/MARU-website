from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, func

from app.database import Base


class LoginDeviceCode(Base):
    """One-time email code required to log in from a device not yet in
    TrustedDevice — the customer-facing equivalent of AdminLoginCode. See
    app/routers/auth.py's login()/verify_login_device()."""

    __tablename__ = "login_device_codes"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    device_id = Column(String(64), nullable=False)
    code_hash = Column(String(64), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
