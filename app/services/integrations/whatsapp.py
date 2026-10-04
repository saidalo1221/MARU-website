"""WhatsApp Business Cloud API connector (PRD ТЗ№4 §40-44). Business-initiated WhatsApp messages
must use templates approved by Meta, so every message here is a template send; the exact template
texts to submit are in WHATSAPP_TEMPLATES.md. Configure WHATSAPP_TOKEN (a permanent system-user
token with whatsapp_business_messaging) and WHATSAPP_PHONE_NUMBER_ID in .env. Without them nothing
is sent. Only orders whose customer ticked the opt-in box get messages."""

import logging
import re
from typing import Optional

import requests

from app.config import settings
from app.services.integrations.adapters import MessagingAdapter
from app.services.jobs import PermanentJobError, enqueue, job_handler

logger = logging.getLogger("maru.whatsapp")

API_VERSION = "v21.0"
LANGS = {"ru", "uz", "en"}

# Template names: create each in Meta Business Manager in all three languages.
ORDER_CREATED = "maru_order_created"      # {{1}} first name, {{2}} order number, {{3}} total with currency
ORDER_STATUS = "maru_order_status"        # {{1}} first name, {{2}} order number, {{3}} new status
SHIPMENT_UPDATE = "maru_shipment_update"  # {{1}} first name, {{2}} order number, {{3}} shipment status, {{4}} tracking

_STATUS_TEXT = {
    "new": ("Новый", "Yangi", "New"),
    "payment_pending": ("Ожидает оплаты", "To'lov kutilmoqda", "Awaiting payment"),
    "paid": ("Оплачен", "To'langan", "Paid"),
    "processing": ("В обработке", "Jarayonda", "Processing"),
    "packed": ("Упакован", "Qadoqlangan", "Packed"),
    "shipped": ("Отправлен", "Jo'natilgan", "Shipped"),
    "in_transit": ("В пути", "Yo'lda", "In transit"),
    "delivered": ("Доставлен", "Yetkazib berilgan", "Delivered"),
    "cancelled": ("Отменён", "Bekor qilingan", "Cancelled"),
    "returned": ("Возвращён", "Qaytarilgan", "Returned"),
    "refunded": ("Деньги возвращены", "Pul qaytarilgan", "Refunded"),
    "payment_failed": ("Ошибка оплаты", "To'lov muvaffaqiyatsiz", "Payment failed"),
    "partially_refunded": ("Частичный возврат", "Qisman qaytarilgan", "Partially refunded"),
}


def status_text(status: str, lang: str) -> str:
    row = _STATUS_TEXT.get(status)
    if row is None:
        return status.replace("_", " ")
    return row[{"ru": 0, "uz": 1}.get(lang, 2)]


def enabled() -> bool:
    return bool(settings.WHATSAPP_TOKEN and settings.WHATSAPP_PHONE_NUMBER_ID)


def to_wa_number(phone: Optional[str]) -> Optional[str]:
    """WhatsApp wants the number as digits with the country code and no '+'. A number without a
    country code (a local '90 123 45 67') cannot be routed, so it is skipped rather than guessed."""
    digits = re.sub(r"\D", "", phone or "")
    return digits if 10 <= len(digits) <= 15 else None


def build_message(to: str, template: str, lang: str, params: list) -> dict:
    return {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": template,
            "language": {"code": lang if lang in LANGS else "en"},
            "components": [{"type": "body", "parameters": [{"type": "text", "text": str(p)[:200] or "-"} for p in params]}],
        },
    }


class WhatsAppAdapter(MessagingAdapter):
    name = "whatsapp"

    def send(self, recipient: str, text: str) -> bool:
        # Free-form text is only allowed inside a 24h customer-service window; this platform only
        # starts conversations, so use send_template() instead.
        raise NotImplementedError("WhatsApp business-initiated messages must use templates")


def send_message(message: dict) -> bool:
    """One Cloud API call; raises requests.RequestException on a network/HTTP error."""
    response = requests.post(
        f"https://graph.facebook.com/{API_VERSION}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages",
        headers={"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"},
        json=message,
        timeout=8,
    )
    if response.status_code >= 400:
        logger.warning("WhatsApp rejected the message (HTTP %s): %s", response.status_code, response.text[:300])
    response.raise_for_status()
    return True


def notify_order(db, order, template: str, params: list, dedupe_key: str) -> None:
    """Sends (or queues) one template message for an order whose customer opted in. Never raises."""
    if not enabled() or not getattr(order, "whatsapp_opt_in", False):
        return
    to = to_wa_number(order.phone)
    if to is None:
        return
    message = build_message(to, template, getattr(order, "language", None) or "ru", params)
    try:
        if settings.JOBS_ASYNC and db is not None:
            enqueue(db, "whatsapp.send", message, dedupe_key=f"wa:{dedupe_key}")
        else:
            send_message(message)
    except requests.RequestException as exc:
        logger.warning("WhatsApp send failed (%s)", type(exc).__name__)
    except Exception:  # noqa: BLE001
        logger.exception("WhatsApp send failed")


@job_handler("whatsapp.send")
def _send_job(db, payload: dict) -> None:
    try:
        send_message(payload)
    except requests.RequestException as exc:
        code = getattr(exc.response, "status_code", None)
        if code is not None and 400 <= code < 500 and code != 429:
            raise PermanentJobError(f"WhatsApp refused the message (HTTP {code}); see the log for Meta's reason") from None
        raise RuntimeError(f"WhatsApp request failed ({type(exc).__name__}, HTTP {code or '-'})") from None
