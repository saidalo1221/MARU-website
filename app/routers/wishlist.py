from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user_required
from app.models import SKU, Inventory
from app.models.product_variant import ProductVariant
from app.models.user import User
from app.models.wishlist_item import WishlistItem
from app.schemas.extras import WishlistItemOut
from app.services.analytics import record_event

router = APIRouter(prefix="/wishlist", tags=["wishlist"])


def _to_out(item: WishlistItem) -> WishlistItemOut:
    sku = item.sku
    product = sku.variant.product
    available = sku.available_quantity
    return WishlistItemOut(
        sku_id=sku.id,
        sku_code=sku.sku_code,
        product_name=product.name,
        product_slug=product.slug,
        price=sku.retail_price,
        currency=sku.currency,
        available=available,
        in_stock=available > 0,
    )


def _list(db: Session, user: User) -> list[WishlistItemOut]:
    stmt = (
        select(WishlistItem)
        .where(WishlistItem.user_id == user.id)
        .options(
            joinedload(WishlistItem.sku).joinedload(SKU.inventories).joinedload(Inventory.warehouse),
            joinedload(WishlistItem.sku).joinedload(SKU.variant).joinedload(ProductVariant.product),
        )
        .order_by(WishlistItem.id.desc())
    )
    return [_to_out(i) for i in db.execute(stmt).unique().scalars().all()]


@router.get("/", response_model=list[WishlistItemOut])
def get_wishlist(user: User = Depends(get_current_user_required), db: Session = Depends(get_db)):
    return _list(db, user)


@router.post("/{sku_id}", response_model=list[WishlistItemOut], status_code=status.HTTP_201_CREATED)
def add_to_wishlist(sku_id: int, user: User = Depends(get_current_user_required), db: Session = Depends(get_db)):
    sku = db.get(SKU, sku_id)
    if sku is None or not sku.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SKU not found or inactive")
    try:
        db.add(WishlistItem(user_id=user.id, sku_id=sku_id))
        db.commit()
    except IntegrityError:
        db.rollback()  # already in wishlist: idempotent
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update wishlist") from exc
    record_event(db, "add_to_wishlist", user=user, sku_id=sku_id)
    return _list(db, user)


@router.delete("/{sku_id}", response_model=list[WishlistItemOut])
def remove_from_wishlist(sku_id: int, user: User = Depends(get_current_user_required), db: Session = Depends(get_db)):
    try:
        item = db.execute(
            select(WishlistItem).where(WishlistItem.user_id == user.id, WishlistItem.sku_id == sku_id)
        ).scalar_one_or_none()
        if item is not None:
            db.delete(item)
            db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update wishlist") from exc
    return _list(db, user)
