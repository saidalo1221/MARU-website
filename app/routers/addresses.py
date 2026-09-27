from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user_required
from app.models.address import Address
from app.models.user import User
from app.schemas.extras import AddressIn, AddressOut

router = APIRouter(prefix="/addresses", tags=["addresses"])


def _own(db: Session, user: User, address_id: int) -> Address:
    address = db.get(Address, address_id)
    if address is None or address.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")
    return address


def _clear_default(db: Session, user: User) -> None:
    db.execute(update(Address).where(Address.user_id == user.id).values(is_default=False))


@router.get("/", response_model=list[AddressOut])
def list_addresses(user: User = Depends(get_current_user_required), db: Session = Depends(get_db)):
    return list(db.execute(select(Address).where(Address.user_id == user.id).order_by(Address.id)).scalars().all())


@router.post("/", response_model=AddressOut, status_code=status.HTTP_201_CREATED)
def create_address(payload: AddressIn, user: User = Depends(get_current_user_required), db: Session = Depends(get_db)):
    try:
        if payload.is_default:
            _clear_default(db, user)
        address = Address(**payload.model_dump(), user_id=user.id)
        db.add(address)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save address") from exc
    db.refresh(address)
    return address


@router.put("/{address_id}", response_model=AddressOut)
def update_address(
    address_id: int, payload: AddressIn, user: User = Depends(get_current_user_required), db: Session = Depends(get_db)
):
    address = _own(db, user, address_id)
    try:
        if payload.is_default:
            _clear_default(db, user)
        for field, value in payload.model_dump().items():
            setattr(address, field, value)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save address") from exc
    db.refresh(address)
    return address


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(address_id: int, user: User = Depends(get_current_user_required), db: Session = Depends(get_db)):
    address = _own(db, user, address_id)
    try:
        db.delete(address)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete address") from exc
