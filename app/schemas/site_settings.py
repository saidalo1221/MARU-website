from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class SiteSettingsOut(BaseModel):
    """Public shape — merges base fields with the requested locale's
    translation override, same idea as blog's _apply_translation()."""

    model_config = ConfigDict(from_attributes=True)

    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    about_title: Optional[str]
    about_body: Optional[str]


class SiteSettingsUpdate(BaseModel):
    phone: Optional[str] = Field(default=None, max_length=30)
    email: Optional[str] = Field(default=None, max_length=255)
    address: Optional[str] = Field(default=None, max_length=500)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    about_title: Optional[str] = Field(default=None, max_length=255)
    about_body: Optional[str] = None


class SiteSettingsTranslationIn(BaseModel):
    address: Optional[str] = Field(default=None, max_length=500)
    about_title: Optional[str] = Field(default=None, max_length=255)
    about_body: Optional[str] = None


class SiteSettingsTranslationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    locale: str
    address: Optional[str]
    about_title: Optional[str]
    about_body: Optional[str]
