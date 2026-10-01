import io
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.config import settings
from app.dependencies import require_role
from app.models.enums import UserRole
from app.models.user import User

router = APIRouter(prefix="/admin/uploads", tags=["admin-uploads"])

# Local disk storage — the project has no S3-compatible object storage
# provisioned yet (see TODO.md's invoice/document note), so this is the
# simplest thing that actually works today. On UzCloud this directory needs
# to sit on a persistent volume, not ephemeral container storage, or
# uploaded images will vanish on redeploy.
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024

ALLOWED_VIDEO_TYPES = {"video/mp4": ".mp4", "video/webm": ".webm"}
MAX_VIDEO_BYTES = 25 * 1024 * 1024


VARIANT_WIDTHS = (320, 800, 1600)
logger = logging.getLogger("maru.uploads")


def _write_variants(contents: bytes, base: str) -> None:
    """WebP copies at 320/800/1600 px wide (PRD ТЗ№3 §86), saved as `<base>-<width>.webp` next to the
    original. Never enlarges; a failure only means the page falls back to the original file."""
    try:
        from PIL import Image, ImageOps

        with Image.open(io.BytesIO(contents)) as src:
            src = ImageOps.exif_transpose(src)
            src = src.convert("RGBA" if "A" in src.getbands() else "RGB")
            for width in VARIANT_WIDTHS:
                copy = src.copy()
                copy.thumbnail((width, 10_000))
                copy.save(UPLOAD_DIR / f"{base}-{width}.webp", "WEBP", quality=82)
    except Exception:  # noqa: BLE001 - Pillow missing or an odd file: keep the original only
        logger.warning("Could not create image variants for %s", base, exc_info=True)


def _matches_signature(content_type: str, data: bytes) -> bool:
    """True if the leading bytes look like the declared type. The browser-sent
    Content-Type is attacker-controlled, so it alone must not decide what gets
    stored under /static."""
    if content_type == "image/jpeg":
        return data.startswith(b"\xff\xd8\xff")
    if content_type == "image/png":
        return data.startswith(b"\x89PNG\r\n\x1a\n")
    if content_type == "image/gif":
        return data.startswith((b"GIF87a", b"GIF89a"))
    if content_type == "image/webp":
        return data[:4] == b"RIFF" and data[8:12] == b"WEBP"
    if content_type == "video/mp4":
        return data[4:8] == b"ftyp"
    if content_type == "video/webm":
        return data.startswith(b"\x1a\x45\xdf\xa3")
    return False


@router.post("/image")
async def upload_image(
    file: UploadFile,
    # Shared by product photos and blog cover images — not just Product Manager.
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER, UserRole.MARKETING_MANAGER)),
) -> dict:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported image type")

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image too large (max 5MB)")
    if not _matches_signature(file.content_type, contents):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File content does not match its image type")

    extension = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}[
        file.content_type
    ]
    # The `img-` prefix marks files that have -320/-800/-1600 WebP variants (see frontend lib/images.js).
    base = f"img-{uuid.uuid4().hex}"
    filename = f"{base}{extension}"
    (UPLOAD_DIR / filename).write_bytes(contents)
    if file.content_type != "image/gif":
        _write_variants(contents, base)

    return {"url": f"{settings.BACKEND_URL.rstrip('/')}/static/uploads/{filename}"}


@router.post("/video")
async def upload_video(
    file: UploadFile,
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER, UserRole.MARKETING_MANAGER)),
) -> dict:
    """Product-gallery videos. The gallery tells images from videos by file
    extension, so only mp4/webm (playable in every browser) are accepted."""
    extension = ALLOWED_VIDEO_TYPES.get(file.content_type)
    if extension is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported video type (mp4 or webm only)")

    contents = await file.read(MAX_VIDEO_BYTES + 1)
    if len(contents) > MAX_VIDEO_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Video too large (max 25MB)")
    if not _matches_signature(file.content_type, contents):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File content does not match its video type")

    filename = f"{uuid.uuid4().hex}{extension}"
    (UPLOAD_DIR / filename).write_bytes(contents)

    return {"url": f"{settings.BACKEND_URL.rstrip('/')}/static/uploads/{filename}"}
