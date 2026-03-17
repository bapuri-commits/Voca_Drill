"""JWT 인증 — SyOps JWT 토큰 검증 (Bearer 헤더 + syops_token 쿠키)."""

from __future__ import annotations

import os

import jwt
from fastapi import Cookie, Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

ALGORITHM = "HS256"
SERVICE_ID = "voca_drill"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def _get_secret_key() -> str:
    return os.environ.get("SYOPS_SECRET_KEY", "dev-secret")


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


def _extract_jwt(
    bearer: str | None = Depends(oauth2_scheme),
    syops_token: str | None = Cookie(default=None),
) -> str | None:
    """Bearer 헤더 또는 syops_token 쿠키에서 JWT 추출."""
    return bearer or syops_token


def _check_service_access(payload: dict) -> None:
    """voca_drill 서비스 접근 권한 체크. admin은 무조건 통과."""
    role = payload.get("role", "user")
    services = payload.get("services", [])
    if role != "admin" and SERVICE_ID not in services:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Voca Drill access denied")


def get_current_user_id(token: str | None = Depends(_extract_jwt)) -> int:
    """현재 사용자 ID 추출. 인증 필수 엔드포인트에 사용."""
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_token(token)
    _check_service_access(payload)
    try:
        return int(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")


def get_optional_user_id(token: str | None = Depends(_extract_jwt)) -> int | None:
    """사용자 ID 추출. 인증 선택적 엔드포인트에 사용. 403(권한 없음)은 그대로 raise."""
    if token is None:
        return None
    try:
        payload = decode_token(token)
        _check_service_access(payload)
        return int(payload["sub"])
    except HTTPException as e:
        if e.status_code == status.HTTP_403_FORBIDDEN:
            raise
        return None
    except Exception:
        return None
