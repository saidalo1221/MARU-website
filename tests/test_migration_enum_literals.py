"""SQLAlchemy stores an Enum column's member NAME ('PAID'), not its value ('paid'). A migration that
writes lowercase values into such a column leaves rows the app cannot read (LookupError -> HTTP 500).
SQLite tests build the schema from the models, so they cannot see this; check the SQL text instead."""

import re
from pathlib import Path

from app.models.enums import OrderStatus, PaymentStatus

SQL = Path(__file__).resolve().parent.parent / "app" / "migration_2026_session12.sql"


def _section(text, start, end):
    i = text.index(start)
    return text[i:text.index(end, i)]


def test_payment_ledger_migration_uses_enum_names():
    block = _section(SQL.read_text(encoding="utf-8"), "-- Payments ledger", "-- Product-level tax")
    code = "\n".join(l for l in block.splitlines() if not l.strip().startswith("--"))
    literals = set(re.findall(r"'([^']*)'", code))
    names = {m.name for m in OrderStatus} | {m.name for m in PaymentStatus}
    # everything that looks like a status word must be an enum NAME
    status_like = {l for l in literals if re.fullmatch(r"[A-Za-z_]+", l) and l.lower() in {n.lower() for n in names}}
    assert status_like and status_like <= names, f"lowercase enum literals in migration: {status_like - names}"
