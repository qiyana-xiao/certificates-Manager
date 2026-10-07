# -*- coding: utf-8 -*-
import pymysql
c = pymysql.connect(host="127.0.0.1", port=3306, user="root", password="123456", database="doc_keeper", charset="utf8mb4")
cur = c.cursor()
cur.execute("SELECT id, code, name FROM document_types")
print("证件类型:", cur.fetchall())
# 给测试证补上 document_type_id（护照/驾驶证均为常见类型，按 code 匹配）
cur.execute("SELECT id FROM document_types WHERE code='passport'"); ps = cur.fetchone()
cur.execute("SELECT id FROM document_types WHERE code='driving_license'"); dr = cur.fetchone()
pw = ('UPDATE my_documents SET document_type_id=%s WHERE id=22', (ps[0],)) if ps else None
dr2 = ('UPDATE my_documents SET document_type_id=%s WHERE id=20', (dr[0],)) if dr else None
for sql, v in (pw, dr2):
    if sql: cur.execute(sql, v)
c.commit()
cur.execute("SELECT id,title,document_type_id FROM my_documents WHERE id IN (20,22)")
print("更新后:", cur.fetchall())
c.close()