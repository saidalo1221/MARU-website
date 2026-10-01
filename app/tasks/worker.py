"""Runs the background jobs (PRD ТЗ№3 §89). Two ways to run it:

    python -m app.tasks.worker --once      # one pass; schedule it every minute from cron
    python -m app.tasks.worker             # keep running (systemd service, see deploy/maru-worker.service)

Several workers can run at once; a job is only ever claimed by one of them.
"""

import argparse
import logging
import os
import socket
import time

from app.database import SessionLocal
from app.services import jobs
from app.services.notifications import queued  # noqa: F401 - registers the notify.* handlers
from app.services import webhooks  # noqa: F401 - registers the webhook.* dispatch
from app.services.integrations import ga4, meta  # noqa: F401 - registers the ga4.send / meta.send handlers

logger = logging.getLogger("maru.worker")


def run_once(limit: int = 50) -> int:
    worker_id = f"{socket.gethostname()}:{os.getpid()}"
    db = SessionLocal()
    try:
        return jobs.run_pending(db, worker_id, limit=limit)
    finally:
        db.close()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="process the due jobs once and exit")
    parser.add_argument("--interval", type=float, default=5.0, help="seconds to sleep when idle")
    args = parser.parse_args(argv)

    if args.once:
        print(f"jobs run: {run_once()}")
        return 0

    logger.info("Worker started")
    while True:
        try:
            if run_once() == 0:
                time.sleep(args.interval)
        except Exception:  # noqa: BLE001 - the loop must survive a database hiccup
            logger.exception("Worker pass failed; retrying shortly")
            time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
