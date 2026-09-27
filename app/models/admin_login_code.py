from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, func

from app.database import Base


class AdminLoginCode(Base):
    """One-time email code for the /admin 2-step login (separate from the
    opt-in TOTP MFA on User.mfa_secret) — see app/routers/auth.py's
    admin_login_request/admin_login_verify."""

    __tablename__ = "admin_login_codes"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    code_hash = Column(String(64), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
