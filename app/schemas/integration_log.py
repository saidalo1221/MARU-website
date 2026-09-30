from typing import Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.integration_log import IntegrationLogStatus


class IntegrationLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    integration: str
    operation: str
    direction: str
    internal_entity: str
    internal_id: int
    external_id: Optional[str]
    status: IntegrationLogStatus
    error_message: Optional[str]
    attempt: int
    created_at: datetime
    completed_at: Optional[datetime]
