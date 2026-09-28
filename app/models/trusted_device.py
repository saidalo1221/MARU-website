from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, UniqueConstraint, func

from app.database import Base


class TrustedDevice(Base):
    """A browser/device a customer has already completed the new-device
    email code for (app/routers/auth.py's login()). `device_id` is an
    opaque random token the frontend generates once and persists in
    localStorage — not tied to IP or user-agent, so it survives normal
    network changes without re-challenging."""

    __tablename__ = "trusted_devices"
    __table_args__ = (
        UniqueConstraint("user_id", "device_id", name="uq_trusted_devices_user_device"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    device_id = Column(String(64), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    last_used_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
