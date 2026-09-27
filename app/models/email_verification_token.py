from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, func

from app.database import Base


class EmailVerificationToken(Base):
    """Same shape as PasswordResetToken — one-time, hashed, expiring."""

    __tablename__ = "email_verification_tokens"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(64), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
