from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class OrderDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    doc_type: str
    status: str
    external_id: Optional[str]
    filename: str
    content_type: str
    size_bytes: int
    created_at: datetime


class DocumentLinkOut(BaseModel):
    url: str
    expires_in_seconds: int
