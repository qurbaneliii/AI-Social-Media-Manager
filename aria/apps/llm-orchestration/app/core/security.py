from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import jwt
from pydantic import BaseModel

from core.config import AppSettings
from core.errors import APIError


class AuthenticatedPrincipal(BaseModel):
    user_id: str
    email: str | None = None
    token_subject: str
    expires_at: datetime | None = None


def verify_access_token(token: str, settings: AppSettings) -> AuthenticatedPrincipal:
    if not settings.JWT_SECRET:
        raise APIError(503, "AUTHENTICATION_UNAVAILABLE", "Server authentication is not configured.")
    try:
        claims: dict[str, Any] = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=["HS256"],
            audience=settings.ARIA_JWT_AUDIENCE,
            issuer=settings.ARIA_JWT_ISSUER,
            options={"require": ["exp", "iat", "sub"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise APIError(401, "TOKEN_EXPIRED", "The access token has expired.") from exc
    except jwt.PyJWTError as exc:
        raise APIError(401, "INVALID_ACCESS_TOKEN", "The access token is invalid.") from exc

    subject = str(claims.get("sub") or "").strip()
    user_id = str(claims.get("userId") or subject).strip()
    if not subject or not user_id:
        raise APIError(401, "INVALID_ACCESS_TOKEN", "The access token has no valid subject.")
    expires_at = datetime.fromtimestamp(int(claims["exp"]), tz=UTC) if claims.get("exp") else None
    return AuthenticatedPrincipal(
        user_id=user_id,
        email=str(claims["email"]) if claims.get("email") else None,
        token_subject=subject,
        expires_at=expires_at,
    )
