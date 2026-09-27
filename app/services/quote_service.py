from sqlalchemy.orm import Session

from app.models.enums import OrderStatus
from app.models.order import Order, OrderType
from app.models.order_item import OrderItem
from app.models.order_status_history import OrderStatusHistory
from app.models.quote_request import QuoteRequest, QuoteStatus
from app.models.user import User
from app.schemas.extras import ConvertQuoteToOrderRequest
from app.services.audit import log_audit
from app.services.order_service import generate_order_number  # reuse, don't duplicate the format


class QuoteConversionError(Exception):
    """Raised for a convert request the router should turn into a 4xx response."""


def convert_quote_to_order(db: Session, quote: QuoteRequest, payload: ConvertQuoteToOrderRequest, admin: User) -> Order:
    """PRD ТЗ№4 §16/§85: once a quote is ACCEPTED, create an order at the
    quoted price — that price is a snapshot, so a later change to the quote
    (there isn't one once ACCEPTED, but belt-and-suspenders) never touches
    the order. The RFQ form (PRD ТЗ№2 §32) collects free-text products/
    quantity, not per-SKU line items, so the resulting order has exactly one
    line item describing the whole quote rather than fabricated SKU rows."""
    if quote.order_id is not None:
        raise QuoteConversionError(f"Quote {quote.rfq_number} was already converted to order {quote.order_id}")
    if quote.status != QuoteStatus.ACCEPTED:
        raise QuoteConversionError(f"Quote must be ACCEPTED before conversion (currently {quote.status.value})")
    if quote.proposed_price is None or quote.currency is None:
        raise QuoteConversionError("Quote has no proposed_price/currency to snapshot into an order")

    if payload.first_name is not None:
        first_name, last_name = payload.first_name, (payload.last_name or "")
    else:
        parts = quote.name.split(maxsplit=1)
        first_name = parts[0]
        last_name = payload.last_name or (parts[1] if len(parts) > 1 else "")

    order = Order(
        order_number=generate_order_number(),
        user_id=quote.user_id,
        status=OrderStatus.NEW,
        customer_type_snapshot="wholesale" if quote.request_type in ("wholesale", "distributor") else "retail",
        currency=quote.currency,
        subtotal_amount=quote.proposed_price,
        discount_amount=0,
        delivery_amount=0,
        total_amount=quote.proposed_price,
        order_type=OrderType.COMPANY if quote.company else OrderType.INDIVIDUAL,
        first_name=first_name,
        last_name=last_name,
        phone=quote.phone or "",
        email=quote.email,
        country=quote.country,
        city=quote.city or "",
        address_line=payload.address_line,
        postal_code=payload.postal_code,
        delivery_method=payload.delivery_method,
        payment_method=payload.payment_method,
        source=quote.source,
        company_name=quote.company,
        contact_person=quote.name,
        notes=f"Converted from quote {quote.rfq_number}" + (f": {quote.comment}" if quote.comment else ""),
    )
    db.add(order)
    db.flush()

    order.items.append(
        OrderItem(
            sku_id=None,
            sku_code_snapshot="RFQ",
            product_name_snapshot=(quote.products or f"Quote {quote.rfq_number}")[:255],
            variant_name_snapshot=quote.quantity,
            unit_price=quote.proposed_price,
            quantity=1,
            line_total=quote.proposed_price,
            currency=quote.currency,
        )
    )
    db.add(OrderStatusHistory(order_id=order.id, from_status=None, to_status=OrderStatus.NEW, changed_by_user_id=admin.id))

    quote.order_id = order.id
    log_audit(db, admin, "quote_converted_to_order", "quote", quote.id, None, {"order_id": order.id})

    db.commit()
    db.refresh(order)
    return order
