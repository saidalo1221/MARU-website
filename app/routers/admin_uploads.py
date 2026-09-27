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


@router.post("/image")
async def upload_image(
    file: UploadFile,
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER)),
) -> dict:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported image type")

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image too large (max 5MB)")

    extension = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}[
        file.content_type
    ]
    filename = f"{uuid.uuid4().hex}{extension}"
    (UPLOAD_DIR / filename).write_bytes(contents)

    return {"url": f"{settings.BACKEND_URL.rstrip('/')}/static/uploads/{filename}"}
