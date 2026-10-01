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


class IntegrationHealthOut(BaseModel):
    integration: str
    status: str  # HEALTHY | DEGRADED | FAILED | DISABLED
    success_24h: int
    failed_24h: int
    dead_letter_24h: int
    last_success_at: Optional[datetime]
    avg_latency_ms: Optional[int] = None
    max_latency_ms: Optional[int] = None
    pending_retries: int = 0
    dead_letters_open: int = 0
    sync_lag_seconds: Optional[int] = None
