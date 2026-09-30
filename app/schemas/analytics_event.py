from typing import Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AnalyticsEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_name: str
    user_id: Optional[int]
    session_id: Optional[str]
    properties: Optional[str]
    created_at: datetime
