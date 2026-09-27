from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models import Category, Product
from app.models.category_translation import CategoryTranslation
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryOut, CategoryTranslationIn, CategoryTranslationOut, CategoryUpdate

router = APIRouter(prefix="/admin/categories", tags=["admin-categories"])


@router.post("/", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER)),
    db: Session = Depends(get_db),
) -> Category:
    if payload.parent_id is not None and db.get(Category, payload.parent_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parent category not found")

    category = Category(**payload.model_dump())
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


@router.patch("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER)),
    db: Session = Depends(get_db),
) -> Category:
    data = payload.model_dump(exclude_unset=True)

    if data.get("parent_id") is not None:
        if data["parent_id"] == category_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category cannot be its own parent")
        if db.get(Category, data["parent_id"]) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parent category not found")

    try:
        category = db.get(Category, category_id)
        if category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

        for field, value in data.items():
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


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER)),
    db: Session = Depends(get_db),
) -> None:
    try:
        category = db.get(Category, category_id)
        if category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

        has_children = db.execute(
            select(Category.id).where(Category.parent_id == category_id).limit(1)
        ).scalar_one_or_none()
        if has_children is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category has child categories")

        has_products = db.execute(
            select(Product.id).where(Product.category_id == category_id).limit(1)
        ).scalar_one_or_none()
        if has_products is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category has products")

        db.delete(category)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete category") from exc


@router.put("/{category_id}/translations/{locale}", response_model=CategoryTranslationOut)
def upsert_category_translation(
    category_id: int,
    locale: Literal["ru", "uz", "en"],
    payload: CategoryTranslationIn,
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER)),
    db: Session = Depends(get_db),
) -> CategoryTranslation:
    if db.get(Category, category_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    try:
        translation = db.execute(
            select(CategoryTranslation).where(
                CategoryTranslation.category_id == category_id, CategoryTranslation.locale == locale
            )
        ).scalar_one_or_none()

        if translation is None:
            translation = CategoryTranslation(category_id=category_id, locale=locale, name=payload.name)
            db.add(translation)
        else:
            translation.name = payload.name

        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save translation") from exc

    db.refresh(translation)
    return translation
