# -*- coding: utf-8 -*-
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..deps import get_admin_user, get_current_user, get_db

router = APIRouter(prefix="/api/guides", tags=["guides"])


def _g_to_out(db: Session, g: models.RenewalGuide) -> schemas.GuideOut:
    tname, ticon = "", "🪪"
    t = db.get(models.DocumentType, g.document_type_id)
    if t:
        tname, ticon = t.name, t.icon
    rname = ""
    if g.region_code:
        p = db.get(models.Province, g.region_code)
        rname = p.name if p else g.region_code
    return schemas.GuideOut(
        id=g.id,
        document_type_id=g.document_type_id,
        type_name=tname,
        type_icon=ticon,
        title=g.title,
        region_code=g.region_code,
        region_name=rname,
        link_mode=g.link_mode,
        materials=g.materials or [],
        location=g.location or "",
        fee=g.fee or "",
        duration=g.duration or "",
        official_url=g.official_url or "",
        source=g.source or "",
        updated_at=g.updated_at,
        disclaimer=g.disclaimer or "",
    )


def _validate(payload: schemas.GuideIn, db: Session):
    if not db.get(models.DocumentType, payload.document_type_id):
        raise HTTPException(status_code=400, detail="证件类型不存在")
    if payload.link_mode not in schemas.LINK_MODES:
        raise HTTPException(status_code=400, detail="链接模式无效")
    region = (payload.region_code or "").strip() or None
    if region and not db.get(models.Province, region):
        raise HTTPException(status_code=400, detail="省份代码无效")
    return region


@router.get("", response_model=list[schemas.GuideOut])
def list_guides(
    type_id: int | None = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    q = select(models.RenewalGuide)
    if type_id:
        q = q.where(models.RenewalGuide.document_type_id == type_id)
    guides = (
        db.execute(
            q.order_by(
                models.RenewalGuide.document_type_id,
                models.RenewalGuide.region_code,  # NULL(全国) 在前，各省版在后
            )
        )
        .scalars()
        .all()
    )
    return [_g_to_out(db, g) for g in guides]


@router.post("", response_model=schemas.GuideOut)
def create_guide(
    payload: schemas.GuideIn,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_admin_user),
):
    region = _validate(payload, db)
    g = models.RenewalGuide(
        document_type_id=payload.document_type_id,
        title=payload.title.strip(),
        region_code=region,
        link_mode=payload.link_mode,
        materials=payload.materials,
        location=payload.location or "",
        fee=payload.fee or "",
        duration=payload.duration or "",
        official_url=payload.official_url or "",
        source=payload.source.strip(),
        updated_at=payload.updated_at or date.today(),
        disclaimer=payload.disclaimer,
    )
    db.add(g)
    db.add(models.AuditLog(admin_id=admin.id, action="create_guide", target=payload.title))
    db.commit()
    db.refresh(g)
    return _g_to_out(db, g)


@router.put("/{guide_id}", response_model=schemas.GuideOut)
def update_guide(
    guide_id: int,
    payload: schemas.GuideIn,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_admin_user),
):
    g = db.get(models.RenewalGuide, guide_id)
    if not g:
        raise HTTPException(status_code=404, detail="指南不存在")
    region = _validate(payload, db)
    for f in ("document_type_id", "title", "materials", "location", "fee",
              "duration", "official_url", "source", "disclaimer"):
        setattr(g, f, getattr(payload, f))
    g.region_code = region
    g.link_mode = payload.link_mode
    g.updated_at = payload.updated_at or date.today()
    db.add(models.AuditLog(admin_id=admin.id, action="update_guide", target=g.title))
    db.commit()
    db.refresh(g)
    return _g_to_out(db, g)


@router.delete("/{guide_id}")
def delete_guide(
    guide_id: int, db: Session = Depends(get_db), admin: models.User = Depends(get_admin_user)
):
    g = db.get(models.RenewalGuide, guide_id)
    if not g:
        raise HTTPException(status_code=404, detail="指南不存在")
    db.add(models.AuditLog(admin_id=admin.id, action="delete_guide", target=g.title))
    db.delete(g)
    db.commit()
    return {"ok": True}
