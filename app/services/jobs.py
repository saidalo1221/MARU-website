"""Background job queue on the database (PRD ТЗ№3 §88-89, ТЗ№4 §50-54).

    enqueue(db, "notify.order_created", {"order_id": 7})      # from a request handler
    python -m app.tasks.worker                                 # runs them

Handlers are plain functions registered with @job_handler("name"); they get a session and the
payload dict. Raise PermanentJobError for a failure that retrying cannot fix (bad data); any other
exception is retried with a growing delay (JOB_RETRY_BACKOFF_MINUTES) until max_attempts, after
which the job is "dead" (dead-letter queue) and waits for an admin to retry it.
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.models.job import JOB_DEAD, JOB_DONE, JOB_PENDING, JOB_RUNNING, Job

logger = logging.getLogger("maru.jobs")

# A running job whose worker has not finished within this time is assumed lost (crashed worker).
STALE_AFTER = timedelta(minutes=15)


class PermanentJobError(Exception):
    """The job can never succeed (e.g. the order it refers to does not exist); skip the retries."""


_HANDLERS: dict[str, Callable[[Session, dict], None]] = {}


def job_handler(name: str):
    def register(fn):
        _HANDLERS[name] = fn
        return fn

    return register


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _backoff(attempts: int) -> timedelta:
    minutes = [int(m) for m in settings.JOB_RETRY_BACKOFF_MINUTES.split(",") if m.strip()] or [1]
    return timedelta(minutes=minutes[min(max(attempts, 1), len(minutes)) - 1])


def enqueue(
    db: Session,
    job_type: str,
    payload: Optional[dict] = None,
    run_at: Optional[datetime] = None,
    dedupe_key: Optional[str] = None,
    max_attempts: Optional[int] = None,
    commit: bool = True,
) -> Optional[Job]:
    """Adds a job. With a dedupe_key, a second enqueue of the same key is ignored (returns None)
    - used so a retried request cannot queue the same work twice."""
    job = Job(
        job_type=job_type,
        payload=json.dumps(payload or {}, default=str),
        run_at=run_at or _now(),
        dedupe_key=dedupe_key,
        max_attempts=max_attempts or settings.JOB_MAX_ATTEMPTS,
    )
    db.add(job)
    try:
        if commit:
            db.commit()
        else:
            db.flush()
    except IntegrityError:
        db.rollback()
        if dedupe_key is not None:
            return None
        raise
    return job


def recover_stale(db: Session) -> int:
    """Puts jobs back that a crashed worker left "running"."""
    cutoff = _now() - STALE_AFTER
    rows = db.execute(select(Job).where(Job.status == JOB_RUNNING, Job.locked_at < cutoff)).scalars().all()
    for job in rows:
        job.status = JOB_PENDING
        job.locked_by = None
        job.last_error = "Worker stopped before finishing; retrying"
    if rows:
        db.commit()
    return len(rows)


def claim_next(db: Session, worker_id: str) -> Optional[Job]:
    """Takes the oldest due job. On MariaDB `SKIP LOCKED` lets several workers run side by side
    without taking the same job; SQLite (tests) ignores it."""
    job = db.execute(
        select(Job)
        .where(Job.status == JOB_PENDING, Job.run_at <= _now())
        .order_by(Job.run_at, Job.id)
        .limit(1)
        .with_for_update(skip_locked=True)
    ).scalar_one_or_none()
    if job is None:
        db.rollback()
        return None
    job.status = JOB_RUNNING
    job.locked_by = worker_id
    job.locked_at = _now()
    job.attempts += 1
    db.commit()
    return job


def _finish(db: Session, job: Job, error: Optional[str], permanent: bool) -> None:
    if error is None:
        job.status = JOB_DONE
        job.last_error = None
        job.finished_at = _now()
    else:
        job.last_error = error[:4000]
        if permanent or job.attempts >= job.max_attempts:
            job.status = JOB_DEAD
            job.finished_at = _now()
        else:
            job.status = JOB_PENDING
            job.run_at = _now() + _backoff(job.attempts)
    job.locked_by = None
    job.locked_at = None
    db.commit()


def run_job(db: Session, job: Job) -> bool:
    """Runs one claimed job and records the outcome. Returns True on success."""
    handler = _HANDLERS.get(job.job_type)
    if handler is None:
        _finish(db, job, f"No handler registered for {job.job_type}", permanent=True)
        return False
    try:
        handler(db, json.loads(job.payload or "{}"))
    except PermanentJobError as exc:
        db.rollback()
        logger.warning("Job %s (%s) failed permanently: %s", job.id, job.job_type, exc)
        _finish(db, job, str(exc), permanent=True)
        return False
    except Exception as exc:  # noqa: BLE001 - a handler bug must not stop the worker
        db.rollback()
        logger.exception("Job %s (%s) failed (attempt %s)", job.id, job.job_type, job.attempts)
        _finish(db, job, f"{type(exc).__name__}: {exc}", permanent=False)
        return False
    _finish(db, job, None, permanent=False)
    return True


def run_pending(db: Session, worker_id: str, limit: int = 20) -> int:
    """Runs up to `limit` due jobs; returns how many were attempted."""
    recover_stale(db)
    done = 0
    for _ in range(limit):
        job = claim_next(db, worker_id)
        if job is None:
            break
        run_job(db, job)
        done += 1
    return done


def retry_dead(db: Session, job_id: int) -> Optional[Job]:
    """Manual retry of a dead job (DLQ -> pending with a fresh attempt budget)."""
    job = db.get(Job, job_id)
    if job is None or job.status != JOB_DEAD:
        return None
    job.status = JOB_PENDING
    job.attempts = 0
    job.run_at = _now()
    job.finished_at = None
    db.commit()
    return job


def queue_stats(db: Session, now: Optional[datetime] = None) -> dict:
    """Counts per status plus the age of the oldest due job - the "queue backlog" of PRD ТЗ№3 §93."""
    now = now or _now()
    counts = {status: 0 for status in (JOB_PENDING, JOB_RUNNING, JOB_DONE, JOB_DEAD)}
    for status, n in db.execute(select(Job.status, func.count()).group_by(Job.status)).all():
        counts[status] = n
    oldest = db.execute(select(func.min(Job.run_at)).where(Job.status == JOB_PENDING, Job.run_at <= now)).scalar_one()
    return {**counts, "oldest_due_seconds": max(0, int((now - oldest).total_seconds())) if oldest else None}
