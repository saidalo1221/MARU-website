"""Emails people who asked to be told when a SKU is back in stock (PRD ТЗ№2
§20). Each alert fires once. Schedule it (cron/systemd timer, every 10-15 min):

    python -m app.tasks.notify_back_in_stock
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.sku import SKU
from app.models.stock_alert import StockAlert
from app.services.notifications.email import EmailNotifier
from app.services.order_service import available_stock


def notify_back_in_stock(db: Session, notifier=None) -> int:
    """Returns how many alerts were sent. Commits per alert so one failing row
    cannot block or duplicate the rest."""
    notifier = notifier or EmailNotifier()
    alerts = db.execute(select(StockAlert).where(StockAlert.notified_at.is_(None))).scalars().all()
    stock_cache: dict[int, int] = {}
    sent = 0
    for alert in alerts:
        sku = db.get(SKU, alert.sku_id)
        if sku is None or not sku.is_active:
            continue
        if alert.sku_id not in stock_cache:
            stock_cache[alert.sku_id] = available_stock(db, alert.sku_id)
        if stock_cache[alert.sku_id] <= 0:
            continue
        try:
            notifier.back_in_stock(alert.email, sku.variant.product.name, sku.variant.product.slug, db=db)
            alert.notified_at = datetime.now(timezone.utc).replace(tzinfo=None)
            db.commit()
            sent += 1
        except Exception:
            db.rollback()
    return sent


if __name__ == "__main__":
    session = SessionLocal()
    try:
        print(f"back-in-stock emails sent: {notify_back_in_stock(session)}")
    finally:
        session.close()
