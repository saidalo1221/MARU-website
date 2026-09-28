from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AboutSectionOut(BaseModel):
    """Public shape, merged with the requested locale's translation."""

    id: int
    title: str
    body: str


class AboutSectionAdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    body: str
    sort_order: int
    created_at: datetime
    updated_at: datetime


class AboutSectionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1)


class AboutSectionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    body: str | None = Field(default=None, min_length=1)


class AboutSectionMove(BaseModel):
    direction: Literal["up", "down"]


class AboutSectionTranslationIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1)


class AboutSectionTranslationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    section_id: int
    locale: str
    title: str
    body: str
