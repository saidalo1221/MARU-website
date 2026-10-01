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
