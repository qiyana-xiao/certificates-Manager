# -*- coding: utf-8 -*-
import json
import urllib.request
from datetime import date

base = "http://127.0.0.1:8000"


def req(method, path, body=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body else None
    r = urllib.request.Request(base + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(r, timeout=10) as resp:
        return json.load(resp)


tok = req("POST", "/api/auth/login", {"username": "demouser", "password": "pass1234"})["access_token"]

# 一张 7 天后到期的卡（默认档位 90/30/7 -> 今天应命中 7 天档）
exp = (date.today().isoformat())
# expire_date 传 today+7
import datetime
exp7 = (datetime.date.today() + datetime.timedelta(days=7)).isoformat()
d = req("POST", "/api/documents", {"document_type_id": 8, "title": "健身房年卡", "doc_number": "VIP999", "expire_date": exp7}, tok)
print("创建年卡 ->", d["title"], "到期", d["expire_date"], "剩余", d["days_left"], "天")

# 直接用服务跑一次扫描
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import SessionLocal
from app.services import reminder_engine

# 复用应用会话
db = SessionLocal()
try:
    n = reminder_engine.scan_once(db, datetime.date.today())
    print("本次扫描新建提醒 =", n)
    again = reminder_engine.scan_once(db, datetime.date.today())
    print("再扫一次(应幂等=0) =", again)
finally:
    db.close()

# 通过 API 查看提醒收件箱
rem = req("GET", "/api/reminders", token=tok)
print("提醒收件箱:")
for r in rem:
    print("  -", r["doc_title"], "| 提前", r["ahead_days"], "天 | 应发", r["remind_on"], "| 状态", r["status"])