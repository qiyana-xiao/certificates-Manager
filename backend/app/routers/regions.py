# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..deps import get_current_user, get_db

router = APIRouter(prefix="/api/provinces", tags=["provinces"])


@router.get("", response_model=list[schemas.ProvinceOut])
def list_provinces(
    db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    rows = db.execute(select(models.Province).order_by(models.Province.sort)).scalars().all()
    return rows
