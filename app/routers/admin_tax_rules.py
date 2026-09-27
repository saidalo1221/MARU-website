from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.enums import UserRole
from app.models.tax_rule import TaxRule
from app.models.user import User
from app.schemas.tax import TaxRuleCreate, TaxRuleOut, TaxRuleUpdate

# PRD ТЗ№3 §41 doesn't assign tax configuration to a specific role; gated to
# Accountant, the closest RBAC fit (PRD §57's role list).
router = APIRouter(prefix="/admin/tax-rules", tags=["admin-tax-rules"])


@router.get("/", response_model=list[TaxRuleOut])
def list_tax_rules(
    user: User = Depends(require_role(UserRole.ACCOUNTANT)),
    db: Session = Depends(get_db),
) -> list[TaxRule]:
    try:
        rules = db.execute(select(TaxRule).order_by(TaxRule.id)).scalars().all()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to fetch tax rules") from exc
    return list(rules)


@router.post("/", response_model=TaxRuleOut, status_code=status.HTTP_201_CREATED)
def create_tax_rule(
    payload: TaxRuleCreate,
    user: User = Depends(require_role(UserRole.ACCOUNTANT)),
    db: Session = Depends(get_db),
) -> TaxRule:
    rule = TaxRule(**payload.model_dump())
    db.add(rule)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A tax rule for this country/customer type/tax type already exists",
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create tax rule") from exc
    db.refresh(rule)
    return rule


@router.patch("/{rule_id}", response_model=TaxRuleOut)
def update_tax_rule(
    rule_id: int,
    payload: TaxRuleUpdate,
    user: User = Depends(require_role(UserRole.ACCOUNTANT)),
    db: Session = Depends(get_db),
) -> TaxRule:
    try:
        rule = db.get(TaxRule, rule_id)
        if rule is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tax rule not found")

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(rule, field, value)

        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update tax rule") from exc

    db.refresh(rule)
    return rule
