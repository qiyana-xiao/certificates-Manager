# -*- coding: utf-8 -*-
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .database import SessionLocal
from .routers import auth, calendar, documents, export_routers, family, guides, health, regions, reminders

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


async def _reminder_loop():
    """进程内定时扫提醒，每分钟一次；Redis 不可用由数据库唯一索引兜底。"""
    from .services import reminder_engine

    while True:
        try:
            db = SessionLocal()
            try:
                reminder_engine.scan_once(db)
            finally:
                db.close()
        except Exception as exc:  # noqa: BLE001
            logging.getLogger("doc-keeper.reminder").warning("reminder scan error: %s", exc)
        await asyncio.sleep(config.REMINDER_SCAN_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_reminder_loop())
    try:
        yield
    finally:
        task.cancel()


app = FastAPI(title="证件管家 Doc Keeper", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(calendar.router)
app.include_router(reminders.router)
app.include_router(guides.router)
app.include_router(regions.router)
app.include_router(family.router)
app.include_router(export_routers.router)