import logging

import requests

from app.config import settings
from app.models.order import Order
from app.services.crm.base import CRMBase

logger = logging.getLogger("maru.crm.bitrix24")


class Bitrix24Connector(CRMBase):
    """Pushes orders to Bitrix24 as CRM deals via an incoming webhook (PRD
    section 26). Requires BITRIX24_WEBHOOK_URL in .env — create one under
    Bitrix24 > CRM > Settings > Robots and applications > Inbound webhook,
    granting the "crm" scope; the URL looks like
    https://<portal>.bitrix24.com/rest/1/<token>/.

    Only standard Bitrix24 fields are used (TITLE, OPPORTUNITY, CURRENCY_ID,
    COMMENTS, CONTACT_ID). The rest of the PRD-required data (source, payment
    method, delivery amount, items) is folded into COMMENTS as text, since
    mapping it to structured fields would need portal-specific custom field
    codes (UF_CRM_*) that only exist once configured in your Bitrix24 admin.
    No de-duplication of contacts across different orders from the same
    customer — Bitrix24's own duplicate-control settings are the standard way
    to handle that; this doesn't try to re-implement it."""

    def push_quote(self, quote) -> bool:
        if not settings.BITRIX24_WEBHOOK_URL:
            logger.warning("Bitrix24 not configured, skipping CRM push for quote %s", quote.rfq_number)
            return False

        fields = {
            "TITLE": f"MARU {quote.request_type} request {quote.rfq_number}",
            "NAME": quote.name,
            "COMPANY_TITLE": quote.company or "",
            "EMAIL": [{"VALUE": quote.email, "VALUE_TYPE": "WORK"}],
            "COMMENTS": (
                f"Country: {quote.country}, city: {quote.city}\n"
                f"Products: {quote.products}\nQuantity: {quote.quantity}\nComment: {quote.comment}"
            ),
        }
        if quote.phone:
            fields["PHONE"] = [{"VALUE": quote.phone, "VALUE_TYPE": "WORK"}]
        base_url = settings.BITRIX24_WEBHOOK_URL.rstrip("/")
        try:
            response = requests.post(f"{base_url}/crm.lead.add.json", json={"fields": fields}, timeout=10)
            response.raise_for_status()
            result = response.json()
            if "error" in result:
                logger.error("Bitrix24 rejected quote %s: %s", quote.rfq_number, result)
                return False
            quote.crm_lead_id = str(result.get("result"))
            return True
        except requests.RequestException:
            logger.exception("Failed to push quote %s to Bitrix24", quote.rfq_number)
            return False

    def push_order(self, order: Order) -> bool:
        if not settings.BITRIX24_WEBHOOK_URL:
            logger.warning("Bitrix24 not configured, skipping CRM push for order %s", order.order_number)
            return False

        base_url = settings.BITRIX24_WEBHOOK_URL.rstrip("/")
        items_summary = "; ".join(
            f"{item.quantity}x {item.product_name_snapshot} ({item.sku_code_snapshot})" for item in order.items
        )
        comments = (
            f"Order: {order.order_number}\n"
            f"Source: {order.source}\n"
            f"Payment method: {order.payment_method}, delivery: {order.delivery_method} "
            f"({order.delivery_amount} {order.currency})\n"
            f"Status: {order.status.value}\n"
            f"Ship to: {order.country}, {order.city}\n"
            f"Items: {items_summary}"
        )

        try:
            if order.crm_deal_id is None:
                contact_response = requests.post(
                    f"{base_url}/crm.contact.add.json",
                    json={
                        "fields": {
                            "NAME": order.first_name,
                            "LAST_NAME": order.last_name,
                            "EMAIL": [{"VALUE": order.email, "VALUE_TYPE": "WORK"}],
                            "PHONE": [{"VALUE": order.phone, "VALUE_TYPE": "WORK"}],
                        }
                    },
                    timeout=10,
                )
                contact_response.raise_for_status()
                contact_id = contact_response.json().get("result")

                deal_fields = {
                    "TITLE": f"MARU order {order.order_number}",
                    "OPPORTUNITY": str(order.total_amount),
                    "CURRENCY_ID": order.currency,
                    "COMMENTS": comments,
                }
                if contact_id:
                    deal_fields["CONTACT_ID"] = contact_id

                deal_response = requests.post(f"{base_url}/crm.deal.add.json", json={"fields": deal_fields}, timeout=10)
                deal_response.raise_for_status()
                result = deal_response.json()
                if "error" in result:
                    logger.error("Bitrix24 rejected order %s: %s", order.order_number, result)
                    return False
                order.crm_deal_id = str(result.get("result"))
            else:
                response = requests.post(
                    f"{base_url}/crm.deal.update.json",
                    json={
                        "id": order.crm_deal_id,
                        "fields": {"COMMENTS": comments, "OPPORTUNITY": str(order.total_amount)},
                    },
                    timeout=10,
                )
                response.raise_for_status()
            return True
        except requests.RequestException:
            logger.exception("Failed to push order %s to Bitrix24", order.order_number)
            return False
