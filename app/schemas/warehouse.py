from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WarehouseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    country: str = Field(min_length=1, max_length=100)
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    priority: int = Field(default=100, ge=0)
    is_active: bool = True


class WarehouseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    country: str | None = Field(default=None, min_length=1, max_length=100)
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    priority: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class WarehouseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    country: str
    address: str | None
    latitude: float | None
    longitude: float | None
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
