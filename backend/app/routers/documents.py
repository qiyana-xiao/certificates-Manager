# -*- coding: utf-8 -*-
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas, security
from ..deps import get_current_user, get_db
from ..services import expiry_calc

router = APIRouter(prefix="/api", tags=["documents"])


def _doc_to_out(doc: models.MyDocument, color: str = "", name: str = "", dname: str = "", dicon: str = "🪪"):
    return schemas.DocumentOut(
        id=doc.id,
        document_type_id=doc.document_type_id,
        member_id=doc.member_id,
        member_name=name,
        member_color=color,
        type_name=dname,
        type_icon=dicon,
        title=doc.title,
        doc_number_masked=security.mask_number(security.decrypt_value(doc.doc_number_cipher)),
        start_date=doc.start_date,
        valid_years=doc.valid_years,
        expire_date=doc.expire_date,
        days_left=expiry_calc.days_left(doc.expire_date),
        status=doc.status,
        note=doc.note,
    )


@router.get("/document-types", response_model=list[schemas.DocumentTypeOut])
def list_types(db: Session = Depends(get_db)):
    return db.execute(select(models.DocumentType).order_by(models.DocumentType.id)).scalars().all()


@router.get("/documents", response_model=list[schemas.DocumentOut])
def list_documents(
    db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    rows = []
    docs = (
        db.execute(
            select(models.MyDocument)
            .where(models.MyDocument.user_id == user.id)
            .order_by(models.MyDocument.expire_date)
        )
        .scalars()
        .all()
    )
    for d in docs:
        rows.append(_decorate(db, d))
    return rows


def _decorate(db: Session, doc: models.MyDocument) -> schemas.DocumentOut:
    color = ""
    name = ""
    if doc.member_id:
        m = db.get(models.FamilyMember, doc.member_id)
        if m:
            color = m.member_color
            name = m.member_name
    dname, dicon = "", "🪪"
    if doc.document_type_id:
        t = db.get(models.DocumentType, doc.document_type_id)
        if t:
            dname, dicon = t.name, t.icon
    return _doc_to_out(doc, color, name, dname, dicon)


@router.post("/documents", response_model=schemas.DocumentOut)
def create_document(
    payload: schemas.DocumentIn,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    expire = payload.resolve_expire_date()
    if not expire:
        raise HTTPException(status_code=400, detail="需提供到期日，或提供起始日+有效年限")
    if payload.member_id:
        m = db.get(models.FamilyMember, payload.member_id)
        if not m or m.host_user_id != user.id:
            raise HTTPException(status_code=403, detail="家庭成员不存在")
    doc = models.MyDocument(
        user_id=user.id,
        document_type_id=payload.document_type_id,
        member_id=payload.member_id,
        title=payload.title.strip(),
        doc_number_cipher=security.encrypt_value(payload.doc_number.strip()),
        start_date=payload.start_date,
        valid_years=payload.valid_years,
        expire_date=expire,
        status=expiry_calc.status_of(expire),
        note=payload.note.strip(),
    )
    db.add(doc)
    db.flush()
    # 默认提醒档位：优先证件类型预设，否则 90/30/7
    ahead = [90, 30, 7]
    if payload.document_type_id:
        t = db.get(models.DocumentType, payload.document_type_id)
        if t and t.default_ahead_days:
            ahead = t.default_ahead_days
    for a in ahead:
        db.add(models.ReminderRule(document_id=doc.id, ahead_days=a, enabled=True))
    db.commit()
    db.refresh(doc)
    return _decorate(db, doc)


@router.patch("/documents/{doc_id}", response_model=schemas.DocumentOut)
def update_document(
    doc_id: int,
    payload: schemas.DocumentIn,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    doc = _own(db, user.id, doc_id)
    if payload.title:
        doc.title = payload.title.strip()
    if payload.doc_number:
        doc.doc_number_cipher = security.encrypt_value(payload.doc_number.strip())
    if payload.start_date:
        doc.start_date = payload.start_date
    if payload.valid_years is not None:
        doc.valid_years = payload.valid_years
    if payload.member_id is not None:
        doc.member_id = payload.member_id or None
    if payload.note is not None:
        doc.note = payload.note.strip()
    expire = payload.resolve_expire_date() or doc.expire_date
    doc.expire_date = expire
    doc.status = expiry_calc.status_of(expire)
    db.commit()
    db.refresh(doc)
    return _decorate(db, doc)


@router.post("/documents/{doc_id}/archive")
def archive_document(
    doc_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    doc = _own(db, user.id, doc_id)
    doc.status = expiry_calc.ARCHIVED
    _close_reminders(db, doc_id)
    db.commit()
    return {"ok": True}


def _close_reminders(db: Session, doc_id: int):
    """结清某证件的全部待办提醒与今日弹窗，处理后再不打扰。"""
    # 待办提醒 → DONE（后续日报扫描不再为它生成新弹窗）
    rows = db.execute(
        select(models.ReminderJob).where(
            models.ReminderJob.document_id == doc_id,
            models.ReminderJob.status == "PENDING",
        )
    ).scalars().all()
    job_ids = [j.id for j in rows]
    for j in rows:
        j.status = "DONE"
    # 已生成而未阅读的每日弹窗 → DONE
    if job_ids:
        notifs = db.execute(
            select(models.AppNotification).where(
                models.AppNotification.job_id.in_(job_ids),
                models.AppNotification.status == "PENDING",
            )
        ).scalars().all()
        for n in notifs:
            n.status = "DONE"


@router.delete("/documents/{doc_id}")
def delete_document(
    doc_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    doc = _own(db, user.id, doc_id)
    db.delete(doc)
    db.commit()
    return {"ok": True}


@router.get("/documents/{doc_id}/rules")
def get_rules(doc_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    _own(db, user.id, doc_id)
    rules = db.execute(
        select(models.ReminderRule).where(models.ReminderRule.document_id == doc_id)
    ).scalars().all()
    return [{"id": r.id, "ahead_days": r.ahead_days, "enabled": r.enabled} for r in rules]


@router.put("/documents/{doc_id}/rules")
def set_rules(
    doc_id: int,
    payload: list[schemas.ReminderRuleIn],
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    doc = _own(db, user.id, doc_id)
    existing = db.execute(
        select(models.ReminderRule).where(models.ReminderRule.document_id == doc_id)
    ).scalars().all()
    seen = set()
    for r in existing:
        hit = next((p for p in payload if p.ahead_days == r.ahead_days), None)
        if hit:
            r.enabled = hit.enabled
            seen.add(r.ahead_days)
        else:
            db.delete(r)
    for p in payload:
        if p.ahead_days not in seen:
            db.add(models.ReminderRule(document_id=doc_id, ahead_days=p.ahead_days, enabled=p.enabled))
    db.commit()
    return {"ok": True}


@router.post("/documents/{doc_id}/renew")
def renew_document(
    doc_id: int,
    payload: schemas.DocumentIn,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """已办新证：原证归为归档，并创建一张新证。"""
    old = _own(db, user.id, doc_id)
    old.status = expiry_calc.ARCHIVED
    _close_reminders(db, doc_id)
    db.commit()
    return create_document(payload, db, user)


def _own(db: Session, user_id: int, doc_id: int) -> models.MyDocument:
    doc = db.get(models.MyDocument, doc_id)
    if not doc or doc.user_id != user_id:
        raise HTTPException(status_code=404, detail="证件不存在")
    return doc