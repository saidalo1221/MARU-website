"""Refreshes ExchangeRate rows from the live FX feed (PRD ТЗ№3 §14). Meant
to be scheduled externally — daily is plenty (exchangerate-api.com's data
itself only updates once every 24h on the free tier) and keeps this
comfortably under the free tier's 1,500 requests/month:

    0 3 * * * cd /path/to/app && python -m app.tasks.sync_exchange_rates

Same "no task queue yet" pattern as expire_reservations.py /
retry_integrations.py. On failure, the existing (stale but valid)
ExchangeRate rows are left untouched — a provider outage degrades to
"rates didn't update today," not "checkout breaks."
"""

import logging

from app.database import SessionLocal
from app.services.fx_provider import FxProviderError, sync_exchange_rates

logger = logging.getLogger("maru.tasks.sync_exchange_rates")


def run() -> int:
    db = SessionLocal()
    try:
        count = sync_exchange_rates(db)
        logger.info("Synced %d exchange rate(s)", count)
        return count
    except FxProviderError:
        logger.exception("Exchange rate sync failed; keeping existing rates")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
