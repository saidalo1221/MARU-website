from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.blog_category import BlogCategory
from app.models.blog_post import BlogPost
from app.models.blog_post_translation import BlogPostTranslation
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.blog import (
    BlogCategoryCreate,
    BlogCategoryOut,
    BlogCategoryUpdate,
    BlogPostAdminOut,
    BlogPostCreate,
    BlogPostTranslationIn,
    BlogPostTranslationOut,
    BlogPostUpdate,
)

router = APIRouter(prefix="/admin/blog", tags=["admin-blog"])


# --- Categories --------------------------------------------------------

@router.get("/categories", response_model=list[BlogCategoryOut])
def list_categories(
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> list[BlogCategory]:
    return list(db.execute(select(BlogCategory).order_by(BlogCategory.name)).scalars().all())


@router.post("/categories", response_model=BlogCategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: BlogCategoryCreate,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> BlogCategory:
    category = BlogCategory(**payload.model_dump())
    db.add(category)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category slug already exists") from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create category") from exc
    db.refresh(category)
    return category


@router.patch("/categories/{category_id}", response_model=BlogCategoryOut)
def update_category(
    category_id: int,
    payload: BlogCategoryUpdate,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> BlogCategory:
    category = db.get(BlogCategory, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    try:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(category, field, value)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category slug already exists") from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update category") from exc
    db.refresh(category)
    return category


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> None:
    category = db.get(BlogCategory, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    has_posts = db.execute(select(BlogPost.id).where(BlogPost.category_id == category_id).limit(1)).scalar_one_or_none()
    if has_posts is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category has posts")
    try:
        db.delete(category)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete category") from exc


# --- Posts ---------------------------------------------------------------

@router.get("/posts", response_model=list[BlogPostAdminOut])
def list_posts(
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> list[BlogPost]:
    """Every post regardless of published state (unlike the public /blog/posts)."""
    return list(db.execute(select(BlogPost).order_by(BlogPost.id.desc())).scalars().all())


@router.post("/posts", response_model=BlogPostAdminOut, status_code=status.HTTP_201_CREATED)
def create_post(
    payload: BlogPostCreate,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> BlogPost:
    if db.get(BlogCategory, payload.category_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found")
    post = BlogPost(**payload.model_dump())
    db.add(post)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Post slug already exists") from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create post") from exc
    db.refresh(post)
    return post


@router.get("/posts/{post_id}", response_model=BlogPostAdminOut)
def get_post(
    post_id: int,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> BlogPost:
    post = db.get(BlogPost, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


@router.patch("/posts/{post_id}", response_model=BlogPostAdminOut)
def update_post(
    post_id: int,
    payload: BlogPostUpdate,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> BlogPost:
    post = db.get(BlogPost, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    data = payload.model_dump(exclude_unset=True)
    if "category_id" in data and db.get(BlogCategory, data["category_id"]) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found")

    try:
        for field, value in data.items():
            setattr(post, field, value)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Post slug already exists") from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update post") from exc
    db.refresh(post)
    return post


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> None:
    post = db.get(BlogPost, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    try:
        db.delete(post)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete post") from exc


@router.get("/posts/{post_id}/translations", response_model=list[BlogPostTranslationOut])
def list_post_translations(
    post_id: int,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> list[BlogPostTranslation]:
    if db.get(BlogPost, post_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return list(db.execute(select(BlogPostTranslation).where(BlogPostTranslation.post_id == post_id)).scalars().all())


@router.put("/posts/{post_id}/translations/{locale}", response_model=BlogPostTranslationOut)
def upsert_post_translation(
    post_id: int,
    locale: Literal["ru", "uz", "en"],
    payload: BlogPostTranslationIn,
    user: User = Depends(require_role(UserRole.MARKETING_MANAGER)),
    db: Session = Depends(get_db),
) -> BlogPostTranslation:
    if db.get(BlogPost, post_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    if payload.slug:
        conflict = db.execute(
            select(BlogPostTranslation.id).where(
                BlogPostTranslation.locale == locale,
                BlogPostTranslation.slug == payload.slug,
                BlogPostTranslation.post_id != post_id,
            )
        ).scalar_one_or_none()
        if conflict is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slug already exists for this locale")

    try:
        translation = db.execute(
            select(BlogPostTranslation).where(
                BlogPostTranslation.post_id == post_id, BlogPostTranslation.locale == locale
            )
        ).scalar_one_or_none()

        if translation is None:
            translation = BlogPostTranslation(post_id=post_id, locale=locale, **payload.model_dump())
            db.add(translation)
        else:
            for field, value in payload.model_dump().items():
                setattr(translation, field, value)

        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save translation") from exc

    db.refresh(translation)
    return translation
