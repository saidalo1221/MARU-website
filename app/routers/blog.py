from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.core.rate_limit import rate_limit
from app.database import get_db
from app.models.blog_category import BlogCategory
from app.models.blog_post import BlogPost
from app.models.blog_post_translation import BlogPostTranslation
from app.schemas.blog import BlogCategoryOut, BlogPostDetail, BlogPostSummary, BlogPostWithRelated
from app.services.i18n import get_blog_post_translation, get_blog_post_translations

router = APIRouter(prefix="/blog", tags=["blog"], dependencies=[Depends(rate_limit("blog", 240, 60))])


def _apply_translation(post: BlogPost, translation) -> dict:
    return {
        "id": post.id,
        "slug": (translation.slug if translation and translation.slug else post.slug),
        "title": translation.title if translation else post.title,
        "excerpt": translation.excerpt if translation else post.excerpt,
        "content": translation.content if translation else post.content,
        "cover_image_url": post.cover_image_url,
        "author_name": post.author_name,
        "published_at": post.published_at,
        "category": post.category,
    }


@router.get("/categories", response_model=list[BlogCategoryOut])
def list_blog_categories(db: Session = Depends(get_db)) -> list[BlogCategory]:
    try:
        return list(db.execute(select(BlogCategory).order_by(BlogCategory.name)).scalars().all())
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to fetch blog categories") from exc


@router.get("/posts", response_model=list[BlogPostSummary])
def list_blog_posts(
    category: Optional[str] = None,
    lang: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[BlogPostSummary]:
    """Published posts only, newest first. Pass ?category=<slug> to filter,
    ?lang=ru|uz|en for translated title/excerpt (PRD section 15)."""
    stmt = (
        select(BlogPost)
        .join(BlogPost.category)
        .where(BlogPost.is_published.is_(True))
        .options(joinedload(BlogPost.category))
        .order_by(BlogPost.published_at.desc())
        .limit(limit)
    )
    if category:
        stmt = stmt.where(BlogCategory.slug == category)

    try:
        posts = db.execute(stmt).unique().scalars().all()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to fetch blog posts") from exc

    translations = get_blog_post_translations(db, [p.id for p in posts], lang) if lang else {}
    return [BlogPostSummary(**_apply_translation(p, translations.get(p.id))) for p in posts]


@router.get("/posts/{slug}", response_model=BlogPostWithRelated)
def get_blog_post(slug: str, lang: Optional[str] = None, db: Session = Depends(get_db)) -> BlogPostWithRelated:
    stmt = (
        select(BlogPost)
        .where(BlogPost.slug == slug, BlogPost.is_published.is_(True))
        .options(joinedload(BlogPost.category))
    )
    try:
        post = db.execute(stmt).unique().scalar_one_or_none()
        # Not the base (default-language) slug — try a per-locale translated
        # slug instead, so a post linked with its Russian/Uzbek slug still
        # resolves regardless of which locale is currently selected.
        if post is None:
            translated_slug_post_id = db.execute(
                select(BlogPostTranslation.post_id).where(BlogPostTranslation.slug == slug)
            ).scalar_one_or_none()
            if translated_slug_post_id is not None:
                post = db.execute(
                    select(BlogPost)
                    .where(BlogPost.id == translated_slug_post_id, BlogPost.is_published.is_(True))
                    .options(joinedload(BlogPost.category))
                ).unique().scalar_one_or_none()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to fetch blog post") from exc

    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    translation = get_blog_post_translation(db, post.id, lang) if lang else None
    detail = BlogPostDetail(**_apply_translation(post, translation))

    # Related Articles (PRD section 40): other published posts in the same
    # category, most recent first, excluding this one.
    related_stmt = (
        select(BlogPost)
        .where(BlogPost.category_id == post.category_id, BlogPost.is_published.is_(True), BlogPost.id != post.id)
        .options(joinedload(BlogPost.category))
        .order_by(BlogPost.published_at.desc())
        .limit(3)
    )
    related_posts = db.execute(related_stmt).unique().scalars().all()
    related_translations = get_blog_post_translations(db, [p.id for p in related_posts], lang) if lang else {}
    related = [BlogPostSummary(**_apply_translation(p, related_translations.get(p.id))) for p in related_posts]

    return BlogPostWithRelated(post=detail, related=related)
