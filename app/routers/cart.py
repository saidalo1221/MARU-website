from typing import Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, contains_eager, joinedload, selectinload

from app.core.rate_limit import rate_limit

from app.database import get_db
from app.dependencies import get_current_user_optional, get_current_user_required, get_or_create_cart
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.enums import CustomerType
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.promo_code import PromoCode
from app.models.sku import SKU
from app.models.user import User
from app.schemas.cart import (
    CartCurrencyUpdate,
    CartItemCreate,
    CartItemOut,
    CartItemUpdate,
    CartOut,
    CartRecommendationsOut,
)
from app.routers.products import _apply_translation, _convert_product_prices
from app.services.badges import compute_badges_batch
from app.services.i18n import get_product_translation, get_product_translations
from app.services.order_service import available_stock
from app.services.recommendations import recommended_product_ids
from app.services.currency import CurrencyError, convert_amount, get_rate_to_usd
from app.services.analytics import record_event
from app.services.pricing import PromoCodeError, promo_line_discounts, resolve_unit_price, validate_promo
from app.services.shipping import ShippingError, calculate_shipping, cart_weight_g, free_shipping_progress
from app.services import loyalty, market
from app.services.packaging import packaging_for
from app.services.tax import calculate_lines_tax

router = APIRouter(prefix="/cart", tags=["cart"], dependencies=[Depends(rate_limit("cart", 300, 60))])


def _resolve_customer_type(user: Optional[User]) -> CustomerType:
    return user.customer_type if user is not None else CustomerType.RETAIL


def _line_details(db: Session, item, unit_price: Decimal, currency: str, lang: Optional[str]) -> dict:
    """Display fields for a cart line; never raises for missing optional data."""
    sku = item.sku
    variant = sku.variant
    product = variant.product
    name = product.name
    if lang:
        translation = get_product_translation(db, product.id, lang)
        if translation is not None and translation.name:
            name = translation.name
    images = sorted(variant.images, key=lambda i: i.sort_order) if variant.images else []
    image_url = images[0].image_url if images else variant.photo_url
    list_price = None
    try:
        retail = convert_amount(db, sku.retail_price, sku.currency, currency)
        if unit_price < retail:
            list_price = retail
    except CurrencyError:
        pass
    return {
        "product_name": name,
        "product_slug": product.slug,
        "variant_name": variant.name,
        "image_url": image_url,
        "list_price": list_price,
    }


