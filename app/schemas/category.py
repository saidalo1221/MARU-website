from pydantic import BaseModel, ConfigDict, Field


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    parent_id: int | None
    children: list["CategoryOut"] = []


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    parent_id: int | None = None


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=255)
    parent_id: int | None = None


class CategoryTranslationIn(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class CategoryTranslationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category_id: int
    locale: str
    name: str
