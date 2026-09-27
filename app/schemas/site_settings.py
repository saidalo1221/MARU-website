from pydantic import BaseModel, ConfigDict, Field


class SiteSettingsOut(BaseModel):
    """Public shape — merges base fields with the requested locale's
    translation override, same idea as blog's _apply_translation()."""

    model_config = ConfigDict(from_attributes=True)

    phone: str | None
    email: str | None
    address: str | None
    latitude: float | None
    longitude: float | None
    about_title: str | None
    about_body: str | None


class SiteSettingsUpdate(BaseModel):
    phone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=255)
    address: str | None = Field(default=None, max_length=500)
    latitude: float | None = None
    longitude: float | None = None
    about_title: str | None = Field(default=None, max_length=255)
    about_body: str | None = None


class SiteSettingsTranslationIn(BaseModel):
    address: str | None = Field(default=None, max_length=500)
    about_title: str | None = Field(default=None, max_length=255)
    about_body: str | None = None


class SiteSettingsTranslationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    locale: str
    address: str | None
    about_title: str | None
    about_body: str | None
