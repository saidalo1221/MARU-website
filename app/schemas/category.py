from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    parent_id: Optional[int]
    children: list["CategoryOut"] = []


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    parent_id: Optional[int] = None


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    slug: Optional[str] = Field(default=None, min_length=1, max_length=255)
    parent_id: Optional[int] = None


class CategoryTranslationIn(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class CategoryTranslationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category_id: int
    locale: str
    name: str
