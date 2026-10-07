# -*- coding: utf-8 -*-
"""提醒引擎：确定性扫描 + 幂等去重。

每天"到点"(remind_on == expire_date - ahead_days)的提醒，才会生成 reminder_jobs。
幂等：Redis SETNX 快通道 + 数据库唯一索引兜底，同证同档同天只提醒一次。
"""
import logging
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import models
from . import expiry_calc

logger = logging.getLogger("doc-keeper.reminder")

_redis = None


def _r():
    global _redis
    if _redis is not None:
        return _redis
    try:
        import redis as _redis_mod

        from .. import config as _cfg

        _redis = _redis_mod.from_url(_cfg.REDIS_URL)
        _redis.ping()
        return _redis
    except Exception:
        _redis = False
        return None


def scan_once(db: Session, today: date | None = None) -> int:
    """扫描一次，返回本次新建的"待办/弹窗"条数。"""
    today = today or date.today()
    created = 0
    docs = db.execute(
        select(models.MyDocument).where(
            models.MyDocument.status.in_([expiry_calc.VALID, expiry_calc.EXPIRING])
        )
    ).scalars().all()

    for doc in docs:
        for rule in doc.rules:
            if not rule.enabled or rule.ahead_days < 0:
                continue
            remind_on = doc.expire_date - timedelta(days=rule.ahead_days)
            if remind_on != today:
                continue
            if _emit(db, doc.id, rule.id, remind_on):
                created += 1

    # 到点后（remind_on <= 今天）且尚未结清的提醒，每天补一条"日常弹窗"，直到被处理。
    # 幂等：插入前先查重 + 唯一索引(job_id, notify_date)兜底，同一天同一条提醒只弹一次。
    pending = db.execute(
        select(models.ReminderJob, models.MyDocument)
        .join(models.MyDocument, models.ReminderJob.document_id == models.MyDocument.id)
        .where(
            models.ReminderJob.status == "PENDING",
            models.ReminderJob.remind_on <= today,
            models.MyDocument.status != expiry_calc.ARCHIVED,
        )
        .order_by(models.ReminderJob.id)  # 尽早先处理旧提醒
    ).all()
    for job, doc in pending:
        if _emit_daily(db, job, doc, today):
            created += 1
    try:
        db.commit()
    except IntegrityError:
        db.rollback()  # 极小概率并发重复，交给唯一索引；整批丢弃下次扫描重来更安全
    return created


def _emit_daily(db: Session, job: models.ReminderJob, doc: models.MyDocument, today: date) -> bool:
    # 先查重，避免触碰唯一约束；普通单进程扫描下判定不重复就必可插入
    dup = db.execute(
        select(models.AppNotification.id).where(
            models.AppNotification.job_id == job.id,
            models.AppNotification.notify_date == today,
        )
    ).scalar_one_or_none()
    if dup:
        return False
    n = models.AppNotification(
        user_id=doc.user_id,
        job_id=job.id,
        document_id=job.document_id,
        document_title=doc.title,
        content=f"您的证件「{doc.title}」已到提醒日，仍未处理，请留意续办。",
        notify_date=today,
        status="PENDING",
    )
    db.add(n)
    db.flush()
    return True


def _emit(db: Session, document_id: int, rule_id: int, remind_on: date) -> bool:
    """SETNX 快通道命中则跳过；数据库唯一索引做最终保证。"""
    r = _r()
    if r:
        try:
            ok = r.set(
                f"doc-keeper:reminder:{document_id}:{rule_id}:{remind_on.isoformat()}",
                "1",
                ex=24 * 3600,
                nx=True,
            )
            if not ok:
                return False
        except Exception:
            r = None  # redis 出错降级，交给数据库

    db.add(models.ReminderJob(
        document_id=document_id, rule_id=rule_id, remind_on=remind_on, status="PENDING"
    ))
    db.flush()
    return True