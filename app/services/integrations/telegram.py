"""Telegram Bot API connector (PRD ТЗ№4 §40-44). Sends a text to a chat id through the bot named in
TELEGRAM_BOT_TOKEN. It does not discover customers: a person has to open the bot and press Start
before the bot may message them, and learning their chat id needs a webhook on a public URL
(`setWebhook`), which only exists once the site is deployed. Until then it is used for staff alerts
(TELEGRAM_ADMIN_CHAT_ID)."""

import logging

import requests

from app.config import settings
from app.services.integrations.adapters import MessagingAdapter

logger = logging.getLogger("maru.telegram")

API = "https://api.telegram.org"


class TelegramAdapter(MessagingAdapter):
    name = "telegram"

    def __init__(self, token: str) -> None:
        self._token = token

    def send(self, recipient: str, text: str) -> bool:
        try:
            r = requests.post(
                f"{API}/bot{self._token}/sendMessage",
                json={"chat_id": recipient, "text": text[:4096], "disable_web_page_preview": True},
                timeout=10,
            )
        except requests.RequestException:
            # Log the failure kind only: the exception text contains the URL, which contains the token.
            logger.error("Telegram request failed (network)")
            return False
        if r.status_code != 200 or not r.json().get("ok"):
            logger.warning("Telegram refused the message (HTTP %s): %s", r.status_code, r.text[:200])
            return False
        return True


def build() -> "TelegramAdapter | None":
    return TelegramAdapter(settings.TELEGRAM_BOT_TOKEN) if settings.TELEGRAM_BOT_TOKEN else None


def notify_admin(text: str) -> bool:
    """Staff alert; a quiet no-op unless both the token and TELEGRAM_ADMIN_CHAT_ID are set."""
    if not (settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_ADMIN_CHAT_ID):
        return False
    return TelegramAdapter(settings.TELEGRAM_BOT_TOKEN).send(settings.TELEGRAM_ADMIN_CHAT_ID, text)


# Staff-facing wording of the new-order alert, in the three site languages. The language comes from
# TELEGRAM_ALERT_LANG (ru, uz or en); "order" uses the language the customer ordered in.
ALERT_TEXT = {
    "en": {
        "title": "New order {n}", "customer": "Customer", "company": "Company", "phone": "Phone", "email": "Email",
        "items": "Items", "subtotal": "Subtotal", "discount": "Discount", "tax": "Tax", "delivery": "Delivery",
        "total": "TOTAL", "payment": "Payment", "method": "Delivery method", "address": "Address", "map": "Map",
        "note": "Note", "open": "Open in admin",
        "status": {"created": "created", "pending": "pending", "authorized": "authorized", "paid": "paid", "failed": "failed",
                   "cancelled": "cancelled", "refunded": "refunded", "partially_refunded": "partially refunded"},
    },
    "ru": {
        "title": "Новый заказ {n}", "customer": "Клиент", "company": "Компания", "phone": "Телефон", "email": "Эл. почта",
        "items": "Товары", "subtotal": "Сумма товаров", "discount": "Скидка", "tax": "Налог", "delivery": "Доставка",
        "total": "ИТОГО", "payment": "Оплата", "method": "Способ доставки", "address": "Адрес", "map": "Карта",
        "note": "Комментарий", "open": "Открыть в админке",
        "status": {"created": "создана", "pending": "ожидает", "authorized": "авторизована", "paid": "оплачена", "failed": "не удалась",
                   "cancelled": "отменена", "refunded": "возвращена", "partially_refunded": "частично возвращена"},
    },
    "uz": {
        "title": "Yangi buyurtma {n}", "customer": "Mijoz", "company": "Kompaniya", "phone": "Telefon", "email": "E-pochta",
        "items": "Mahsulotlar", "subtotal": "Mahsulotlar summasi", "discount": "Chegirma", "tax": "Soliq", "delivery": "Yetkazib berish",
        "total": "JAMI", "payment": "To'lov", "method": "Yetkazib berish usuli", "address": "Manzil", "map": "Xarita",
        "note": "Izoh", "open": "Adminkada ochish",
        "status": {"created": "yaratildi", "pending": "kutilmoqda", "authorized": "tasdiqlandi", "paid": "to'landi", "failed": "muvaffaqiyatsiz",
                   "cancelled": "bekor qilindi", "refunded": "qaytarildi", "partially_refunded": "qisman qaytarildi"},
    },
}


def _alert_language(order, lang=None) -> str:
    choice = (lang or settings.TELEGRAM_ALERT_LANG or "ru").lower()
    if choice == "order":
        choice = (getattr(order, "language", None) or "ru").lower()
    return choice if choice in ALERT_TEXT else "en"


def _money(value, currency: str) -> str:
    return f"{value:,.2f} {currency}"


def build_order_alert(order, lang=None) -> str:
    """The staff message for a new order: who, what, how much, where, and a link to open it."""
    from urllib.parse import quote

    w = ALERT_TEXT[_alert_language(order, lang)]
    lines = [w["title"].format(n=order.order_number), ""]
    lines.append(f"{w['customer']}: {order.first_name} {order.last_name}".rstrip())
    if order.company_name:
        lines.append(f"{w['company']}: {order.company_name}")
    lines.append(f"{w['phone']}: {order.phone}")
    lines.append(f"{w['email']}: {order.email}")
    lines += ["", f"{w['items']}:"]
    for item in order.items:
        variant = f" ({item.variant_name_snapshot})" if item.variant_name_snapshot else ""
        lines.append(
            f"- {item.product_name_snapshot}{variant} [{item.sku_code_snapshot}] "
            f"x{item.quantity} @ {_money(item.unit_price, order.currency)}"
        )
    lines += ["", f"{w['subtotal']}: {_money(order.subtotal_amount, order.currency)}"]
    if order.discount_amount:
        lines.append(f"{w['discount']}: -{_money(order.discount_amount, order.currency)}")
    if order.tax_amount:
        lines.append(f"{w['tax']}: {_money(order.tax_amount, order.currency)}")
    lines.append(f"{w['delivery']}: {_money(order.delivery_amount, order.currency)}")
    lines.append(f"{w['total']}: {_money(order.total_amount, order.currency)}")
    status = getattr(order.payment_status, "value", order.payment_status)
    lines.append(f"{w['payment']}: {order.payment_method} ({w['status'].get(status, status)})")
    lines += ["", f"{w['method']}: {order.delivery_method}"]
    address = ", ".join(p for p in (order.address_line, order.city, order.region, order.postal_code, order.country) if p)
    lines.append(f"{w['address']}: {address}")
    lines.append(f"{w['map']}: https://www.google.com/maps/search/?api=1&query=" + quote(", ".join(p for p in (order.address_line, order.city, order.country) if p)))
    if order.notes:
        lines += ["", f"{w['note']}: {order.notes}"]
    lines += ["", f"{w['open']}: {settings.FRONTEND_URL.rstrip('/')}/admin/orders/{order.id}"]
    return "\n".join(lines)


def notify_new_order(order) -> None:
    """Fire-and-forget staff alert for a new order. The text is built here (while the order is loaded) and
    posted from a background thread, so a slow or unreachable Telegram never delays checkout; failures are
    only logged."""
    if not (settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_ADMIN_CHAT_ID):
        return
    import threading

    try:
        text = build_order_alert(order)
    except Exception:  # noqa: BLE001 - an alert must never break checkout
        logger.exception("Could not build the Telegram order alert")
        return
    threading.Thread(target=notify_admin, args=(text,), daemon=True).start()
