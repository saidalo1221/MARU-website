"""PRD ТЗ№4 §80: phones are stored in one shape (digits, optional +)."""

import pytest
from pydantic import ValidationError

from app.schemas.extras import AddressIn, QuoteCreate
from app.schemas.order import CheckoutRequest
from conftest import CHECKOUT_PAYLOAD


def test_checkout_phone_is_normalized_and_validated():
    assert CheckoutRequest(**{**CHECKOUT_PAYLOAD, "phone": "+998 (90) 123-45-67"}).phone == "+998901234567"
    for bad in ("abc", "12", ""):
        with pytest.raises(ValidationError):
            CheckoutRequest(**{**CHECKOUT_PAYLOAD, "phone": bad})


def test_address_and_quote_phone_are_normalized():
    addr = AddressIn(first_name="A", last_name="B", phone="998 90 111 22 33", country="UZ", city="T", address_line="x", postal_code="1")
    assert addr.phone == "998901112233"
    quote = QuoteCreate(name="A", country="UZ", email="a@b.co", phone=" +1 555 010 9999 ")
    assert quote.phone == "+15550109999"
    assert QuoteCreate(name="A", country="UZ", email="a@b.co").phone is None
