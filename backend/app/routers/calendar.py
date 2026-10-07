# -*- coding: utf-8 -*-
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models
from ..deps import get_current_user, get_db
from ..services import expiry_calc

router = APIRouter(prefix="/api", tags=["calendar"])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    today = date.today()
    docs = db.execute(
        select(models.MyDocument).where(models.MyDocument.user_id == user.id)
    ).scalars().all()
    active = [d for d in docs if d.status != expiry_calc.ARCHIVED]
    expired = [d for d in active if d.status == expiry_calc.EXPIRED]
    next30 = [d for d in active if 0 <= expiry_calc.days_left(d.expire_date, today) <= 30]
    due_today = [d for d in active if d.expire_date == today]
    recent_jobs = db.execute(
        select(models.ReminderJob)
        .join(models.MyDocument)
        .where(models.MyDocument.user_id == user.id)
        .order_by(models.ReminderJob.remind_on.desc())
        .limit(5)
    ).scalars().all()
    return {
        "due_today": len(due_today),
        "next30": len(next30),
        "expired": len(expired),
        "total_active": len(active),
        "recent_reminders": [
            {"id": j.id, "document_id": j.document_id, "remind_on": j.remind_on.isoformat()}
            for j in recent_jobs
        ],
    }


@router.get("/calendar")
def calendar(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    docs = db.execute(
        select(models.MyDocument)
        .where(models.MyDocument.user_id == user.id, models.MyDocument.status != "ARCHIVED")
    ).scalars().all()
    out = []
    for d in docs:
        if d.expire_date.year == year and d.expire_date.month == month:
            out.append(
                {
                    "id": d.id,
                    "title": d.title,
                    "expire_date": d.expire_date.isoformat(),
                    "days_left": expiry_calc.days_left(d.expire_date),
                    "status": d.status,
                }
            )
    return {"year": year, "month": month, "items": out}


@router.get("/calendar/year")
def calendar_year(
    year: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    docs = db.execute(
        select(models.MyDocument)
        .where(models.MyDocument.user_id == user.id, models.MyDocument.status != "ARCHIVED")
    ).scalars().all()
    months = {m: [] for m in range(1, 13)}
    for d in docs:
        if d.expire_date.year == year:
            months[d.expire_date.month].append(
                {"id": d.id, "title": d.title, "day": d.expire_date.day, "status": d.status}
            )
    return {"year": year, "months": {str(k): v for k, v in months.items()}}