import hashlib
from datetime import datetime, timedelta, timezone
from secrets import randbelow, token_urlsafe

import pyotp
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.core.rate_limit import rate_limit
from app.database import get_db
from app.dependencies import get_current_user_required
from app.models.admin_login_code import AdminLoginCode
from app.models.email_verification_token import EmailVerificationToken
from app.models.enums import UserRole
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.schemas.extras import ForgotPasswordRequest, ResetPasswordRequest, VerifyEmailRequest
from app.services.analytics import record_event
from app.services.notifications.email import EmailNotifier
from app.schemas.user import (
    AdminLoginRequest,
    AdminVerifyRequest,
    MfaCodeRequest,
    MfaSetupOut,
    Token,
    UserCreate,
    UserLogin,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])
email_notifier = EmailNotifier()


def _issue_email_verification(db: Session, user: User) -> None:
    token = token_urlsafe(32)
    db.add(
        EmailVerificationToken(
            user_id=user.id,
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=24),
        )
    )
    db.commit()
    email_notifier.email_verification(user.email, token, db=db)


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("register", 10, 3600))],
)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> Token:
    try:
        existing = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to check existing account") from exc

    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        phone=payload.phone,
        customer_type=payload.customer_type,
    )
    db.add(user)
    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create account") from exc

    db.refresh(user)
    _issue_email_verification(db, user)
    record_event(db, "sign_up", user=user)
    return Token(access_token=create_access_token(str(user.id)))


@router.post("/login", response_model=Token, dependencies=[Depends(rate_limit("login", 10, 60))])
def login(payload: UserLogin, db: Session = Depends(get_db)) -> Token:
    try:
        user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to authenticate") from exc

    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if user.mfa_enabled:
        if not payload.mfa_code or not pyotp.TOTP(user.mfa_secret).verify(payload.mfa_code, valid_window=1):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing MFA code")

    record_event(db, "login", user=user)
    return Token(access_token=create_access_token(str(user.id)))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user_required)) -> User:
    return user


@router.post("/forgot-password", dependencies=[Depends(rate_limit("forgot", 5, 3600))])
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)) -> dict:
    """Always answers the same way so it can't be used to discover which emails have accounts."""
    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if user is not None and user.is_active:
        token = token_urlsafe(32)
        db.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=hashlib.sha256(token.encode()).hexdigest(),
                expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1),
            )
        )
        try:
            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to start password reset") from exc
        email_notifier.password_reset(user.email, token, db=db)
    return {"detail": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password", dependencies=[Depends(rate_limit("reset", 10, 3600))])
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> dict:
    token_hash = hashlib.sha256(payload.token.encode()).hexdigest()
    record = db.execute(select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)).scalar_one_or_none()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if record is None or record.used_at is not None or record.expires_at < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    user = db.get(User, record.user_id)
    try:
        user.password_hash = hash_password(payload.new_password)
        record.used_at = now
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to reset password") from exc
    return {"detail": "Password updated"}


@router.post("/verify-email")
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)) -> dict:
    token_hash = hashlib.sha256(payload.token.encode()).hexdigest()
    record = db.execute(
        select(EmailVerificationToken).where(EmailVerificationToken.token_hash == token_hash)
    ).scalar_one_or_none()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if record is None or record.used_at is not None or record.expires_at < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification token")

    user = db.get(User, record.user_id)
    try:
        user.email_verified = True
        record.used_at = now
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to verify email") from exc
    return {"detail": "Email verified"}


@router.post(
    "/resend-verification",
    dependencies=[Depends(rate_limit("resend_verification", 5, 3600))],
)
def resend_verification(user: User = Depends(get_current_user_required), db: Session = Depends(get_db)) -> dict:
    if user.email_verified:
        return {"detail": "Email already verified"}
    try:
        _issue_email_verification(db, user)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to resend verification email") from exc
    return {"detail": "Verification email sent"}


# --- Admin panel 2-step email login ---------------------------------------
#
# Separate from the opt-in TOTP MFA below: every non-customer account must
# complete this to use the admin panel at all (enforced in require_role(),
# not here) — /auth/login alone is not sufficient. Step 1 checks the
# password and emails a 6-digit code; step 2 checks the code and issues the
# normal access token, additionally marking the account admin-verified for
# ADMIN_MFA_VALID_HOURS.

ADMIN_MFA_CODE_TTL_MINUTES = 10
ADMIN_MFA_VALID_HOURS = 12


