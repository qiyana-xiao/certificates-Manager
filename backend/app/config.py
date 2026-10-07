# -*- coding: utf-8 -*-
"""证件管家后端配置：从 backend/.env 读取，未配置时使用默认值。"""
import os
from pathlib import Path

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


def _load_dotenv():
    if not _ENV_FILE.exists():
        return
    for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip())


_load_dotenv()


def _get(key: str, default: str = "") -> str:
    return os.getenv(key, default)


DB_USER = _get("DB_USER", "root")
DB_PASSWORD = _get("DB_PASSWORD", "")
DB_HOST = _get("DB_HOST", "127.0.0.1")
DB_PORT = _get("DB_PORT", "3306")
DB_NAME = _get("DB_NAME", "doc_keeper")
DATABASE_URL = _get(
    "DATABASE_URL",
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4",
)

REDIS_URL = _get(
    "REDIS_URL",
    f"redis://{_get('REDIS_HOST', '127.0.0.1')}:{_get('REDIS_PORT', '6379')}/0",
)

JWT_SECRET = _get("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_EXPIRE_MINUTES = int(_get("JWT_ACCESS_EXPIRE_MINUTES", "60"))
JWT_REFRESH_EXPIRE_DAYS = int(_get("JWT_REFRESH_EXPIRE_DAYS", "7"))

ENC_KEY = _get("ENC_KEY", "")

APP_PORT = int(_get("APP_PORT", "8000"))
CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in _get(
        "CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if o.strip()
]
DEFAULT_TZ = _get("DEFAULT_TZ", "Asia/Shanghai")

REMINDER_SCAN_INTERVAL_SECONDS = int(_get("REMINDER_SCAN_INTERVAL_SECONDS", "60"))