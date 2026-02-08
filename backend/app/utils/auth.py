"""JWT auth utilities."""

from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from app.config import settings

ALGORITHM = "HS256"


def _create_token(subject: str, expires_delta: timedelta, secret: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def create_access_token(user_id: int) -> str:
    return _create_token(
        subject=str(user_id),
        expires_delta=timedelta(minutes=settings.jwt_access_exp_minutes),
        secret=settings.jwt_secret,
    )


def create_refresh_token(user_id: int) -> str:
    return _create_token(
        subject=str(user_id),
        expires_delta=timedelta(days=settings.jwt_refresh_exp_days),
        secret=settings.jwt_refresh_secret,
    )


def verify_access_token(token: str) -> int:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        return int(payload.get("sub"))
    except (JWTError, ValueError) as exc:
        raise ValueError("Invalid access token") from exc


def verify_refresh_token(token: str) -> int:
    try:
        payload = jwt.decode(token, settings.jwt_refresh_secret, algorithms=[ALGORITHM])
        return int(payload.get("sub"))
    except (JWTError, ValueError) as exc:
        raise ValueError("Invalid refresh token") from exc
