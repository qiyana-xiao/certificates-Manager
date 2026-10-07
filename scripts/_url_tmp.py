# -*- coding: utf-8 -*-
import pymysql
c = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='123456', database='doc_keeper', charset='utf8mb4')
cur = c.cursor()
cur.execute("SELECT code,name,portal_name,portal_url FROM provinces WHERE portal_url IS NULL OR portal_url='' ORDER BY sort")
rows = cur.fetchall()
print('缺失portal_url的省份数:', len(rows))
for r in rows:
    print(r[0], r[1], '||', r[2], '||', r[3])
print('--- 已有portal_url的省份 ---')
cur.execute("SELECT code,name,portal_name,portal_url FROM provinces WHERE portal_url IS NOT NULL AND portal_url!='' ORDER BY sort")
for r in cur.fetchall():
    print(r[0], r[1], '||', r[3])
c.close()