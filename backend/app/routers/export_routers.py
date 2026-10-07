# -*- coding: utf-8 -*-
import csv
import hashlib
import io
from datetime import datetime

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, security
from ..deps import get_current_user, get_db
from ..services import expiry_calc

router = APIRouter(prefix="/api", tags=["export"])


@router.post("/export")
def export_csv(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    docs = db.execute(
        select(models.MyDocument).where(models.MyDocument.user_id == user.id)
    ).scalars().all()
    types = {t.id: t for t in db.execute(select(models.DocumentType)).scalars().all()}
    members = {m.id: m for m in db.execute(select(models.FamilyMember)).scalars().all()}

    buf = io.StringIO()
    buf.write("\ufeff")  # BOM，Excel 打开不乱码
    writer = csv.writer(buf)
    writer.writerow(["证件", "类型", "归属成员", "号码(脱敏)", "开始日期", "有效年限", "到期日", "剩余天数", "状态", "备注"])
    for d in docs:
        type_name = types[d.document_type_id].name if d.document_type_id in types else ""
        member_name = members[d.member_id].member_name if d.member_id in members else ""
        masked = security.mask_number(security.decrypt_value(d.doc_number_cipher))
        writer.writerow(
            [
                d.title,
                type_name,
                member_name,
                masked,
                d.start_date.isoformat() if d.start_date else "",
                d.valid_years or "",
                d.expire_date.isoformat(),
                expiry_calc.days_left(d.expire_date),
                d.status,
                d.note,
            ]
        )
    csv_data = buf.getvalue()
    file_hash = hashlib.sha256(csv_data.encode("utf-8")).hexdigest()[:16]
    db.add(models.ExportLog(user_id=user.id, scope="all", file_hash=file_hash))
    db.commit()
    filename = f"doc-keeper-{datetime.now():%Y%m%d-%H%M%S}.csv"
    return Response(
        csv_data,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )