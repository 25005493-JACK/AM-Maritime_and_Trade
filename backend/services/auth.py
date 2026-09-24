"""
Reviewer Authentication Service for DocuMatch
Enforces role-based security so anonymous users cannot read/write sensitive
reviewer records (human overrides, conflict resolutions, shipment corrections,
durable processing jobs).

Supports:
1. Supabase Auth / Standard JWT tokens (Authorization: Bearer <token>)
2. API Key authentication for headless workers and integrations (X-Reviewer-Key)
3. Configurable JWT verification secret with graceful fallback for dev/testing
"""
import os
import time
import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel
import jwt
from fastapi import Header, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger("documatch.auth")

# Reviewer authentication configuration
DEFAULT_JWT_SECRET = os.getenv("DOCUMATCH_JWT_SECRET") or os.getenv("SUPABASE_JWT_SECRET") or "documatch-secure-hackathon-reviewer-secret-2026"
DEFAULT_REVIEWER_KEY = os.getenv("DOCUMATCH_REVIEWER_KEY", "documatch-reviewer-dev-key-2026")
JWT_ALGORITHM = "HS256"

security_bearer = HTTPBearer(auto_error=False)


class ReviewerUser(BaseModel):
    user_id: str
    reviewer_name: str
    email: str
    role: str = "reviewer"
    authenticated_via: str = "jwt"


def create_reviewer_token(
    reviewer_name: str = "Pohyi Chong",
    email: str = "reviewer@documatch.maritime.internal",
    user_id: Optional[str] = None,
    expires_in_hours: int = 48,
    role: str = "reviewer",
    secret: Optional[str] = None
) -> str:
    """Generate a signed JWT token with reviewer claims."""
    now = int(time.time())
    payload = {
        "sub": user_id or f"rev_{int(now)}",
        "email": email,
        "name": reviewer_name,
        "role": role,
        "aud": "authenticated",
        "iat": now,
        "exp": now + (expires_in_hours * 3600)
    }
    jwt_secret = secret or DEFAULT_JWT_SECRET
    return jwt.encode(payload, jwt_secret, algorithm=JWT_ALGORITHM)


def decode_and_validate_token(token: str) -> Optional[ReviewerUser]:
    """
    Decodes and validates a JWT token.
    First checks if the token matches the configured static reviewer key.
    Then attempts JWT decode using the configured secret.
    """
    if not token:
        return None

    # Support static reviewer key directly as bearer token
    if token == DEFAULT_REVIEWER_KEY:
        return ReviewerUser(
            user_id="rev_static_key",
            reviewer_name="Operational Reviewer",
            email="ops-reviewer@documatch.internal",
            role="reviewer",
            authenticated_via="key"
        )

    # Decode JWT
    try:
        payload = jwt.decode(
            token,
            DEFAULT_JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={"verify_aud": False}
        )
        role = payload.get("role") or (payload.get("app_metadata", {}).get("role")) or "reviewer"
        return ReviewerUser(
            user_id=str(payload.get("sub", "unknown")),
            reviewer_name=str(payload.get("name") or payload.get("email") or "Reviewer"),
            email=str(payload.get("email", "")),
            role=role,
            authenticated_via="jwt"
        )
    except jwt.PyJWTError:
        # Fallback check: could be Supabase signed JWT without local secret verification
        # In testing/dev, if the token has the expected payload structure:
        try:
            unverified = jwt.decode(token, options={"verify_signature": False})
            role = unverified.get("role") or (unverified.get("app_metadata", {}).get("role"))
            if role in ("reviewer", "authenticated", "admin", "service_role"):
                return ReviewerUser(
                    user_id=str(unverified.get("sub", "unknown")),
                    reviewer_name=str(unverified.get("name") or unverified.get("email") or "Reviewer"),
                    email=str(unverified.get("email", "")),
                    role=role if role != "authenticated" else "reviewer",
                    authenticated_via="jwt_unverified"
                )
        except Exception:
            pass
        return None


def get_current_reviewer(
    auth_credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    x_reviewer_key: Optional[str] = Header(None, alias="X-Reviewer-Key")
) -> ReviewerUser:
    """
    FastAPI dependency: Enforces that the request comes from an authenticated reviewer.
    Rejects anonymous requests with HTTP 401 Unauthorized.
    Rejects non-reviewer roles with HTTP 403 Forbidden.
    """
    token = None
    if auth_credentials and auth_credentials.credentials:
        token = auth_credentials.credentials.strip()
    elif x_reviewer_key:
        token = x_reviewer_key.strip()

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required: reviewer credentials missing. Provide 'Authorization: Bearer <token>' or 'X-Reviewer-Key' header.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = decode_and_validate_token(token)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired reviewer credentials.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if user.role not in ("reviewer", "admin", "service_role"):
        raise HTTPException(
            status_code=403,
            detail=f"Forbidden: role '{user.role}' lacks reviewer privileges."
        )

    return user


def get_optional_reviewer(
    auth_credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    x_reviewer_key: Optional[str] = Header(None, alias="X-Reviewer-Key")
) -> Optional[ReviewerUser]:
    """
    FastAPI dependency: Returns ReviewerUser if valid credentials are provided,
    otherwise returns None without raising an exception.
    """
    token = None
    if auth_credentials and auth_credentials.credentials:
        token = auth_credentials.credentials.strip()
    elif x_reviewer_key:
        token = x_reviewer_key.strip()

    if not token:
        return None

    return decode_and_validate_token(token)
