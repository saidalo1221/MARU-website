from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Text, func

from app.database import Base

# pending -> running -> done | pending again (retry with backoff) | dead (retries used up
# or a permanent error: the dead-letter queue, PRD ТЗ№4 §54).
JOB_PENDING = "pending"
JOB_RUNNING = "running"
JOB_DONE = "done"
JOB_DEAD = "dead"


class Job(Base):
    """One unit of background work (PRD ТЗ№3 §88-89, ТЗ№4 §50-54). The database is the
    queue, so a job survives a restart and can be inspected and retried by an admin;
    app/tasks/worker.py runs them. `dedupe_key` makes enqueuing idempotent."""

    __tablename__ = "jobs"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    queue = Column(String(30), nullable=False, default="default")
    job_type = Column(String(60), nullable=False)
    payload = Column(Text, nullable=False, default="{}")  # JSON

    status = Column(String(12), nullable=False, default=JOB_PENDING, index=True)
    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=5)
    run_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)

    locked_by = Column(String(64), nullable=True)
    locked_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    dedupe_key = Column(String(120), nullable=True, unique=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    finished_at = Column(DateTime, nullable=True)
