from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


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
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    telegram_url: Optional[str] = None
    youtube_url: Optional[str] = None
    whatsapp_enabled: bool = False


class SiteSettingsUpdate(BaseModel):
    phone: Optional[str] = Field(default=None, max_length=30)
    email: Optional[str] = Field(default=None, max_length=255)
    address: Optional[str] = Field(default=None, max_length=500)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    about_title: Optional[str] = Field(default=None, max_length=255)
    about_body: Optional[str] = None
    facebook_url: Optional[str] = Field(default=None, max_length=255)
    instagram_url: Optional[str] = Field(default=None, max_length=255)
    telegram_url: Optional[str] = Field(default=None, max_length=255)
    youtube_url: Optional[str] = Field(default=None, max_length=255)

    @field_validator("facebook_url", "instagram_url", "telegram_url", "youtube_url")
    @classmethod
    def _social_url(cls, value):
        # Rendered as links in the footer, so only http(s) is allowed (no javascript: URLs).
        value = (value or "").strip()
        if not value:
            return None
        if not value.lower().startswith(("http://", "https://")):
            raise ValueError("must be an http(s) URL")
        return value


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
