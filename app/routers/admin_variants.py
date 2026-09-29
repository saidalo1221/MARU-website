from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models import Inventory, ProductVariant, SKU, VariantImage, Warehouse
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.product import (
    ProductVariantOut,
    ProductVariantUpdate,
    SKUCreate,
    SKUOut,
    VariantImageCreate,
    VariantImageOut,
    VariantImageReorder,
)

router = APIRouter(prefix="/admin/variants", tags=["admin-variants"])


@router.patch("/{variant_id}", response_model=ProductVariantOut)
def update_variant(
    variant_id: int,
    payload: ProductVariantUpdate,
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER)),
    db: Session = Depends(get_db),
) -> ProductVariant:
    try:
        variant = db.get(ProductVariant, variant_id)
        if variant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(variant, field, value)

        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update variant") from exc

    db.refresh(variant)
    return variant


@router.post("/{variant_id}/skus", response_model=SKUOut, status_code=status.HTTP_201_CREATED)
def create_sku(
    variant_id: int,
    payload: SKUCreate,
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER)),
    db: Session = Depends(get_db),
) -> SKU:
    if db.get(ProductVariant, variant_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")

    # Every sellable SKU needs a stock ledger row (PRD section 19), and since
    # Inventory now belongs to a specific warehouse (PRD ТЗ№3 §28), there must
    # be at least one to create it against.
    default_warehouse = db.execute(
        select(Warehouse).where(Warehouse.is_active.is_(True)).order_by(Warehouse.priority.asc())
    ).scalars().first()
    if default_warehouse is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active warehouse exists yet — create one via /admin/warehouses/ before adding SKUs",
        )

    sku = SKU(variant_id=variant_id, **payload.model_dump())
    db.add(sku)
    try:
        db.flush()
        # admin_inventory assumes this row already exists and 404s on GET/PATCH if it doesn't.
        db.add(Inventory(sku_id=sku.id, warehouse_id=default_warehouse.id))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="SKU code or barcode already exists"
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create SKU") from exc

    db.refresh(sku)
    return sku


@router.post("/{variant_id}/images", response_model=VariantImageOut, status_code=status.HTTP_201_CREATED)
def add_variant_image(
    variant_id: int,
    payload: VariantImageCreate,
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER)),
    db: Session = Depends(get_db),
) -> VariantImage:
    if db.get(ProductVariant, variant_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")

    next_order = db.execute(
        select(func.coalesce(func.max(VariantImage.sort_order), -1)).where(VariantImage.variant_id == variant_id)
    ).scalar_one()

    image = VariantImage(variant_id=variant_id, image_url=payload.image_url, sort_order=next_order + 1)
    db.add(image)
    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to add image") from exc

    db.refresh(image)
    return image


@router.patch("/{variant_id}/images/{image_id}", response_model=VariantImageOut)
def reorder_variant_image(
    variant_id: int,
    image_id: int,
    payload: VariantImageReorder,
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER)),
    db: Session = Depends(get_db),
) -> VariantImage:
    image = db.execute(
        select(VariantImage).where(VariantImage.id == image_id, VariantImage.variant_id == variant_id)
    ).scalar_one_or_none()
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

    image.sort_order = payload.sort_order
    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to reorder image") from exc

    db.refresh(image)
    return image


@router.delete("/{variant_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_variant_image(
    variant_id: int,
    image_id: int,
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER)),
    db: Session = Depends(get_db),
) -> None:
    image = db.execute(
        select(VariantImage).where(VariantImage.id == image_id, VariantImage.variant_id == variant_id)
    ).scalar_one_or_none()
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

    try:
        db.delete(image)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete image") from exc
