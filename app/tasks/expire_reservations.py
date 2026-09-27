"""Releases stock reservations for orders that never got paid within
RESERVATION_TTL_MINUTES (PRD ТЗ№3 §19/§63). This project has no task queue
yet (see TODO.md), so this is a plain script meant to be scheduled
externally, e.g. a cron entry or a Windows Task Scheduler / systemd timer job
every 1-5 minutes:

    * * * * * cd /path/to/app && python -m app.tasks.expire_reservations

create_order() also calls the same sweep opportunistically on every checkout,
so in practice stock rarely stays reserved past its TTL even without this
running — but nothing frees it for a SKU nobody else tries to buy until this
(or the next checkout for that SKU) runs.
"""

import logging

from app.database import SessionLocal
from app.services.order_service import expire_stale_reservations

logger = logging.getLogger("maru.tasks.expire_reservations")


def run() -> int:
    db = SessionLocal()
    try:
        count = expire_stale_reservations(db)
        logger.info("Expired %d stale order reservation(s)", count)
        return count
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
