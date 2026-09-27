from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.audit import log_audit
from app.dependencies import require_role
from app.models import SKU
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.product import SKUOut, SKUUpdate

router = APIRouter(prefix="/admin/skus", tags=["admin-skus"])


@router.patch("/{sku_id}", response_model=SKUOut)
def update_sku(
    sku_id: int,
    payload: SKUUpdate,
    user: User = Depends(require_role(UserRole.PRODUCT_MANAGER)),
    db: Session = Depends(get_db),
) -> SKU:
    try:
        sku = db.get(SKU, sku_id)
        if sku is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SKU not found")

        changes = payload.model_dump(exclude_unset=True)
        log_audit(
            db, user, "sku_update", "sku", sku.id,
            {f: getattr(sku, f) for f in changes}, changes,
        )
        for field, value in changes.items():
            setattr(sku, field, value)

        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Barcode already exists") from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update SKU") from exc

    db.refresh(sku)
    return sku
