"""FastAPI dependency injection helpers.

These are imported by routers via `Depends(get_current_user)` etc. The pattern
keeps auth/role enforcement out of route handler bodies, which keeps the
handlers focused on the actual feature.
"""

from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.user import User, UserRole
from app.security import decode_token

# tokenUrl is the endpoint where Swagger UI's "Authorize" button posts to
# get a token. It must match the actual login route.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    try:
        user_id = decode_token(token, expected_type="access")
    except JWTError:
        raise credentials_exception
    user = db.get(User, user_id)
    if user is None or not user.is_active or user.is_suspended:
        raise credentials_exception
    return user


def require_role(*roles: UserRole):
    """Factory that returns a dependency permitting only the given roles."""

    def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {[r.value for r in roles]}",
            )
        return user

    return _checker


require_pharmacy = require_role(UserRole.PHARMACY)
require_distributor = require_role(UserRole.DISTRIBUTOR)
require_admin = require_role(UserRole.ADMIN)
