# -*- coding: utf-8 -*-
from typing import Generator

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from . import models, security
from .database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _bearer_token(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    raise HTTPException(status_code=401, detail="未登录或登录已过期")


def get_current_user(
    request: Request,
    token: str = Depends(_bearer_token),
    db: Session = Depends(get_db),
) -> models.User:
    payload = security.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token 无效或已过期")
    if is_revoked(payload.get("jti", "")):
        raise HTTPException(status_code=401, detail="Token 已注销")
    user = db.get(models.User, int(payload.get("sub", 0)))
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


def get_admin_user(user: models.User = Depends(get_current_user)) -> models.User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


# ---- JWT 注销黑名单（Redis 可选；Redis 不可用时退化为进程内记忆，短期窗口可接受）----
_revoked_mem: set = set()
_redis = None


def _get_redis():
    global _redis
    if _redis is not None:
        return _redis
    try:
        import redis as redis_mod

        from . import config as _cfg

        r = redis_mod.from_url(_cfg.REDIS_URL)
        r.ping()
        _redis = r
        return r
    except Exception:
        _redis = False
        return None


def revoke_token(jti: str, ttl_seconds: int = 3600):
    r = _get_redis()
    if r:
        try:
            r.setex(f"doc-keeper:jwt:revoked:{jti}", ttl_seconds, "1")
            return
        except Exception:
            pass
    _revoked_mem.add(jti)


def is_revoked(jti: str) -> bool:
    if not jti:
        return False
    r = _get_redis()
    if r:
        try:
            return bool(r.get(f"doc-keeper:jwt:revoked:{jti}"))
        except Exception:
            pass
    return jti in _revoked_mem