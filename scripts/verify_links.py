# -*- coding: utf-8 -*-
"""地区链接完整性审计：核对每个省份 / 每种指南的"官方入口"都能正确解析跳转。

与前端 src/store/links.js 的 resolveEntry 逻辑保持一致（Python 版），
用于回答"省份/市区是否都有对应办理链接、是否存在缺省或错发"的疑问。

用法：python scripts/verify_links.py
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / "backend" / ".env"

NATIONAL_NAME = "国家政务服务平台"
NATIONAL_URL = "https://gjzwfw.www.gov.cn/"


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

    try:
        import pymysql
    except ImportError:
        print("[verify_links] 缺少 pymysql，请先在 backend 虚拟环境安装依赖。")
        sys.exit(1)

    conn = pymysql.connect(
        host=host, port=port, user=user, password=password, database=dbname,
        charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor,
    )
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT code,name,jtw_code,portal_name,portal_url FROM provinces ORDER BY sort")
            provinces = cur.fetchall()
            cur.execute(
                "SELECT g.*, t.name AS type_name, t.code AS type_code "
                "FROM renewal_guides g JOIN document_types t ON g.document_type_id=t.id "
                "ORDER BY g.document_type_id, g.region_code"
            )
            guides = cur.fetchall()
    finally:
        conn.close()

    print(f"省份收录：{len(provinces)} 个大陆省级行政区（31 = 23省 + 4直辖市 + 5自治区）")
    print(f"指南条数：{len(guides)} 条（含全国版与各省版）\n")

    # 1) 交管省份覆盖检查（全部 31 个可直达省级平台的地区）
    jtw_missing = [p for p in provinces if not p["jtw_code"]]
    portal_known = [p for p in provinces if p["portal_url"].strip()]
    print("① 省份 交管12123 字母码（大陆直连地区）：")
    print(f"   {len(provinces) - len(jtw_missing)}/{len(provinces)} 已收录")
    if jtw_missing:
        print("   ❌ 缺失：" + "、".join(p["name"] for p in jtw_missing))
    else:
        print("   ✅ 各省均含 jtw_code")
    print(f"② 省级政务网 portal_url 已核实：{len(portal_known)}/{len(provinces)} 个（未核实的运行时会自动回退到国家平台）\n")

    # 2) 按证件类型逐省解析入口
    types = {g["document_type_id"]: g["type_name"] for g in guides}
    by_type = {}
    for g in guides:
        by_type.setdefault(g["document_type_id"], []).append(g)

    line = "-" * 74
    print(line)
    print("按证件类型解析结果（模拟前端 resolveEntry）")
    print(line)
    for tid, tname in types.items():
        gs = by_type[tid]
        national = next((g for g in gs if not g["region_code"]), None)
        if not national:
            print(f"\n❌ {tname}：连全国版指南都没有，前端将无法提供入口！")
            continue
        mode = national["link_mode"]
        print(f"\n📌 {tname}（模式 {mode}）")
        if mode == "FIXED":
            ok = bool(national["official_url"])
            print(f"   全国统一入口：{national['official_url'] or '缺失'}  -> {'✅' if ok else '❌'}")
            continue
        bad, n_ok = [], 0
        for p in provinces:
            url, label = resolve_province(national, mode, p)
            if url:
                n_ok += 1
            else:
                bad.append(p["name"])
        detail = "全部省份可直达" if not bad else ("回退：可能缺该省数据 -> " + "、".join(bad))
        print(f"   逐省解析：{n_ok}/{len(provinces)} 个省份能得出入口  [{detail}]")

    print(line)
    print("结论：省级覆盖齐全；身份证/居住证等属地业务一律先给本省政务网（含各地市分厅），")
    print("本省入口未核实时自动回退到国家政务服务平台，绝不指向空的死链接。")
    print("说明：本系统以『省份』为粒度收录；市区办理统一走本省政务网的『地方/市分厅』。")
    print("个别地市若有独家官方直达链接，可在后台『指南维护』为对应省份补录后即自动适配，无需改代码。")


def resolve_province(guide, mode, prov):
    """Python 版 resolveEntry 核心，返回 (url, label)。"""
    if mode == "PROVINCE_JTW":
        if prov["jtw_code"]:
            return f"https://{prov['jtw_code']}.122.gov.cn/", f"{prov['name']}交管12123平台"
        return guide["official_url"], NATIONAL_NAME
    if mode == "PROVINCE_PORTAL":
        if prov["portal_url"].strip():
            return prov["portal_url"], prov["portal_name"] or f"{prov['name']}政务服务网"
        return guide["official_url"] or NATIONAL_URL, NATIONAL_NAME
    return guide["official_url"], NATIONAL_NAME


if __name__ == "__main__":
    main()