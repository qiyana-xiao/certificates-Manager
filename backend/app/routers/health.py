# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..deps import _get_redis, get_db

router = APIRouter()


@router.get("/api/health")
def health():
    return {"status": "UP"}


@router.get("/api/health/ready")
def ready(db: Session = Depends(get_db)):
    mysql_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        mysql_ok = False

    redis_ok = False
    r = _get_redis()
    if r:
        try:
            r.ping()
            redis_ok = True
        except Exception:
            redis_ok = False

    status = "READY" if mysql_ok else "NOT_READY"
    return {
        "status": status,
        "mysql": "UP" if mysql_ok else "DOWN",
        "redis": "UP" if redis_ok else ("DOWN" if r is None else "DOWN"),
    }