def _generate_numeric_code() -> str:
    return f"{randbelow(1_000_000):06d}"


@router.post("/admin/login", dependencies=[Depends(rate_limit("admin_login", 5, 900))])
def admin_login_request(payload: AdminLoginRequest, db: Session = Depends(get_db)) -> dict:
    try:
        user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to authenticate") from exc

    if (
        user is None
        or not user.is_active
        or user.role == UserRole.CUSTOMER
        or not verify_password(payload.password, user.password_hash)
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    code = _generate_numeric_code()
    db.add(
        AdminLoginCode(
            user_id=user.id,
            code_hash=hashlib.sha256(code.encode()).hexdigest(),
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=ADMIN_MFA_CODE_TTL_MINUTES),
        )
    )
    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to start admin login") from exc

    email_notifier.admin_login_code(user.email, code, db=db)
    return {"detail": "Verification code sent"}


@router.post("/admin/verify", response_model=Token, dependencies=[Depends(rate_limit("admin_verify", 10, 900))])
def admin_login_verify(payload: AdminVerifyRequest, db: Session = Depends(get_db)) -> Token:
    try:
        user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to verify code") from exc

    if user is None or user.role == UserRole.CUSTOMER:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    code_hash = hashlib.sha256(payload.code.encode()).hexdigest()
    record = db.execute(
        select(AdminLoginCode)
        .where(AdminLoginCode.user_id == user.id, AdminLoginCode.code_hash == code_hash)
        .order_by(AdminLoginCode.id.desc())
    ).scalar_one_or_none()

    if record is None or record.used_at is not None or record.expires_at < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code")

    try:
        record.used_at = now
        user.admin_mfa_verified_until = now + timedelta(hours=ADMIN_MFA_VALID_HOURS)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to verify code") from exc

    record_event(db, "admin_login", user=user)
    return Token(access_token=create_access_token(str(user.id)))


# --- Admin MFA (PRD ТЗ№3 §58) --------------------------------------------
#
# Available to any authenticated account, not force-enabled for admin roles:
# there's no verified path here to hand a brand-new admin account a paired
# authenticator app during account creation, so making MFA an unconditional
# login requirement for every SALES_MANAGER/PRODUCT_MANAGER/etc. account today
# risks locking out an admin who has never completed setup. Once enabled by
# an account (mfa_enabled=True), login DOES enforce it (see login() above).
# Whether to force it on for every admin role by policy, and how newly
# created admin accounts complete first-time setup, is a rollout decision
# for whoever runs this in production — flagged in TODO.md, not decided here.


@router.post(
    "/mfa/setup",
    response_model=MfaSetupOut,
    dependencies=[Depends(rate_limit("mfa_setup", 10, 3600))],
)
def setup_mfa(user: User = Depends(get_current_user_required), db: Session = Depends(get_db)) -> MfaSetupOut:
    """Generates a new TOTP secret and returns it (plus a provisioning URI an
    authenticator app can scan as a QR code). Doesn't enable MFA yet — call
    /auth/mfa/enable with a code generated from it to confirm setup worked."""
    secret = pyotp.random_base32()
    try:
        user.mfa_secret = secret
        user.mfa_enabled = False
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to start MFA setup") from exc

    uri = pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="MARU")
    return MfaSetupOut(secret=secret, provisioning_uri=uri)


@router.post(
    "/mfa/enable",
    dependencies=[Depends(rate_limit("mfa_enable", 10, 3600))],
)
def enable_mfa(
    payload: MfaCodeRequest, user: User = Depends(get_current_user_required), db: Session = Depends(get_db)
) -> dict:
    if not user.mfa_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Call /auth/mfa/setup first")
    if not pyotp.TOTP(user.mfa_secret).verify(payload.code, valid_window=1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code")

    try:
        user.mfa_enabled = True
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to enable MFA") from exc
    return {"detail": "MFA enabled"}


@router.post(
    "/mfa/disable",
    dependencies=[Depends(rate_limit("mfa_disable", 10, 3600))],
)
def disable_mfa(
    payload: MfaCodeRequest, user: User = Depends(get_current_user_required), db: Session = Depends(get_db)
) -> dict:
    if not user.mfa_enabled or not user.mfa_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is not enabled")
    if not pyotp.TOTP(user.mfa_secret).verify(payload.code, valid_window=1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code")

    try:
        user.mfa_enabled = False
        user.mfa_secret = None
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to disable MFA") from exc
    return {"detail": "MFA disabled"}
