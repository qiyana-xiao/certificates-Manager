# -*- coding: utf-8 -*-
"""认证与加密：JWT 签发/校验、Argon2 密码哈希、AES-256-GCM 敏感字段加密。"""
import base64
import os
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from . import config

_ph = PasswordHasher()


def hash_password(plain: str) -> str:
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, plain)
    except Exception:
        return False


def _now_utc():
    return datetime.now(timezone.utc)


def create_access_token(user_id: int, username: str, role: str) -> str:
    now = _now_utc()
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=config.JWT_ACCESS_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    now = _now_utc()
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(days=config.JWT_REFRESH_EXPIRE_DAYS),
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
    except Exception:
        return None


def _enc_key_bytes() -> bytes:
    return base64.b64decode(config.ENC_KEY)


def _encryption_enabled() -> bool:
    return bool(config.ENC_KEY)


def encrypt_value(plain: str) -> str:
    """返回 Base64(nonce + ciphertext)。未配置 ENC_KEY 时原样返回（不启用加密）。"""
    if not plain or not _encryption_enabled():
        return plain
    aesgcm = AESGCM(_enc_key_bytes())
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plain.encode("utf-8"), None)
    return base64.b64encode(nonce + ct).decode("utf-8")


def decrypt_value(token: str) -> str:
    if not token or not _encryption_enabled():
        return token
    raw = base64.b64decode(token)
    nonce, ct = raw[:12], raw[12:]
    aesgcm = AESGCM(_enc_key_bytes())
    return aesgcm.decrypt(nonce, ct, None).decode("utf-8")


def mask_number(plain: str) -> str:
    """身份证/账号等脱敏：保留前6后4，其余打星。短号码直接打码。"""
    if not plain:
        return ""
    if len(plain) <= 8:
        return plain[:2] + "*" * (len(plain) - 2)
    return plain[:6] + "*" * (len(plain) - 10) + plain[-4:]