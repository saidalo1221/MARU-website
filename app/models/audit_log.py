from sqlalchemy import BigInteger, Column, DateTime, String, Text, func

from app.database import Base


class AuditLog(Base):
    """Append-only record of sensitive admin actions (PRD ТЗ№3 §81)."""

    __tablename__ = "audit_logs"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=True)
    action = Column(String(50), nullable=False)
    entity = Column(String(50), nullable=False)
    entity_id = Column(String(50), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