def _build_cart_out(
    db: Session,
    cart: Cart,
    customer_type: CustomerType,
    promo_code: Optional[str],
    country: Optional[str] = None,
    delivery_method: Optional[str] = None,
    region: Optional[str] = None,
    lang: Optional[str] = None,
    user_id: Optional[int] = None,
    user: Optional[User] = None,
    loyalty_points: int = 0,
    market_country: Optional[str] = None,
) -> CartOut:
    items: list[CartItemOut] = []
    cart_lines: list = []  # (sku, line_total): what promo targeting and per-line tax work on
    subtotal = Decimal("0")
    for item in cart.items:
        try:
            unit_price = resolve_unit_price(db, item.sku, customer_type, item.quantity, cart.currency)
        except CurrencyError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        line_total = unit_price * item.quantity
        subtotal += line_total
        cart_lines.append((item.sku, line_total))
        items.append(
            CartItemOut(
                id=item.id,
                sku_id=item.sku_id,
                sku_code=item.sku.sku_code,
                quantity=item.quantity,
                min_order_quantity=item.sku.variant.product.min_order_quantity or 1,
                unit_price=unit_price,
                line_total=line_total,
                available_in_market=market.is_available(item.sku.variant.product, market_country),
                **_line_details(db, item, unit_price, cart.currency, lang),
            )
        )

    saved_items: list[CartItemOut] = []
    for item in cart.saved_items:
        try:
            saved_price = resolve_unit_price(db, item.sku, customer_type, item.quantity, cart.currency)
        except CurrencyError:
            continue
        saved_items.append(
            CartItemOut(
                id=item.id,
                sku_id=item.sku_id,
                sku_code=item.sku.sku_code,
                quantity=item.quantity,
                unit_price=saved_price,
                line_total=saved_price * item.quantity,
                **_line_details(db, item, saved_price, cart.currency, lang),
            )
        )

    # Promo validity (min order amount, expiry, usage cap) depends on the
    # subtotal, so it can only be checked once item prices are resolved.
    promo: Optional[PromoCode] = None
    if promo_code:
        try:
            promo = validate_promo(
                db, promo_code, subtotal, cart.currency,
                lines=cart_lines, user_id=user_id, country=country,
            )
        except PromoCodeError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    try:
        line_discounts = promo_line_discounts(db, promo, cart_lines, cart.currency)
    except PromoCodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    discount = sum(line_discounts, Decimal("0"))

    loyalty_info = loyalty.summary(db, user, subtotal - discount, cart.currency)
    points_applied = min(max(loyalty_points, 0), loyalty_info["max_points"]) if loyalty_info else 0
    loyalty_discount = Decimal("0.00")
    if points_applied:
        loyalty_discount = min(loyalty.spend_amount(db, points_applied, cart.currency), subtotal - discount)
        shares = loyalty.split(loyalty_discount, [total - line_discounts[i] for i, (_sku, total) in enumerate(cart_lines)])
        line_discounts = [a + b for a, b in zip(line_discounts, shares)]
        discount = sum(line_discounts, Decimal("0"))

    # Destination is usually unknown before checkout, so shipping/tax are only
    # estimated when the caller supplies a country (delivery method too, for shipping).
    tax = Decimal("0")
    if country:
        tax = sum(
            calculate_lines_tax(
                db, country, customer_type.value,
                [(sku.variant.product.tax_class, total - line_discounts[i]) for i, (sku, total) in enumerate(cart_lines)],
                region=region, currency=cart.currency,
            ),
            Decimal("0"),
        )

    delivery = Decimal("0")
    if country and delivery_method:
        try:
            delivery = calculate_shipping(
                db, country, delivery_method, cart_weight_g(cart), subtotal - discount, cart.currency
            )
        except ShippingError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    total = subtotal + delivery + tax - discount
    threshold, remaining = free_shipping_progress(db, country, delivery_method, subtotal - discount, cart.currency)

    return CartOut(
        id=cart.id,
        currency=cart.currency,
        items=items,
        subtotal=subtotal,
        discount=discount,
        tax=tax,
        delivery=delivery,
        total=total,
        item_count=sum(i.quantity for i in cart.items),
        promo_code=promo.code if promo is not None else None,
        free_shipping_threshold=threshold,
        free_shipping_remaining=remaining,
        saved_items=saved_items,
        packaging=packaging_for((i.sku, i.quantity) for i in cart.items).as_dict() if cart.items else None,
        loyalty=loyalty_info,
        unavailable_items=sum(1 for i in items if not i.available_in_market),
        loyalty_points_applied=points_applied,
        loyalty_discount=loyalty_discount,
    )


def _load_cart_with_items(db: Session, cart_id: int) -> Cart:
    stmt = (
        select(Cart)
        .where(Cart.id == cart_id)
        .options(
            joinedload(Cart.items).joinedload(CartItem.sku),
            selectinload(Cart.saved_items).joinedload(CartItem.sku),
        )
    )
    return db.execute(stmt).unique().scalar_one()


