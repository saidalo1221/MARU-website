from typing import Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WarehouseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    country: str = Field(min_length=1, max_length=100)
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    priority: int = Field(default=100, ge=0)
    is_active: bool = True


class WarehouseUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    country: Optional[str] = Field(default=None, min_length=1, max_length=100)
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    priority: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = None


class WarehouseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    country: str
    address: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
