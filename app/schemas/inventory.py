from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class InventoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku_id: int
    warehouse_id: int
    stock: int
    reserved: int
    incoming: int
    min_stock: int
    available: int


class InventoryCreate(BaseModel):
    warehouse_id: int
    stock: int = Field(default=0, ge=0)
    incoming: int = Field(default=0, ge=0)
    min_stock: int = Field(default=0, ge=0)


class InventoryUpdate(BaseModel):
    stock: Optional[int] = Field(default=None, ge=0)
    incoming: Optional[int] = Field(default=None, ge=0)
    min_stock: Optional[int] = Field(default=None, ge=0)
