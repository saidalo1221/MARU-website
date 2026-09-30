from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, contains_eager

from app.database import get_db
from app.dependencies import require_role
from app.models import Category, Product, ProductVariant
from app.models.enums import UserRole
from app.models.product_translation import ProductTranslation
from app.models.user import User
from app.schemas.product import (
    ProductCreate,
    ProductOut,
    ProductTranslationIn,
    ProductTranslationOut,
    ProductUpdate,
    ProductVariantCreate,
    ProductVariantOut,
)
from app.services.badges import compute_badges, compute_badges_batch

router = APIRouter(prefix="/admin/products", tags=["admin-products"])


def _load_product(db: Session, product_id: int) -> Optional[Product]:
    stmt = (
        select(Product)
        .outerjoin(Product.variants)
        .outerjoin(ProductVariant.skus)
        .where(Product.id == product_id)
        .options(contains_eager(Product.variants).contains_eager(ProductVariant.skus))
    )
    return db.execute(stmt).unique().scalar_one_or_none()


def _to_out(db: Session, product: Product) -> ProductOut:
    out = ProductOut.model_validate(product)
    out.badges = compute_badges(db, product)
    return out


@router.get("/", response_model=list[ProductOut])
def list_products(
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER)),
    db: Session = Depends(get_db),
) -> list[ProductOut]:
    """Admin catalog view: every product regardless of variant/SKU active status
    (unlike the public /products/ route, which only shows sellable ones)."""
    stmt = (
        select(Product)
        .outerjoin(Product.variants)
        .outerjoin(ProductVariant.skus)
        .options(contains_eager(Product.variants).contains_eager(ProductVariant.skus))
        .order_by(Product.id)
    )
    try:
        products = list(db.execute(stmt).unique().scalars().all())
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to fetch products") from exc

    badges = compute_badges_batch(db, products)
    out = [ProductOut.model_validate(p) for p in products]
    for product, product_out in zip(products, out):
        product_out.badges = badges[product.id]
    return out


@router.post("/", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER)),
    db: Session = Depends(get_db),
) -> ProductOut:
    if db.get(Category, payload.category_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found")

    # material is fixed by ck_products_material (PRD section 4: first-stage assortment is PP only).
    product = Product(**payload.model_dump(), material="polypropylene")
    db.add(product)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product slug already exists") from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create product") from exc

    return _to_out(db, _load_product(db, product.id))


@router.get("/{product_id}", response_model=ProductOut)
def get_product(
    product_id: int,
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER)),
    db: Session = Depends(get_db),
) -> ProductOut:
    try:
        product = _load_product(db, product_id)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to fetch product") from exc

    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    return _to_out(db, product)


@router.patch("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER)),
    db: Session = Depends(get_db),
) -> ProductOut:
    data = payload.model_dump(exclude_unset=True)

    if "category_id" in data and db.get(Category, data["category_id"]) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found")

    try:
        product = db.get(Product, product_id)
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        for field, value in data.items():
            setattr(product, field, value)

        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product slug already exists") from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update product") from exc

    return _to_out(db, _load_product(db, product_id))


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER)),
    db: Session = Depends(get_db),
) -> None:
    try:
        product = db.get(Product, product_id)
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        has_variants = db.execute(
            select(ProductVariant.id).where(ProductVariant.product_id == product_id).limit(1)
        ).scalar_one_or_none()
        if has_variants is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Product has variants; deactivate them instead of deleting the product",
            )

        db.delete(product)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete product") from exc


@router.post("/{product_id}/variants", response_model=ProductVariantOut, status_code=status.HTTP_201_CREATED)
def create_variant(
    product_id: int,
    payload: ProductVariantCreate,
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER)),
    db: Session = Depends(get_db),
) -> ProductVariant:
    if db.get(Product, product_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    variant = ProductVariant(product_id=product_id, **payload.model_dump())
    db.add(variant)
    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create variant") from exc

    db.refresh(variant)
    return variant


@router.get("/{product_id}/translations", response_model=list[ProductTranslationOut])
def list_product_translations(
    product_id: int,
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER)),
    db: Session = Depends(get_db),
) -> list[ProductTranslation]:
    if db.get(Product, product_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return list(
        db.execute(select(ProductTranslation).where(ProductTranslation.product_id == product_id)).scalars().all()
    )


@router.put("/{product_id}/translations/{locale}", response_model=ProductTranslationOut)
def upsert_product_translation(
    product_id: int,
    locale: Literal["ru", "uz", "en"],
    payload: ProductTranslationIn,
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER)),
    db: Session = Depends(get_db),
) -> ProductTranslation:
    if db.get(Product, product_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    try:
        translation = db.execute(
            select(ProductTranslation).where(
                ProductTranslation.product_id == product_id, ProductTranslation.locale == locale
            )
        ).scalar_one_or_none()

        if translation is None:
            translation = ProductTranslation(product_id=product_id, locale=locale, **payload.model_dump())
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
