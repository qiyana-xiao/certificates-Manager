# -*- coding: utf-8 -*-
"""迁移省级地区数据：补齐 region_type 列 + 回填 + 移除台湾省/港澳 3 个地区。
产品只收 31 个大陆省级行政区（23省+4直辖市+5自治区），港澳台不收录。
幂等且安全：列不存在才 ADD，region_type 仅更新为空的旧行，删除 3 个地区幂等（不存在也不报错）。
用法：python scripts/migrate_provinces.py
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / "backend" / ".env"

# code -> region_type
REGION_TYPES = {
    "BJ": "直辖市", "SH": "直辖市", "CQ": "直辖市", "TJ": "直辖市",
    "NM": "自治区", "GX": "自治区", "XZ": "自治区", "NX": "自治区", "XJ": "自治区",
    # 其余地区均为 省，对应列默认即 '省'
}
# 需移除的地区（上一版曾补入台湾省/港澳，本版改为不收录并删除存量）
REMOVE = {"TW", "HK", "MO"}


def load_env():
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())


def main():
    load_env()
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = int(os.getenv("DB_PORT", "3306"))
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    dbname = os.getenv("DB_NAME", "doc_keeper")

    import pymysql  # noqa: PLC0415
    conn = pymysql.connect(host=host, port=port, user=user, password=password,
                           database=dbname, charset="utf8mb4")
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA=%s AND TABLE_NAME='provinces' AND COLUMN_NAME='region_type'",
                (dbname,),
            )
            if cur.fetchone()[0] == 0:
                cur.execute(
                    "ALTER TABLE `provinces` ADD COLUMN `region_type` VARCHAR(20) "
                    "NOT NULL DEFAULT '省' COMMENT '直辖市/省/自治区/特别行政区' AFTER `portal_url`"
                )
                print("[migrate] 已新增 provinces.region_type 列")
            else:
                print("[migrate] provinces.region_type 列已存在，跳过")

            # 回填旧行的 region_type
            for code, rt in REGION_TYPES.items():
                cur.execute("UPDATE `provinces` SET `region_type`=%s WHERE `code`=%s AND `region_type`='省'" if rt != "省" else
                            "UPDATE `provinces` SET `region_type`=%s WHERE `code`=%s", (rt, code))

            # 移除台湾省/港澳 3 个地区（幂等）
            phs = ",".join(["%s"] * len(REMOVE))
            cur.execute(f"SELECT name FROM `provinces` WHERE `code` IN ({phs})", tuple(REMOVE))
            removed = [r[0] for r in cur.fetchall()]
            cur.execute(f"DELETE FROM `provinces` WHERE `code` IN ({phs})", tuple(REMOVE))
            if removed:
                print(f"[migrate] 已移除不收录地区：{'、'.join(removed)}")
            else:
                print("[migrate] 无需移除（台湾省/港澳已不在表中）")

            cur.execute("SELECT COUNT(*) FROM `provinces`")
            total = cur.fetchone()[0]
            print(f"[migrate] 当前省级地区总数 = {total}（31 = 23省 + 4直辖市 + 5自治区）")
        conn.commit()
        print("[migrate] 完成")
    except Exception as exc:  # noqa: BLE001
        print(f"[migrate] 失败：{exc}")
        sys.exit(2)
    finally:
        conn.close()


if __name__ == "__main__":
    main()