@router.get("/", response_model=CartOut)
def get_cart(
    promo_code: Optional[str] = None,
    country: Optional[str] = None,
    delivery_method: Optional[str] = None,
    region: Optional[str] = None,
    lang: Optional[str] = None,
    loyalty_points: int = Query(default=0, ge=0, le=10_000_000),
    market_country: Optional[str] = Query(default=None, max_length=100),
    cart: Cart = Depends(get_or_create_cart),
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> CartOut:
    return _build_cart_out(
        db, _load_cart_with_items(db, cart.id), _resolve_customer_type(user), promo_code, country, delivery_method, region, lang,
        user_id=user.id if user is not None else None, user=user, loyalty_points=loyalty_points,
        market_country=market_country,
    )


@router.get(
    "/recommendations",
    response_model=CartRecommendationsOut,
    dependencies=[Depends(rate_limit("cart_recommendations", 60, 60))],
)
def get_cart_recommendations(
    lang: Optional[str] = None,
    currency: Optional[str] = None,
    limit: int = Query(default=4, ge=1, le=12),
    cart: Cart = Depends(get_or_create_cart),
    db: Session = Depends(get_db),
) -> CartRecommendationsOut:
    """Upsell block shown on the cart page (PRD section 21). Advisory only -
    never blocks checkout, so the frontend treats any failure as "no
    recommendations"."""
    try:
        cart_product_ids = set(
            db.execute(
                select(ProductVariant.product_id)
                .join(SKU, SKU.variant_id == ProductVariant.id)
                .join(CartItem, CartItem.sku_id == SKU.id)
                .where(CartItem.cart_id == cart.id)
            ).scalars()
        )
        candidate_ids, co_count = recommended_product_ids(db, cart_product_ids, limit)
        if not candidate_ids:
            return CartRecommendationsOut(based_on_orders=False, products=[])

        loaded = (
            db.execute(
                select(Product)
                .join(Product.variants)
                .join(ProductVariant.skus)
                .where(
                    Product.id.in_(candidate_ids),
                    ProductVariant.is_active.is_(True),
                    SKU.is_active.is_(True),
                )
                .options(
                    contains_eager(Product.variants)
                    .contains_eager(ProductVariant.skus)
                    .joinedload(SKU.inventories)
                    .joinedload(Inventory.warehouse)
                )
            )
            .unique()
            .scalars()
            .all()
        )
        by_id = {p.id: p for p in loaded}
        badges = compute_badges_batch(db, loaded)
        products = [
            by_id[pid] for pid in candidate_ids if pid in by_id and not badges[pid].is_out_of_stock
        ][:limit]

        translations = get_product_translations(db, [p.id for p in products], lang) if lang else {}
        out = [_apply_translation(p, translations.get(p.id)) for p in products]
        for product, product_out in zip(products, out):
            product_out.badges = badges[product.id]
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to load recommendations") from exc

    if currency:
        try:
            for product_out in out:
                _convert_product_prices(db, product_out, currency)
        except CurrencyError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    # Co-purchase results are ranked first, so "bought together" is only
    # honest when the top surviving result (after stock filtering) is one.
    based_on_orders = bool(products) and products[0].id in set(candidate_ids[:co_count])
    return CartRecommendationsOut(based_on_orders=based_on_orders, products=out)


@router.post("/items", response_model=CartOut, status_code=status.HTTP_201_CREATED)
def add_item(
    payload: CartItemCreate,
    cart: Cart = Depends(get_or_create_cart),
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> CartOut:
    try:
        sku = db.get(SKU, payload.sku_id)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to look up SKU") from exc

    if sku is None or not sku.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SKU not found or inactive")

    try:
        existing = db.execute(
            select(CartItem).where(CartItem.cart_id == cart.id, CartItem.sku_id == sku.id)
        ).scalar_one_or_none()

        new_quantity = payload.quantity + (existing.quantity if existing is not None else 0)
        if new_quantity > available_stock(db, sku.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="INSUFFICIENT_STOCK: requested quantity exceeds available stock"
            )

        if existing is not None:
            existing.quantity += payload.quantity
            existing.saved_for_later = False
        else:
            db.add(CartItem(cart_id=cart.id, sku_id=sku.id, quantity=payload.quantity))

        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to add item to cart") from exc

    record_event(db, "add_to_cart", user=user, session_id=cart.token, sku_id=sku.id, quantity=payload.quantity)
    return _build_cart_out(db, _load_cart_with_items(db, cart.id), _resolve_customer_type(user), None)


@router.patch("/items/{sku_id}", response_model=CartOut)
def update_item(
    sku_id: int,
    payload: CartItemUpdate,
    cart: Cart = Depends(get_or_create_cart),
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> CartOut:
    try:
        item = db.execute(
            select(CartItem).where(CartItem.cart_id == cart.id, CartItem.sku_id == sku_id)
        ).scalar_one_or_none()

        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not in cart")

        if payload.quantity > available_stock(db, sku_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="INSUFFICIENT_STOCK: requested quantity exceeds available stock"
            )

        item.quantity = payload.quantity
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update cart item") from exc

    return _build_cart_out(db, _load_cart_with_items(db, cart.id), _resolve_customer_type(user), None)


@router.post("/items/{sku_id}/save-for-later", response_model=CartOut)
def save_item_for_later(
    sku_id: int,
    cart: Cart = Depends(get_or_create_cart),
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> CartOut:
    return _set_saved(db, cart, user, sku_id, saved=True)


@router.post("/items/{sku_id}/move-to-cart", response_model=CartOut)
def move_saved_item_to_cart(
    sku_id: int,
    cart: Cart = Depends(get_or_create_cart),
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> CartOut:
    return _set_saved(db, cart, user, sku_id, saved=False)


def _set_saved(db: Session, cart: Cart, user: Optional[User], sku_id: int, saved: bool) -> CartOut:
    try:
        item = db.execute(
            select(CartItem).where(CartItem.cart_id == cart.id, CartItem.sku_id == sku_id)
        ).scalar_one_or_none()
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not in cart")
        if not saved and item.saved_for_later and item.quantity > available_stock(db, sku_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="INSUFFICIENT_STOCK: requested quantity exceeds available stock"
            )
        item.saved_for_later = saved
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update cart") from exc
    return _build_cart_out(db, _load_cart_with_items(db, cart.id), _resolve_customer_type(user), None)


@router.delete("/items/{sku_id}", response_model=CartOut)
def remove_item(
    sku_id: int,
    cart: Cart = Depends(get_or_create_cart),
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> CartOut:
    try:
        item = db.execute(
            select(CartItem).where(CartItem.cart_id == cart.id, CartItem.sku_id == sku_id)
        ).scalar_one_or_none()

        if item is not None:
            db.delete(item)
            db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to remove cart item") from exc

    if item is not None:
        record_event(db, "remove_from_cart", user=user, session_id=cart.token, sku_id=sku_id)
    return _build_cart_out(db, _load_cart_with_items(db, cart.id), _resolve_customer_type(user), None)


@router.patch("/currency", response_model=CartOut)
def set_cart_currency(
    payload: CartCurrencyUpdate,
    cart: Cart = Depends(get_or_create_cart),
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> CartOut:
    """Lets the customer pick a display/checkout currency (PRD section 14).
    Persisted on the cart so it carries through to the order at checkout."""
    currency = payload.currency.upper()
    if currency != "USD":
        try:
            get_rate_to_usd(db, currency)
        except CurrencyError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    try:
        cart.currency = currency
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update cart currency") from exc

    return _build_cart_out(db, _load_cart_with_items(db, cart.id), _resolve_customer_type(user), None)


@router.post("/merge", response_model=CartOut)
def merge_guest_cart(
    x_cart_token: Optional[str] = Header(default=None, alias="X-Cart-Token"),
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
) -> CartOut:
    """Called right after login/register with the pre-login X-Cart-Token so
    a guest's cart isn't lost (PRD section 10). Idempotent and safe to call
    defensively even with no guest cart present."""
    try:
        user_cart = db.execute(
            select(Cart).where(Cart.user_id == user.id, Cart.is_active.is_(True))
        ).scalar_one_or_none()

        guest_cart = None
        if x_cart_token:
            guest_cart = db.execute(
                select(Cart).where(
                    Cart.token == x_cart_token, Cart.is_active.is_(True), Cart.user_id.is_(None)
                )
            ).scalar_one_or_none()

        if guest_cart is None:
            if user_cart is None:
                user_cart = Cart(user_id=user.id)
                db.add(user_cart)
                db.commit()
                db.refresh(user_cart)
        elif user_cart is None:
            guest_cart.user_id = user.id
            db.commit()
            user_cart = guest_cart
        else:
            guest_items = db.execute(select(CartItem).where(CartItem.cart_id == guest_cart.id)).scalars().all()
            for guest_item in guest_items:
                existing = db.execute(
                    select(CartItem).where(
                        CartItem.cart_id == user_cart.id, CartItem.sku_id == guest_item.sku_id
                    )
                ).scalar_one_or_none()
                if existing is not None:
                    if not guest_item.saved_for_later:
                        existing.quantity += guest_item.quantity
                        existing.saved_for_later = False
                else:
                    db.add(
                        CartItem(
                            cart_id=user_cart.id,
                            sku_id=guest_item.sku_id,
                            quantity=guest_item.quantity,
                            saved_for_later=guest_item.saved_for_later,
                        )
                    )

            guest_cart.is_active = False
            db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to merge cart") from exc

    return _build_cart_out(db, _load_cart_with_items(db, user_cart.id), _resolve_customer_type(user), None)
