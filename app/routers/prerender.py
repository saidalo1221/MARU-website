"""Server-rendered HTML for crawlers and link-preview bots (PRD ТЗ№3 §85 "SSR where useful", ТЗ№2 §62).

The storefront is a single-page app: its <title>, description and structured data are written by JavaScript, which
search engines run but many link-preview bots (Telegram, WhatsApp, Facebook, Slack...) do not. The reverse proxy
sends those user agents to /prerender/<same path> (see deploy/nginx.conf.example); this route answers with a small
complete HTML page: title, description, canonical, Open Graph, JSON-LD and the main text. Visitors never see it.
Not part of /api/v1 and not in the OpenAPI schema.
"""

import html
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Category, Product
from app.models.blog_post import BlogPost
from app.routers import products as products_router
from app.services.i18n import get_category_translation_row

router = APIRouter(prefix="/prerender", include_in_schema=False)

DEFAULT_LANG = "ru"
SITE = "MARU"
HOME_TITLE = "MARU - plastic food containers"
HOME_DESCRIPTION = "Plastic food containers made in-house - polypropylene containers from 350 ml to 1900 ml, in stock and ready to ship."


def _e(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _page(title: str, description: str, path: str, body: str, image: Optional[str] = None, kind: str = "website", json_ld: Optional[dict] = None, lang: str = DEFAULT_LANG) -> Response:
    base = settings.FRONTEND_URL.rstrip("/")
    url = f"{base}/{path}".rstrip("/") if path else base
    full_title = f"{title} | {SITE}" if title != HOME_TITLE else title
    ld = f'<script type="application/ld+json">{json.dumps(json_ld, ensure_ascii=False).replace("</", "<\\/")}</script>' if json_ld else ""
    image_tags = f'<meta property="og:image" content="{_e(image)}"><meta name="twitter:image" content="{_e(image)}">' if image else ""
    page = (
        f'<!doctype html><html lang="{_e(lang)}"><head><meta charset="utf-8">'
        f"<title>{_e(full_title)}</title>"
        f'<meta name="description" content="{_e(description)}">'
        f'<link rel="canonical" href="{_e(url)}">'
        f'<meta property="og:site_name" content="{SITE}"><meta property="og:type" content="{_e(kind)}">'
        f'<meta property="og:title" content="{_e(full_title)}"><meta property="og:description" content="{_e(description)}">'
        f'<meta property="og:url" content="{_e(url)}">{image_tags}'
        f'<meta name="twitter:card" content="{"summary_large_image" if image else "summary"}">'
        f"{ld}</head><body>{body}</body></html>"
    )
    return Response(page, media_type="text/html; charset=utf-8", headers={"Cache-Control": "public, max-age=300"})


def _product_page(db: Session, slug: str, lang: str) -> Response:
    product = db.execute(select(Product).where(Product.slug == slug)).scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Not found")
    items = products_router._present(db, [product.id], products_router._sellable_conditions(), lang, None)
    if not items:
        raise HTTPException(status_code=404, detail="Not found")
    p = items[0]
    skus = [s for v in p.variants for s in v.skus]
    prices = [float(s.special_price if s.special_price is not None and s.special_price < s.retail_price else s.retail_price) for s in skus]
    currency = skus[0].currency if skus else "USD"
    in_stock = any(s.available_quantity > 0 for s in skus)
    image = next((i.image_url for v in p.variants for i in v.images), None) or next((v.photo_url for v in p.variants if v.photo_url), None)
    description = p.meta_description or p.description or HOME_DESCRIPTION
    ld = {
        "@context": "https://schema.org", "@type": "Product", "name": p.name, "description": description,
        "sku": skus[0].sku_code if skus else None, "image": image,
        "offers": {
            "@type": "AggregateOffer", "priceCurrency": currency, "lowPrice": min(prices) if prices else None,
            "availability": "https://schema.org/InStock" if in_stock else "https://schema.org/OutOfStock",
        },
    }
    if p.rating_count:
        ld["aggregateRating"] = {"@type": "AggregateRating", "ratingValue": p.rating_average, "reviewCount": p.rating_count}
    specs = "".join(f"<li>{_e(label)}: {_e(value)}</li>" for label, value in (("Volume", f"{p.volume_ml} ml"), ("Material", p.material), ("Shape", p.shape), ("Origin", p.country_of_origin)) if value)
    advantages = "".join(f"<li>{_e(x.strip())}</li>" for x in (p.advantages or "").splitlines() if x.strip())
    body = (
        f"<h1>{_e(p.name)}</h1><p>{_e(p.description)}</p><ul>{specs}</ul>"
        + (f"<h2>Advantages</h2><ul>{advantages}</ul>" if advantages else "")
        + (f"<p>From {min(prices):.2f} {_e(currency)}</p>" if prices else "")
    )
    return _page(p.seo_title or p.name, description, f"products/{p.slug}", body, image, "product", {k: v for k, v in ld.items() if v is not None}, lang)


def _category_page(db: Session, slug: str, lang: str) -> Response:
    category = db.execute(select(Category).where(Category.slug == slug)).scalar_one_or_none()
    if category is None:
        raise HTTPException(status_code=404, detail="Not found")
    tr = get_category_translation_row(db, category.id, lang)
    name = (tr.name if tr is not None and getattr(tr, "name", None) else category.name)
    description = (getattr(tr, "description", None) if tr is not None else None) or category.description or HOME_DESCRIPTION
    seo = (getattr(tr, "seo_content", None) if tr is not None else None) or category.seo_content or ""
    body = f"<h1>{_e(name)}</h1><p>{_e(description)}</p><p>{_e(seo)}</p>"
    return _page(name, description, f"shop/{category.slug}", body, category.image_url, "website", None, lang)


def _blog_page(db: Session, slug: str, lang: str) -> Response:
    post = db.execute(select(BlogPost).where(BlogPost.slug == slug, BlogPost.is_published.is_(True))).scalar_one_or_none()
    if post is None:
        raise HTTPException(status_code=404, detail="Not found")
    description = post.excerpt or post.content[:200]
    ld = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": post.title, "image": post.cover_image_url, "author": {"@type": "Person", "name": post.author_name} if post.author_name else None,
          "datePublished": post.published_at.isoformat() if post.published_at else None}
    body = f"<h1>{_e(post.title)}</h1><p>{_e(post.excerpt)}</p><div>{_e(post.content)}</div>"
    return _page(post.title, description, f"blog/{post.slug}", body, post.cover_image_url, "article", {k: v for k, v in ld.items() if v is not None}, lang)


@router.get("")
@router.get("/")
def prerender_home() -> Response:
    ld = {"@context": "https://schema.org", "@type": "Organization", "name": SITE, "url": settings.FRONTEND_URL}
    return _page(HOME_TITLE, HOME_DESCRIPTION, "", f"<h1>{_e(HOME_TITLE)}</h1><p>{_e(HOME_DESCRIPTION)}</p>", None, "website", ld)


@router.get("/products/{slug}")
def prerender_product(slug: str, lang: str = DEFAULT_LANG, db: Session = Depends(get_db)) -> Response:
    return _product_page(db, slug, lang if lang in ("ru", "uz", "en") else DEFAULT_LANG)


@router.get("/shop/{slug}")
def prerender_category(slug: str, lang: str = DEFAULT_LANG, db: Session = Depends(get_db)) -> Response:
    return _category_page(db, slug, lang if lang in ("ru", "uz", "en") else DEFAULT_LANG)


@router.get("/blog/{slug}")
def prerender_blog(slug: str, lang: str = DEFAULT_LANG, db: Session = Depends(get_db)) -> Response:
    return _blog_page(db, slug, lang if lang in ("ru", "uz", "en") else DEFAULT_LANG)
