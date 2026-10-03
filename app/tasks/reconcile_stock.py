"""Reports (and optionally repairs) drift in Inventory.reserved. Schedule the
report nightly and look at the output:

    python -m app.tasks.reconcile_stock          # report only
    python -m app.tasks.reconcile_stock --fix    # also reset drifted counters

Exit status is 1 when mismatches were found, so cron/monitoring can alert."""

import sys

from app.database import SessionLocal
from app.services.notifications.email import EmailNotifier
from app.services.stock_reconciliation import find_mismatches, fix_reserved_drift


def _describe(m) -> str:
    return (
        f"{m.problem}: inventory={m.inventory_id} sku={m.sku_id} warehouse={m.warehouse_id} "
        f"stock={m.stock} reserved={m.reserved} expected_reserved={m.expected_reserved}"
    )


def alert_on_mismatches(mismatches, notifier=None) -> bool:
    """Emails ALERT_EMAIL a summary when there is drift. Returns True if an
    alert was attempted. Never raises (the notifier logs its own failures)."""
    if not mismatches:
        return False
    notifier = notifier or EmailNotifier()
    lines = [_describe(m) for m in mismatches[:50]]
    if len(mismatches) > 50:
        lines.append(f"... and {len(mismatches) - 50} more")
    notifier.admin_alert(
        f"MARU stock reconciliation: {len(mismatches)} mismatch(es)",
        "\n".join(lines) + "\n\nRun: python -m app.tasks.reconcile_stock [--fix]",
    )
    return True


def main(argv: list[str]) -> int:
    session = SessionLocal()
    try:
        mismatches = find_mismatches(session)
        for m in mismatches:
            print(_describe(m))
        print(f"{len(mismatches)} mismatch(es)")
        alert_on_mismatches(mismatches)
        if "--fix" in argv and mismatches:
            print(f"fixed {fix_reserved_drift(session, mismatches)} drifted row(s)")
        return 1 if mismatches else 0
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
