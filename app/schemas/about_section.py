from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class AboutSectionOut(BaseModel):
    """Public shape, merged with the requested locale's translation."""

    id: int
    title: str
    body: str


class AboutSectionAdminOut(BaseModel):
    id: int
    title: str
    body: str
    # Translated title for the requested ?lang= (falls back to `title` when
    # untranslated or no lang given) — display-only, for recognizing
    # sections at a glance; editing always targets the base `title`/`body`.
    display_title: str
    sort_order: int
    created_at: datetime
    updated_at: datetime


class AboutSectionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1)


class AboutSectionUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    body: Optional[str] = Field(default=None, min_length=1)


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
