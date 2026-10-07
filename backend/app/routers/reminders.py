# -*- coding: utf-8 -*-
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models
from ..deps import get_current_user, get_db
from ..services import expiry_calc

router = APIRouter(prefix="/api/reminders", tags=["reminders"])


def _type_name(db: Session, document_type_id: int | None) -> str:
    t = db.get(models.DocumentType, document_type_id) if document_type_id else None
    return t.name if t else ""


@router.get("/daily")
def daily_pending(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """今日待弹窗的"日常提醒"（每天同一提醒最多一条）。"""
    rows = db.execute(
        select(models.AppNotification, models.MyDocument)
        .join(models.MyDocument, models.AppNotification.document_id == models.MyDocument.id)
        .join(models.ReminderJob, models.AppNotification.job_id == models.ReminderJob.id)
        .where(
            models.AppNotification.user_id == user.id,
            models.AppNotification.status == "PENDING",
            models.AppNotification.notify_date == date.today(),
            models.ReminderJob.status == "PENDING",
        )
        .order_by(models.AppNotification.id)
        .limit(20)
    ).all()
    return [
        {
            "id": n.id,
            "document_id": n.document_id,
            "document_title": n.document_title,
            "content": n.content,
            "notify_date": n.notify_date.isoformat(),
            "days_left": expiry_calc.days_left(doc.expire_date),
            "doc_status": doc.status,
            "type_name": _type_name(db, doc.document_type_id),
        }
        for n, doc in rows
    ]


@router.post("/daily/{notification_id}/dismiss")
def dismiss_daily(
    notification_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """当天忽略一条"日常弹窗"；明天会再提醒，直到证件被处理。"""
    n = db.get(models.AppNotification, notification_id)
    if not n or n.user_id != user.id:
        raise HTTPException(status_code=404, detail="通知不存在")
    n.status = "DISMISSED"
    db.commit()
    return {"ok": True}


@router.get("")
def list_reminders(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    jobs = (
        db.execute(
            select(models.ReminderJob, models.MyDocument, models.ReminderRule)
            .join(models.MyDocument, models.ReminderJob.document_id == models.MyDocument.id)
            .join(models.ReminderRule, models.ReminderJob.rule_id == models.ReminderRule.id)
            .where(models.MyDocument.user_id == user.id)
            .order_by(models.ReminderJob.remind_on.desc(), models.ReminderJob.id.desc())
            .limit(200)
        )
        .all()
    )
    result = []
    types = {t.id: t for t in db.execute(select(models.DocumentType)).scalars().all()}
    for job, doc, rule in jobs:
        dname, dicon = "", "🪪"
        t = types.get(doc.document_type_id)
        if t:
            dname, dicon = t.name, t.icon
        result.append(
            {
                "id": job.id,
                "document_id": doc.id,
                "doc_title": doc.title,
                "type_name": dname,
                "type_icon": dicon,
                "expire_date": doc.expire_date.isoformat(),
                "remind_on": job.remind_on.isoformat(),
                "days_left": expiry_calc.days_left(doc.expire_date),
                "ahead_days": rule.ahead_days,
                "status": job.status,
            }
        )
    return result


@router.post("/{job_id}/dismiss")
def dismiss(job_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    job = db.get(models.ReminderJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="提醒不存在")
    doc = db.get(models.MyDocument, job.document_id)
    if not doc or doc.user_id != user.id:
        raise HTTPException(status_code=403, detail="无权操作")
    job.status = "DONE"
    # 结清后，该提醒的"每日弹窗"一并归档，不再弹出
    notifs = db.query(models.AppNotification).filter(
        models.AppNotification.job_id == job.id,
        models.AppNotification.status == "PENDING",
    ).all()
    for n in notifs:
        n.status = "DONE"
    db.commit()
    return {"ok": True}