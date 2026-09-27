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
    name: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=255)


class BlogPostSummary(BaseModel):
    """List view — no `content` (can be long; the detail view has it)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    excerpt: str | None
    cover_image_url: str | None
    author_name: str | None
    published_at: datetime | None
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
    excerpt: str | None = None
    content: str = Field(min_length=1)
    cover_image_url: str | None = Field(default=None, max_length=500)
    author_name: str | None = Field(default=None, max_length=100)
    is_published: bool = False
    published_at: datetime | None = None


class BlogPostUpdate(BaseModel):
    category_id: int | None = None
    slug: str | None = Field(default=None, min_length=1, max_length=255)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    excerpt: str | None = None
    content: str | None = Field(default=None, min_length=1)
    cover_image_url: str | None = Field(default=None, max_length=500)
    author_name: str | None = Field(default=None, max_length=100)
    is_published: bool | None = None
    published_at: datetime | None = None


class BlogPostAdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    slug: str
    title: str
    excerpt: str | None
    content: str
    cover_image_url: str | None
    author_name: str | None
    is_published: bool
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime


class BlogPostTranslationIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    excerpt: str | None = None
    content: str = Field(min_length=1)


class BlogPostTranslationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    post_id: int
    locale: str
    title: str
    excerpt: str | None
    content: str
