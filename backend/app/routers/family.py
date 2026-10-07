# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..deps import get_current_user, get_db

router = APIRouter(prefix="/api/family", tags=["family"])


@router.get("", response_model=list[schemas.FamilyMemberOut])
def list_members(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    members = db.execute(
        select(models.FamilyMember).where(models.FamilyMember.host_user_id == user.id)
    ).scalars().all()
    out = []
    for m in members:
        count = db.execute(
            select(func.count(models.MyDocument.id)).where(
                models.MyDocument.member_id == m.id,
                models.MyDocument.status != "ARCHIVED",
            )
        ).scalar() or 0
        out.append(
            schemas.FamilyMemberOut(
                id=m.id, member_name=m.member_name, member_color=m.member_color, doc_count=count
            )
        )
    return out


@router.post("", response_model=schemas.FamilyMemberOut)
def create_member(
    payload: schemas.FamilyMemberIn,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    m = models.FamilyMember(
        host_user_id=user.id, member_name=payload.member_name.strip(), member_color=payload.member_color
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return schemas.FamilyMemberOut(
        id=m.id, member_name=m.member_name, member_color=m.member_color, doc_count=0
    )


@router.delete("/{member_id}")
def delete_member(
    member_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    m = db.get(models.FamilyMember, member_id)
    if not m or m.host_user_id != user.id:
        raise HTTPException(status_code=404, detail="成员不存在")
    docs = db.execute(
        select(models.MyDocument).where(models.MyDocument.member_id == member_id)
    ).scalars().all()
    for d in docs:
        d.member_id = None
    db.delete(m)
    db.commit()
    return {"ok": True}