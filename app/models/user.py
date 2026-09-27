from sqlalchemy import BigInteger, Boolean, Column, DateTime, String, func
from sqlalchemy import Enum as SAEnum

from app.database import Base
from app.models.enums import CustomerType, UserRole


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)

    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(30), nullable=True)

    role = Column(SAEnum(UserRole, native_enum=False, length=30), nullable=False, default=UserRole.CUSTOMER)
    customer_type = Column(
        SAEnum(CustomerType, native_enum=False, length=20), nullable=False, default=CustomerType.RETAIL
    )
    is_active = Column(Boolean, nullable=False, default=True)
    # PRD ТЗ№3 §19 (Users table). Registration issues a verification email
    # (app/routers/auth.py); nothing currently gates on this being True — no
    # PRD acceptance criterion requires blocking checkout/login on it.
    email_verified = Column(Boolean, nullable=False, default=False)

    # Admin MFA (PRD ТЗ№3 §58). mfa_secret is set by /auth/mfa/setup and only
    # takes effect once confirmed via /auth/mfa/enable (mfa_enabled=True) — see
    # that router's module docstring for why this isn't force-enabled for
    # every admin role yet.
    mfa_secret = Column(String(32), nullable=True)
    mfa_enabled = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
