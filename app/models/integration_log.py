import enum

from sqlalchemy import BigInteger, Column, DateTime, Enum as SAEnum, Integer, String, Text, func

from app.database import Base


class IntegrationLogStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


class IntegrationLog(Base):
    """PRD ТЗ№4 §57: one row per attempt (append-only, like OrderStatusHistory/
    AuditLog — never mutated), so `attempt` history is just "rows for this
    (integration, operation, internal_entity, internal_id) ordered by
    created_at". app/services/integrations/log.py writes these;
    app/tasks/retry_integrations.py and POST /admin/integration-logs/{id}/retry
    read them to decide what to retry."""

    __tablename__ = "integration_logs"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    integration = Column(String(50), nullable=False)  # e.g. "crm_bitrix24"
    operation = Column(String(50), nullable=False)  # e.g. "push_order"
    direction = Column(String(10), nullable=False, default="outbound")
    internal_entity = Column(String(50), nullable=False)  # e.g. "order", "quote"
    internal_id = Column(BigInteger, nullable=False)
    external_id = Column(String(255), nullable=True)
    request_id = Column(String(64), nullable=True)

    status = Column(SAEnum(IntegrationLogStatus, native_enum=False, length=20), nullable=False)
    error_code = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    attempt = Column(Integer, nullable=False, default=1)
    duration_ms = Column(Integer, nullable=True)  # wall time of the call itself

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)
