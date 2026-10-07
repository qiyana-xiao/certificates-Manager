# -*- coding: utf-8 -*-
"""创建管理员账号（用于"指南维护"）。
用法：python scripts/create_admin.py <用户名> <密码>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app import models
from app.database import SessionLocal
from app.security import hash_password


def main():
    if len(sys.argv) < 3:
        print("用法：python scripts/create_admin.py <用户名> <密码>")
        sys.exit(1)
    username, password = sys.argv[1], sys.argv[2]
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.username == username).first()
        if user:
            user.password_hash = hash_password(password)
            user.role = "admin"
            db.commit()
            print(f"已把既有用户「{username}」提升为管理员。")
        else:
            db.add(models.User(username=username, password_hash=hash_password(password), role="admin"))
            db.commit()
            print(f"已创建管理员「{username}」。")
    finally:
        db.close()


if __name__ == "__main__":
    main()