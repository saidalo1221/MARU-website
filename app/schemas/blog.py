from typing import Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BlogCategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class BlogCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)


class BlogCategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    slug: Optional[str] = Field(default=None, min_length=1, max_length=255)


class BlogPostSummary(BaseModel):
    """List view — no `content` (can be long; the detail view has it)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    excerpt: Optional[str]
    cover_image_url: Optional[str]
    author_name: Optional[str]
    published_at: Optional[datetime]
    category: BlogCategoryOut


class BlogPostDetail(BlogPostSummary):
    content: str


class BlogPostWithRelated(BaseModel):
    post: BlogPostDetail
    related: list[BlogPostSummary]


class BlogPostCreate(BaseModel):
    category_id: int
    slug: str = Field(min_length=1, max_length=255)
    title: str = Field(min_length=1, max_length=255)
    excerpt: Optional[str] = None
    content: str = Field(min_length=1)
    cover_image_url: Optional[str] = Field(default=None, max_length=500)
    author_name: Optional[str] = Field(default=None, max_length=100)
    is_published: bool = False
    published_at: Optional[datetime] = None


class BlogPostUpdate(BaseModel):
    category_id: Optional[int] = None
    slug: Optional[str] = Field(default=None, min_length=1, max_length=255)
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    excerpt: Optional[str] = None
    content: Optional[str] = Field(default=None, min_length=1)
    cover_image_url: Optional[str] = Field(default=None, max_length=500)
    author_name: Optional[str] = Field(default=None, max_length=100)
    is_published: Optional[bool] = None
    published_at: Optional[datetime] = None


class BlogPostAdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    slug: str
    title: str
    excerpt: Optional[str]
    content: str
    cover_image_url: Optional[str]
    author_name: Optional[str]
    is_published: bool
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class BlogPostTranslationIn(BaseModel):
    slug: Optional[str] = Field(default=None, max_length=255)
    title: str = Field(min_length=1, max_length=255)
    excerpt: Optional[str] = None
    content: str = Field(min_length=1)


class BlogPostTranslationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    post_id: int
    locale: str
    slug: Optional[str]
    title: str
    excerpt: Optional[str]
    content: str
