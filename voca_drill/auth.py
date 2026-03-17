"""JWT 인증 — SyOps JWT 토큰 검증."""

from __future__ import annotations

import os

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def _get_secret_key() -> str:
    key = os.environ.get("SYOPS_SECRET_KEY", "dev-secret")
    return key


def decode_token(token: str) -> dict:
    """SyOps JWT 토큰을 검증하고 페이로드 반환."""
    try:
        payload = jwt.decode(token, _get_secret_key(), algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def get_current_user_id(token: str | None = Depends(oauth2_scheme)) -> int:
    """현재 사용자 ID 추출. 인증 필수 엔드포인트에 사용."""
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_token(token)
    try:
        return int(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")


def get_optional_user_id(token: str | None = Depends(oauth2_scheme)) -> int | None:
    """사용자 ID 추출. 인증 선택적 엔드포인트에 사용."""
    if token is None:
        return None
    try:
        payload = decode_token(token)
        return int(payload["sub"])
    except Exception:
        return None
