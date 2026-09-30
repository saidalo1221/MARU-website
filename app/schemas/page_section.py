from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

PageKey = Literal["delivery", "payment", "returns", "faq", "contact"]


class PageSectionOut(BaseModel):
    """Public shape, merged with the requested locale's translation."""

    id: int
    title: str
    body: str


class PageSectionAdminOut(BaseModel):
    id: int
    page: str
    title: str
    body: str
    # Translated title for the requested ?lang= (falls back to `title` when
    # untranslated or no lang given) — display-only, for recognizing
    # sections at a glance; editing always targets the base `title`/`body`.
    display_title: str
    sort_order: int
    created_at: datetime
    updated_at: datetime


class PageSectionCreate(BaseModel):
    page: PageKey
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1)


class PageSectionUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    body: Optional[str] = Field(default=None, min_length=1)


class PageSectionMove(BaseModel):
    direction: Literal["up", "down"]


class PageSectionTranslationIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1)


class PageSectionTranslationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    section_id: int
    locale: str
    title: str
    body: str
