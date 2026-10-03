from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.enums import PaymentStatus


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    provider: str
    provider_transaction_id: Optional[str]
    amount: Decimal
    currency: str
    status: PaymentStatus
    paid_at: Optional[datetime]
    created_at: datetime
