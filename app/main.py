from html import escape

from fastapi import APIRouter, Depends, FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.core.logging_config import configure_logging, init_error_tracking
from app.core.request_id import install_log_record_factory, new_request_id, request_id_var
from app.database import get_db
from app.models.blog_post import BlogPost
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.sku import SKU

from app.routers import (
    about_sections,
    admin_about_sections,
    admin_analytics_events,
    admin_audit,
    admin_blog,
    admin_categories,
    admin_exchange_rates,
    admin_integration_logs,
    admin_inventory,
    admin_newsletter,
    admin_notification_templates,
    admin_orders,
    admin_page_sections,
    admin_products,
    admin_promo_codes,
    admin_quotes,
    admin_reviews,
    admin_shipping_rates,
    admin_site_settings,
    admin_skus,
    admin_tax_rules,
    admin_uploads,
    admin_users,
    admin_variants,
    admin_warehouses,
    addresses,
    analytics,
    auth,
    blog,
    cart,
    categories,
    exchange_rates,
    newsletter,
    orders,
    page_sections,
    payment_webhooks,
    privacy,
    products,
    quotes,
    reviews,
    shipping,
    site_settings,
    stock_alerts,
    wishlist,
)

app = FastAPI(
    title="MARU",
    docs_url="/docs" if settings.ENABLE_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_DOCS else None,
    openapi_url="/openapi.json" if settings.ENABLE_DOCS else None,
)

_DOCS_PATHS = ("/docs", "/redoc", "/openapi.json")

install_log_record_factory()
# uvicorn only configures its own loggers; this gives the app's `maru.*` loggers
# a handler (text or JSON, see app/core/logging_config.py).
configure_logging()
init_error_tracking()


@app.middleware("http")
async def request_id_middleware(request, call_next):
    request_id = new_request_id(request.headers.get("X-Request-ID"))
    token = request_id_var.set(request_id)
    try:
        response = await call_next(request)
    finally:
        request_id_var.reset(token)
    response.headers["X-Request-ID"] = request_id
    return response


@app.middleware("http")
async def security_headers(request, call_next):
    """Baseline hardening headers for every API response (PRD ТЗ№3 §102). The
    storefront's static files are served by the reverse proxy, which needs the
    same headers (plus a CSP suited to the React app) — see MARIADB_PREFLIGHT.md."""
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "geolocation=(), camera=(), microphone=()")
    # Ignored by browsers over plain http, so safe to send from a local server.
    response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    if not request.url.path.startswith(_DOCS_PATHS):
        # The API only returns JSON/XML/media; nothing in it should ever run as a page.
        response.headers.setdefault("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    # Guest carts return this header when a cart is first created; JavaScript
    # must be able to read it to persist the cart across requests.
    expose_headers=["X-Cart-Token", "X-Total-Count"],
)

# Serves admin-uploaded images (app/routers/admin_uploads.py); see that
# module's docstring for why this is local disk rather than S3.
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# PRD ТЗ№3 §15/§43: base API version is /api/v1. All routers are mounted
# under one versioned router rather than repeating prefix="/api/v1" on every
# include_router() call below; bump to /api/v2 the same way for a future
# breaking change, per §101's deprecation-not-immediate-removal policy.
api_v1 = APIRouter(prefix="/api/v1")

api_v1.include_router(about_sections.router)
api_v1.include_router(admin_about_sections.router)
api_v1.include_router(admin_analytics_events.router)
api_v1.include_router(admin_audit.router)
api_v1.include_router(admin_blog.router)
api_v1.include_router(admin_categories.router)
api_v1.include_router(admin_exchange_rates.router)
api_v1.include_router(admin_integration_logs.router)
api_v1.include_router(admin_inventory.router)
api_v1.include_router(admin_newsletter.router)
api_v1.include_router(admin_notification_templates.router)
api_v1.include_router(admin_orders.router)
api_v1.include_router(admin_page_sections.router)
api_v1.include_router(admin_products.router)
api_v1.include_router(admin_promo_codes.router)
api_v1.include_router(admin_quotes.router)
api_v1.include_router(admin_reviews.router)
api_v1.include_router(admin_shipping_rates.router)
api_v1.include_router(admin_site_settings.router)
api_v1.include_router(admin_skus.router)
api_v1.include_router(admin_tax_rules.router)
api_v1.include_router(admin_uploads.router)
api_v1.include_router(admin_users.router)
api_v1.include_router(admin_variants.router)
api_v1.include_router(admin_warehouses.router)
api_v1.include_router(addresses.router)
api_v1.include_router(analytics.router)
api_v1.include_router(auth.router)
api_v1.include_router(blog.router)
api_v1.include_router(cart.router)
api_v1.include_router(categories.router)
api_v1.include_router(exchange_rates.router)
api_v1.include_router(newsletter.router)
api_v1.include_router(orders.router)
api_v1.include_router(page_sections.router)
api_v1.include_router(payment_webhooks.router)
api_v1.include_router(privacy.router)
api_v1.include_router(products.router)
api_v1.include_router(quotes.router)
api_v1.include_router(reviews.router)
api_v1.include_router(reviews.featured_router)
api_v1.include_router(shipping.router)
api_v1.include_router(site_settings.router)
api_v1.include_router(stock_alerts.router)
api_v1.include_router(wishlist.router)

app.include_router(api_v1)


@app.get("/sitemap.xml", include_in_schema=False)
def sitemap(db: Session = Depends(get_db)) -> Response:
    """Dynamic XML sitemap for the storefront (frontend, not this API) —
    static pages, every product with a purchasable SKU, and every published
    blog post. Not versioned under /api/v1 since it's meant to be crawled at
    the site root; a production reverse proxy fronting both this backend and
    the frontend build needs to route /sitemap.xml here specifically (it
    can't be a static file — the product/blog list changes)."""
    base = settings.FRONTEND_URL.rstrip("/")
    urls = [base] + [
        f"{base}/{path}"
        for path in (
            "shop",
            "blog",
            "about",
            "contact",
            "delivery",
            "payment",
            "returns",
            "faq",
            "privacy",
            "terms",
            "b2b",
            "wholesale",
            "distributor",
        )
    ]

    product_slugs = db.execute(
        select(Product.slug)
        .join(Product.variants)
        .join(ProductVariant.skus)
        .where(ProductVariant.is_active.is_(True), SKU.is_active.is_(True))
        .distinct()
    ).scalars().all()
    urls += [f"{base}/products/{slug}" for slug in product_slugs]

    post_slugs = db.execute(
        select(BlogPost.slug).where(BlogPost.is_published.is_(True), BlogPost.published_at.isnot(None))
    ).scalars().all()
    urls += [f"{base}/blog/{slug}" for slug in post_slugs]

    body = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    body += [f"<url><loc>{escape(url)}</loc></url>" for url in urls]
    body.append("</urlset>")
    return Response("\n".join(body), media_type="application/xml")
