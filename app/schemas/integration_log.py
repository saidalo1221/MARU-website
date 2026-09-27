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
    external_id: str | None
    status: IntegrationLogStatus
    error_message: str | None
    attempt: int
    created_at: datetime
    completed_at: datetime | None
