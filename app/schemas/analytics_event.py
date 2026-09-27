from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AnalyticsEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_name: str
    user_id: int | None
    session_id: str | None
    properties: str | None
    created_at: datetime
