from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

from app.routers import (
    admin_analytics_events,
    admin_audit,
    admin_categories,
    admin_exchange_rates,
    admin_integration_logs,
    admin_inventory,
    admin_notification_templates,
    admin_orders,
    admin_products,
    admin_promo_codes,
    admin_quotes,
    admin_reviews,
    admin_shipping_rates,
    admin_skus,
    admin_tax_rules,
    admin_variants,
    admin_warehouses,
    addresses,
    auth,
    cart,
    categories,
    exchange_rates,
    orders,
    payment_webhooks,
    products,
    quotes,
    reviews,
    shipping,
    wishlist,
)

app = FastAPI(title="MARU")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    # Guest carts return this header when a cart is first created; JavaScript
    # must be able to read it to persist the cart across requests.
    expose_headers=["X-Cart-Token"],
)

# PRD ТЗ№3 §15/§43: base API version is /api/v1. All routers are mounted
# under one versioned router rather than repeating prefix="/api/v1" on every
# include_router() call below; bump to /api/v2 the same way for a future
# breaking change, per §101's deprecation-not-immediate-removal policy.
api_v1 = APIRouter(prefix="/api/v1")

api_v1.include_router(admin_analytics_events.router)
api_v1.include_router(admin_audit.router)
api_v1.include_router(admin_categories.router)
api_v1.include_router(admin_exchange_rates.router)
api_v1.include_router(admin_integration_logs.router)
api_v1.include_router(admin_inventory.router)
api_v1.include_router(admin_notification_templates.router)
api_v1.include_router(admin_orders.router)
api_v1.include_router(admin_products.router)
api_v1.include_router(admin_promo_codes.router)
api_v1.include_router(admin_quotes.router)
api_v1.include_router(admin_reviews.router)
api_v1.include_router(admin_shipping_rates.router)
api_v1.include_router(admin_skus.router)
api_v1.include_router(admin_tax_rules.router)
api_v1.include_router(admin_variants.router)
api_v1.include_router(admin_warehouses.router)
api_v1.include_router(addresses.router)
api_v1.include_router(auth.router)
api_v1.include_router(cart.router)
api_v1.include_router(categories.router)
api_v1.include_router(exchange_rates.router)
api_v1.include_router(orders.router)
api_v1.include_router(payment_webhooks.router)
api_v1.include_router(products.router)
api_v1.include_router(quotes.router)
api_v1.include_router(reviews.router)
api_v1.include_router(shipping.router)
api_v1.include_router(wishlist.router)

app.include_router(api_v1)
