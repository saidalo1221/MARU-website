from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_type: str
    status: str
    attempts: int
    max_attempts: int
    run_at: datetime
    last_error: Optional[str]
    created_at: datetime
    finished_at: Optional[datetime]


class JobStatsOut(BaseModel):
    pending: int
    running: int
    done: int
    dead: int
    oldest_due_seconds: Optional[int]
