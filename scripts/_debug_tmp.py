# -*- coding: utf-8 -*-
import pymysql
c = pymysql.connect(host="127.0.0.1", port=3306, user="root", password="123456", database="doc_keeper", charset="utf8mb4")
cur = c.cursor()
cur.execute("SELECT id, title, doc_number_cipher, expire_date, document_type_id FROM my_documents WHERE id IN (20,21,22,23)")
print("证件原文:")
for r in cur.fetchall():
    print("  id=%s title=[%s] docno=[%s] document_type_id=%s" % (r[0], r[1], r[2], r[4],))
cur.execute("SELECT id, document_type_id, title, link_mode, region_code, official_url, portal_name FROM renewal_guides")
print("\n指南:")
for r in cur.fetchall():
    print("  id=%s type=%s mode=%s region=%s url=[%s] name=[%s]" % (r[0], r[1], r[3], r[4], r[5], r[6]))
c.close()