# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas, security
from ..deps import get_current_user, get_db, is_revoked, revoke_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=schemas.TokenOut)
def register(payload: schemas.RegisterIn, db: Session = Depends(get_db)):
    name = payload.username.strip()
    exists = db.execute(
        select(models.User).where(models.User.username == name)
    ).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = models.User(
        username=name,
        password_hash=security.hash_password(payload.password),
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _token_pair(user)


@router.post("/login", response_model=schemas.TokenOut)
def login(payload: schemas.LoginIn, db: Session = Depends(get_db)):
    user = db.execute(
        select(models.User).where(models.User.username == payload.username.strip())
    ).scalar_one_or_none()
    if not user or not security.verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return _token_pair(user)


@router.post("/refresh", response_model=schemas.TokenOut)
def refresh(payload: dict, db: Session = Depends(get_db)):
    token = (payload.get("refresh_token") or "").strip()
    data = security.decode_token(token)
    if not data or data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="refresh token 无效")
    user = db.get(models.User, int(data["sub"]))
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return _token_pair(user)


@router.post("/logout")
def logout(
    payload: dict,
    user: models.User = Depends(get_current_user),
):
    token = (payload.get("access_token") or "").strip()
    if token:
        data = security.decode_token(token)
        if data:
            revoke_token(data.get("jti", ""))
    return {"ok": True}


@router.get("/me", response_model=schemas.UserOut)
def me(user: models.User = Depends(get_current_user)):
    return user


@router.put("/me", response_model=schemas.UserOut)
def update_me(
    payload: schemas.ProfileIn,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """更新个人资料（当前仅省份，用于指南与官方入口按省直达）。"""
    code = (payload.province_code or "").strip() or None
    if code and not db.get(models.Province, code):
        raise HTTPException(status_code=400, detail="省份代码无效")
    user.province_code = code
    db.commit()
    db.refresh(user)
    return user


def _token_pair(user: models.User) -> dict:
    return {
        "access_token": security.create_access_token(user.id, user.username, user.role),
        "refresh_token": security.create_refresh_token(user.id),
        "token_type": "bearer",
    }