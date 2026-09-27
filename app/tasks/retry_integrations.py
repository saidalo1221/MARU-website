"""Retries integrations whose last recorded attempt failed (PRD ТЗ№4 §52-54).
This project has no task queue yet (see TODO.md), so — same as
expire_reservations.py — this is a plain script meant to be scheduled
externally, e.g. every 5-15 minutes:

    */10 * * * * cd /path/to/app && python -m app.tasks.retry_integrations

Rows that exhaust their retry budget become DEAD_LETTER and are only
retried again by an admin, via POST /admin/integration-logs/{id}/retry.
"""

import logging

from app.database import SessionLocal
from app.services.integrations.retry import retry_failed_integrations

logger = logging.getLogger("maru.tasks.retry_integrations")


def run() -> int:
    db = SessionLocal()
    try:
        count = retry_failed_integrations(db)
        logger.info("Retried %d failed integration(s)", count)
        return count
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
