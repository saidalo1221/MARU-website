from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.core.rate_limit import rate_limit
from app.database import get_db
from app.dependencies import get_current_user_required
from app.models import SKU, Inventory
from app.models.product_variant import ProductVariant
from app.models.user import User
from app.models.wishlist_item import WishlistItem
from app.schemas.extras import WishlistItemOut
from app.services.analytics import record_event
from app.services.currency import CurrencyError, convert_amount
from app.services.i18n import get_product_translations

router = APIRouter(prefix="/wishlist", tags=["wishlist"], dependencies=[Depends(rate_limit("wishlist", 120, 60))])


def _to_out(item: WishlistItem, translation, currency: str | None, db: Session) -> WishlistItemOut:
    sku = item.sku
    product = sku.variant.product
    available = sku.available_quantity
    price = sku.retail_price
    out_currency = sku.currency
    if currency and currency != sku.currency:
        price = convert_amount(db, price, sku.currency, currency)
        out_currency = currency
    return WishlistItemOut(
        sku_id=sku.id,
        sku_code=sku.sku_code,
        product_name=translation.name if translation is not None else product.name,
        product_slug=product.slug,
        price=price,
        currency=out_currency,
        available=available,
        in_stock=available > 0,
    )


def _list(db: Session, user: User, lang: str | None, currency: str | None) -> list[WishlistItemOut]:
    stmt = (
        select(WishlistItem)
        .where(WishlistItem.user_id == user.id)
        .options(
            joinedload(WishlistItem.sku).joinedload(SKU.inventories).joinedload(Inventory.warehouse),
            joinedload(WishlistItem.sku).joinedload(SKU.variant).joinedload(ProductVariant.product),
        )
        .order_by(WishlistItem.id.desc())
    )
    items = list(db.execute(stmt).unique().scalars().all())

    translations = {}
    if lang:
        product_ids = [i.sku.variant.product.id for i in items]
        translations = get_product_translations(db, product_ids, lang)

    try:
        return [
            _to_out(i, translations.get(i.sku.variant.product.id), currency, db)
            for i in items
        ]
    except CurrencyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/", response_model=list[WishlistItemOut])
def get_wishlist(
    lang: str | None = None,
    currency: str | None = None,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
    """Pass ?lang=ru|uz|en and/or ?currency=UZS|EUR|KZT|AED to match the
    catalog's display locale/currency (PRD section 14/15)."""
    return _list(db, user, lang, currency)


@router.post("/{sku_id}", response_model=list[WishlistItemOut], status_code=status.HTTP_201_CREATED)
def add_to_wishlist(
    sku_id: int,
    lang: str | None = None,
    currency: str | None = None,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
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
    return _list(db, user, lang, currency)


@router.delete("/{sku_id}", response_model=list[WishlistItemOut])
def remove_from_wishlist(
    sku_id: int,
    lang: str | None = None,
    currency: str | None = None,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
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
    return _list(db, user, lang, currency)
