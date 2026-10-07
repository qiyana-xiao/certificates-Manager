# -*- coding: utf-8 -*-
"""到期计算：唯一负责"今天 / 剩余天数 / 状态"的口径，避免各处在多处重复。"""
from datetime import date, timedelta

VALID = "VALID"
EXPIRING = "EXPIRING"
EXPIRED = "EXPIRED"
ARCHIVED = "ARCHIVED"

# 触发"临期"显示的提前天数阈值（仅用于展示分级）
EXPIRING_THRESHOLD = 90


def days_left(expire_date: date, today: date | None = None) -> int:
    today = today or date.today()
    return (expire_date - today).days


def status_of(expire_date: date, today: date | None = None) -> str:
    d = days_left(expire_date, today)
    if d < 0:
        return EXPIRED
    if d <= EXPIRING_THRESHOLD:
        return EXPIRING
    return VALID


def add_years(anchor: date, years: int) -> date:
    """在 anchor 上加若干年，正确处理闰年 2/29。"""
    try:
        return date(anchor.year + years, anchor.month, anchor.day)
    except ValueError:
        return date(anchor.year + years, 2, 28)


def compute_expire_date(start_date: date, valid_years: int) -> date:
    """起始日 + N 年 -> 到期日（到期日一般为起始日的 N 年纪念日）。"""
    return add_years(start_date, valid_years)