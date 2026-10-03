"""Numbers for the admin dashboard (PRD ТЗ№1 §27-28, §59-60). Everything is computed from orders and
analytics events, in USD, using the stored exchange rates.

Definitions (also shown on the dashboard):
- an order "counts" once it is paid or beyond (not new / payment pending / failed / cancelled); refunds
  are not netted out;
- revenue = order total in USD; "today" and "this month" are UTC calendar days / months;
- visitors = distinct analytics sessions that viewed a product or the catalogue in the period;
- conversion rate = counted orders / visitors;
- gross profit = (item revenue after discount - item cost) over order lines whose SKU had a cost price at
  purchase time; `cost_coverage` says what share of item revenue that is;
- a customer is the account id, or the lower-cased e-mail for guests;
- CAC = marketing spend of the month / customers whose first counted order was in the month;
- ROAS = revenue of orders attributed to paid media (utm_medium cpc/ppc/paid/paid_social/display) / spend.
"""

import json
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.analytics_event import AnalyticsEvent
from app.models.enums import OrderStatus
from app.models.marketing_spend import MarketingSpend
from app.models.order import Order
from app.models.order_item import OrderItem
from app.services.badges import _SOLD_STATUSES
from app.services.currency import CurrencyError, get_rate_to_usd

PAID_MEDIA = {"cpc", "ppc", "paid", "paid_social", "paidsocial", "display"}
Z = Decimal("0")


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _q(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01")))


def _usd_converter(db: Session):
    cache: dict = {}

    def to_usd(amount: Decimal, currency: str) -> Decimal:
        if currency not in cache:
            try:
                cache[currency] = get_rate_to_usd(db, currency)
            except CurrencyError:
                cache[currency] = None  # no rate configured: the order is left out of USD totals
        rate = cache[currency]
        return amount / rate if rate else Z

    return to_usd


def _market(country: Optional[str]) -> str:
    c = (country or "").strip().lower()
    if c in ("uzbekistan", "uz", "узбекистан", "o'zbekiston"):
        return "Uzbekistan"
    if c in ("kazakhstan", "kz", "казахстан", "qozog'iston"):
        return "Kazakhstan"
    return "International"


def _customer_key(order: Order) -> str:
    return f"u{order.user_id}" if order.user_id is not None else f"e{(order.email or '').strip().lower()}"


def _medium(order: Order) -> str:
    try:
        return str((json.loads(order.attribution) if order.attribution else {}).get("utm_medium", "")).lower()
    except ValueError:
        return ""


def _source(order: Order) -> str:
    try:
        attr = json.loads(order.attribution) if order.attribution else {}
    except ValueError:
        attr = {}
    return str(attr.get("utm_source") or order.source or "direct").lower()


def _visitors(db: Session, start: datetime, end: datetime) -> int:
    return db.execute(
        select(func.count(func.distinct(AnalyticsEvent.session_id))).where(
            AnalyticsEvent.event_name.in_(("view_item", "view_item_list")),
            AnalyticsEvent.session_id.is_not(None),
            AnalyticsEvent.created_at >= start,
            AnalyticsEvent.created_at < end,
        )
    ).scalar_one()


def _sessions(db: Session, event: str, start: datetime, end: datetime) -> int:
    return db.execute(
        select(func.count(func.distinct(AnalyticsEvent.session_id))).where(
            AnalyticsEvent.event_name == event,
            AnalyticsEvent.session_id.is_not(None),
            AnalyticsEvent.created_at >= start,
            AnalyticsEvent.created_at < end,
        )
    ).scalar_one()


def build_dashboard(db: Session, now: Optional[datetime] = None) -> dict:
    now = now or _now()
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = day_start.replace(day=1)
    next_day = day_start + timedelta(days=1)
    funnel_start = now - timedelta(days=30)
    to_usd = _usd_converter(db)

    orders = db.execute(select(Order).where(Order.status.in_(_SOLD_STATUSES)).order_by(Order.created_at)).scalars().all()

    # first counted order per customer, and orders per customer, over all time
    first_order: dict = {}
    per_customer: dict = defaultdict(list)
    for o in orders:
        key = _customer_key(o)
        first_order.setdefault(key, o.created_at)
        per_customer[key].append(o)

    def revenue(o: Order) -> Decimal:
        return to_usd(o.total_amount, o.currency)

    # --- items: units and profit
    items = db.execute(
        select(OrderItem.order_id, OrderItem.quantity, OrderItem.line_total, OrderItem.discount_amount, OrderItem.unit_cost_usd, OrderItem.currency)
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.status.in_(_SOLD_STATUSES))
    ).all()
    by_order_items: dict = defaultdict(list)
    for row in items:
        by_order_items[row.order_id].append(row)

    def units(o: Order) -> int:
        return sum(r.quantity for r in by_order_items.get(o.id, []))

    def profit_parts(o: Order):
        """(item revenue USD, profit USD) over the order's lines that have a known cost, plus all item revenue."""
        known_rev = known_profit = all_rev = Z
        for r in by_order_items.get(o.id, []):
            net = to_usd(r.line_total - (r.discount_amount or Z), r.currency)
            all_rev += net
            if r.unit_cost_usd is not None:
                known_rev += net
                known_profit += net - r.unit_cost_usd * r.quantity
        return all_rev, known_rev, known_profit

    today_orders = [o for o in orders if day_start <= o.created_at < next_day]
    month_orders = [o for o in orders if o.created_at >= month_start]
    today_rev = sum((revenue(o) for o in today_orders), Z)
    month_rev = sum((revenue(o) for o in month_orders), Z)

    all_rev = known_rev = known_profit = Z
    for o in month_orders:
        a, k, p = profit_parts(o)
        all_rev += a
        known_rev += k
        known_profit += p

    month_customers = {_customer_key(o) for o in month_orders}
    new_in_month = {k for k in month_customers if first_order[k] >= month_start}
    visitors_month = _visitors(db, month_start, next_day)

    # --- markets (this month)
    markets: dict = defaultdict(lambda: {"orders": 0, "revenue": Z})
    for name in ("Uzbekistan", "Kazakhstan", "International"):
        markets[name]
    for o in month_orders:
        m = markets[_market(o.country)]
        m["orders"] += 1
        m["revenue"] += revenue(o)

    # --- customers (all time)
    total_customers = len(per_customer)
    repeat_customers = sum(1 for v in per_customer.values() if len(v) >= 2)
    lifetime = sum((revenue(o) for o in orders), Z)

    # --- marketing (this month)
    spend = db.execute(select(func.coalesce(func.sum(MarketingSpend.amount_usd), 0)).where(MarketingSpend.month == month_start.date())).scalar_one()
    spend = Decimal(str(spend))
    paid_rev = sum((revenue(o) for o in month_orders if _medium(o) in PAID_MEDIA), Z)

    # --- sources (this month)
    sources: dict = defaultdict(lambda: {"orders": 0, "revenue": Z})
    for o in month_orders:
        s = sources[_source(o)]
        s["orders"] += 1
        s["revenue"] += revenue(o)

    # --- funnel (last 30 days, distinct analytics sessions; orders counted directly)
    stage_visitors = _visitors(db, funnel_start, next_day)
    stages = [
        ("visitors", stage_visitors),
        ("product_view", _sessions(db, "view_item", funnel_start, next_day)),
        ("add_to_cart", _sessions(db, "add_to_cart", funnel_start, next_day)),
        ("checkout", _sessions(db, "begin_checkout", funnel_start, next_day)),
        ("payment", _sessions(db, "add_payment_info", funnel_start, next_day)),
        ("order", sum(1 for o in orders if o.created_at >= funnel_start)),
        ("repeat_order", sum(1 for v in per_customer.values() if len(v) >= 2 and v[-1].created_at >= funnel_start)),
    ]
    funnel = []
    previous = None
    for name, count in stages:
        funnel.append({"stage": name, "count": count, "rate_from_previous": (round(count / previous, 4) if previous else None)})
        previous = count if count else None

    return {
        "generated_at": now.isoformat(),
        "currency": "USD",
        "today": {
            "orders": len(today_orders),
            "revenue": _q(today_rev),
            "units": sum(units(o) for o in today_orders),
            "average_order_value": _q(today_rev / len(today_orders)) if today_orders else None,
        },
        "month": {
            "revenue": _q(month_rev),
            "orders": len(month_orders),
            "customers": len(month_customers),
            "gross_profit": _q(known_profit) if known_rev > 0 else None,
            "gross_margin": round(float(known_profit / known_rev), 4) if known_rev > 0 else None,
            "cost_coverage": round(float(known_rev / all_rev), 4) if all_rev > 0 else None,
            "conversion_rate": round(len(month_orders) / visitors_month, 4) if visitors_month else None,
            "visitors": visitors_month,
        },
        "markets": [{"market": k, "orders": v["orders"], "revenue": _q(v["revenue"])} for k, v in markets.items()],
        "customers": {
            "total": total_customers,
            "new_this_month": len(new_in_month),
            "returning_this_month": len(month_customers) - len(new_in_month),
            "repeat_purchase_rate": round(repeat_customers / total_customers, 4) if total_customers else None,
            "lifetime_value": _q(lifetime / total_customers) if total_customers else None,
            "orders_per_customer": round(len(orders) / total_customers, 2) if total_customers else None,
        },
        "marketing": {
            "spend": _q(spend),
            "cac": _q(spend / len(new_in_month)) if spend > 0 and new_in_month else None,
            "roas": round(float(paid_rev / spend), 2) if spend > 0 else None,
            "paid_media_revenue": _q(paid_rev),
        },
        "sources": sorted(
            ({"source": k, "orders": v["orders"], "revenue": _q(v["revenue"])} for k, v in sources.items()),
            key=lambda r: -r["revenue"],
        ),
        "funnel": funnel,
    }


def month_start_of(value: date) -> date:
    return value.replace(day=1)
