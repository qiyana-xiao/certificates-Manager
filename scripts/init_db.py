# -*- coding: utf-8 -*-
"""初始化数据库：建库 + 建表 + （仅在空库时）灌入种子（省份、证件类型、续办指南）。

默认幂等且安全：库/表不存在才创建，绝不删除已有数据——多次运行不丢任何用户档案。
彻底重置（清空一切）仅当显式传 --reset：python scripts/init_db.py --reset   （慎用）
读取 backend\\.env 中的 DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME。
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / "backend" / ".env"
SCHEMA = ROOT / "database" / "sql" / "01_schema.sql"
SEED = ROOT / "database" / "sql" / "02_seed.sql"


def load_env():
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())


def main():
    do_reset = "--reset" in sys.argv[1:]
    load_env()
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = int(os.getenv("DB_PORT", "3306"))
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    dbname = os.getenv("DB_NAME", "doc_keeper")

    try:
        import pymysql
    except ImportError:
        print("[init_db] 缺少 pymysql，请先在 backend 虚拟环境中安装依赖。")
        sys.exit(1)

    for label, path in (("schema", SCHEMA), ("seed", SEED)):
        if not path.exists():
            print(f"[init_db] 找不到 {label} 文件：{path}")
            sys.exit(1)

    if do_reset:
        print(f"[init_db] 收到 --reset：正在清空数据库 {dbname}（将丢失全部数据）...")
        conn = pymysql.connect(host=host, port=port, user=user, password=password, charset="utf8mb4")
        try:
            with conn.cursor() as cur:
                cur.execute(f"DROP DATABASE IF EXISTS `{dbname}`")
            conn.commit()
        finally:
            conn.close()

    conn = pymysql.connect(
        host=host, port=port, user=user, password=password, charset="utf8mb4",
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{dbname}` "
                "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.commit()
    finally:
        conn.close()

    print(f"[init_db] 已连接 MySQL {host}:{port}，库 {dbname}，执行 schema（只建不删）...")

    conn = pymysql.connect(
        host=host, port=port, user=user, password=password, database=dbname, charset="utf8mb4",
    )
    try:
        with conn.cursor() as cur:
            for stmt in _split(SCHEMA.read_text(encoding="utf-8")):
                if stmt.strip():
                    cur.execute(stmt)

            # 幂等播种：仅当证件类型表为空才补种子，避免重复插入、避免覆盖用户数据
            cur.execute("SELECT COUNT(*) FROM document_types")
            seeded = cur.fetchone()[0] > 0
            if not seeded:
                for stmt in _split(SEED.read_text(encoding="utf-8")):
                    if stmt.strip():
                        cur.execute(stmt)
                print("[init_db] 已完成种子数据（省份 / 证件类型 / 续办指南）。")
            else:
                print("[init_db] 检测到已有种子数据，跳过补种（用户档案不受影响）。")
        conn.commit()
        print("[init_db] 完成：库与表就绪。")
    except Exception as exc:  # noqa: BLE001
        print(f"[init_db] 执行失败：{exc}")
        sys.exit(2)
    finally:
        conn.close()


def _split(sql: str):
    stmts, buf = [], []
    for line in sql.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("--"):
            continue
        if stripped.lower().startswith("delimiter"):
            continue
        buf.append(line)
        if stripped.endswith(";"):
            stmts.append("\n".join(buf))
            buf = []
    return [s for s in stmts if s.strip()]


if __name__ == "__main__":
    main()