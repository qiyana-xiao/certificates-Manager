# -*- coding: utf-8 -*-
import json
import urllib.request

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

d = req(
    "POST",
    "/api/documents",
    {
        "document_type_id": 2,
        "title": "我的驾驶证",
        "doc_number": "610100199201019876",
        "start_date": "2020-01-01",
        "valid_years": 6,
    },
    tok,
)
print("创建证件 ->", d["title"], "|", d["type_name"], "| 到期", d["expire_date"], "| 掩码", d["doc_number_masked"])

docs = req("GET", "/api/documents", token=tok)
print("文档数 =", len(docs), "| 第一条标题 =", docs[0]["title"])

guides = req("GET", "/api/guides", token=tok)
print("指南数 =", len(guides), "| 首条 =", guides[0]["title"], "| 费用 =", guides[0]["fee"])

dash = req("GET", "/api/dashboard", token=tok)
print("首页统计 =", dash)