"""辰星 (Chenxing) <-> deer-flow server-to-server session bridge.

CARRY-PATCH (keep across upstream merges): isolated add-on that lets the
Chenxing backend obtain a deer-flow access token for a given Chenxing
user id, authenticated by an HMAC signature over a shared secret
(env CX_S2S_SECRET). Each Chenxing user maps to a dedicated deer-flow
user (cx-{uid}@chenxing.local), giving per-user data isolation via the
standard owner-scoped persistence. No public registration needed.

Companion tiny touch points (also carry-patches):
  - app.py: import cx_auth + app.include_router(cx_auth.router)
  - auth_middleware._PUBLIC_EXACT_PATHS: add /api/v1/auth/cx-session
  - csrf_middleware._AUTH_EXEMPT_PATHS: add /api/v1/auth/cx-session
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from app.gateway.auth.config import get_auth_config
from app.gateway.auth.jwt import create_access_token
from app.gateway.deps import get_local_provider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["chenxing-s2s"])

# Clock-skew tolerance for the signed timestamp (seconds).
_MAX_SKEW_SECONDS = 300


class CxSessionResponse(BaseModel):
    access_token: str
    user_id: str
    expires_in: int


def _verify_signature(uid: str, ts: str, nonce: str, sign: str) -> bool:
    """Verify HMAC-SHA256 over "uid\\nts\\nnonce" with the shared secret."""
    secret = os.environ.get("CX_S2S_SECRET", "")
    if not (secret and uid and ts and nonce and sign):
        return False
    try:
        if abs(time.time() - float(ts)) > _MAX_SKEW_SECONDS:
            return False
    except ValueError:
        return False
    message = f"{uid}\n{ts}\n{nonce}".encode("utf-8")
    expected = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sign)


@router.post("/cx-session", response_model=CxSessionResponse)
async def cx_session(request: Request) -> CxSessionResponse:
    """Issue a deer-flow access token for a Chenxing user (HMAC-authenticated).

    The Chenxing backend signs (uid, ts, nonce) with CX_S2S_SECRET and sends
    the result in headers. We provision/find the mapped deer-flow user and
    mint a standard JWT, which the caller then uses as the access_token
    cookie (plus a self-generated csrf double-submit) for /api/threads,
    /api/runs, etc.
    """
    uid = request.headers.get("x-cx-uid", "")
    ts = request.headers.get("x-cx-ts", "")
    nonce = request.headers.get("x-cx-nonce", "")
    sign = request.headers.get("x-cx-sign", "")

    if not _verify_signature(uid, ts, nonce, sign):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid cx signature")

    provider = get_local_provider()
    email = f"cx-{uid}@chenxing-ai.com"
    user = await provider.get_user_by_email(email)
    if user is None:
        user = await provider.create_user(email=email, password=None, system_role="user")
        logger.info("cx-session provisioned deer-flow user for chenxing uid=%s -> %s", uid, user.id)

    token = create_access_token(str(user.id), token_version=user.token_version)
    return CxSessionResponse(
        access_token=token,
        user_id=str(user.id),
        expires_in=get_auth_config().token_expiry_days * 24 * 3600,
    )
