from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


def _http_url(value: Optional[str]) -> Optional[str]:
    # Rendered as an <img src>, so only http(s) URLs are accepted.
    value = (value or "").strip()
    if not value:
        return None
    if not value.lower().startswith(("http://", "https://")):
        raise ValueError("image_url must be an http(s) URL")
    return value


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    parent_id: Optional[int]
    children: list["CategoryOut"] = []
    image_url: Optional[str] = None
    description: Optional[str] = None
    seo_content: Optional[str] = None


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    parent_id: Optional[int] = None
    description: Optional[str] = None
    seo_content: Optional[str] = None
    image_url: Optional[str] = Field(default=None, max_length=500)

    _image = field_validator("image_url")(_http_url)


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    slug: Optional[str] = Field(default=None, min_length=1, max_length=255)
    parent_id: Optional[int] = None
    description: Optional[str] = None
    seo_content: Optional[str] = None
    image_url: Optional[str] = Field(default=None, max_length=500)

    _image = field_validator("image_url")(_http_url)


class CategoryTranslationIn(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    seo_content: Optional[str] = None


class CategoryTranslationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category_id: int
    locale: str
    name: str
    description: Optional[str] = None
    seo_content: Optional[str] = None


class CategoryPageOut(BaseModel):
    """Public category page (PRD ТЗ№2 §10), merged with the requested locale."""

    id: int
    name: str
    slug: str
    description: Optional[str] = None
    seo_content: Optional[str] = None
    image_url: Optional[str] = None
    parent: Optional["CategoryRef"] = None
    children: list["CategoryRef"] = []


class CategoryRef(BaseModel):
    id: int
    name: str
    slug: str
