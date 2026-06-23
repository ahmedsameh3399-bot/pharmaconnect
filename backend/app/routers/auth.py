"""Authentication endpoints: register / login / refresh / password reset."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models.distributor import Distributor
from app.models.pharmacy import Pharmacy
from app.models.user import User, UserRole
from app.schemas.auth import (
    CurrentUser,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
)
from app.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_password_reset_token,
    hash_password,
    verify_password,
)
from app.services.email import send_email
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext

router = APIRouter(prefix="/auth", tags=["auth"])

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenPair:
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    if payload.role == UserRole.PHARMACY and not payload.pharmacy:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Pharmacy details required")
    if payload.role == UserRole.DISTRIBUTOR and not payload.distributor:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Distributor details required")
    if payload.role == UserRole.ADMIN:
        # Admins are seeded, not self-registered. Locks down obvious privilege escalation.
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin registration is not public")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        full_name=payload.full_name,
    )
    db.add(user)
    db.flush()

    if payload.role == UserRole.PHARMACY:
        assert payload.pharmacy is not None
        db.add(Pharmacy(user_id=user.id, **payload.pharmacy.model_dump()))
    else:
        assert payload.distributor is not None
        db.add(Distributor(user_id=user.id, **payload.distributor.model_dump()))

    db.commit()

    return TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/login", response_model=TokenPair)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenPair:
    # OAuth2PasswordRequestForm uses `username`; we accept the email here.
    user = db.scalar(select(User).where(User.email == form.username))
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    if user.is_suspended or not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is not active")

    return TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    try:
        user_id = decode_token(payload.refresh_token, expected_type="refresh")
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
    user = db.get(User, user_id)
    if not user or not user.is_active or user.is_suspended:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not allowed")
    return TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/password-reset/request", status_code=status.HTTP_204_NO_CONTENT)
def request_password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)) -> None:
    """Always returns 204 - we don't reveal whether the email is registered."""
    user = db.scalar(select(User).where(User.email == payload.email))
    if user:
        plaintext, hashed = generate_password_reset_token()
        user.password_reset_token_hash = hashed
        user.password_reset_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        db.commit()
        send_email(
            to=user.email,
            subject="Pharma Connect password reset",
            body=(
                f"Hi {user.full_name},\n\nUse this token to reset your password "
                f"(valid for 1 hour):\n\n{plaintext}\n\n"
                "If you didn't request this, ignore this email."
            ),
        )


@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
def confirm_password_reset(payload: PasswordResetConfirm, db: Session = Depends(get_db)) -> None:
    # Linear scan is fine: number of users with a pending reset is tiny. The
    # alternative would be storing a public token id alongside the hash.
    users = db.scalars(select(User).where(User.password_reset_token_hash.isnot(None))).all()
    now = datetime.now(timezone.utc)
    for user in users:
        if user.password_reset_expires_at is None or user.password_reset_expires_at < now:
            continue
        if _pwd.verify(payload.token, user.password_reset_token_hash or ""):
            user.hashed_password = hash_password(payload.new_password)
            user.password_reset_token_hash = None
            user.password_reset_expires_at = None
            db.commit()
            return
    raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired token")


@router.get("/me", response_model=CurrentUser)
def me(user: User = Depends(get_current_user)) -> CurrentUser:
    return CurrentUser(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        pharmacy_id=user.pharmacy.id if user.pharmacy else None,
        distributor_id=user.distributor.id if user.distributor else None,
    )
