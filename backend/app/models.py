# -*- coding: utf-8 -*-
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Province(Base):
    __tablename__ = "provinces"
    code: Mapped[str] = mapped_column(String(8), primary_key=True)
    name: Mapped[str] = mapped_column(String(20))
    jtw_code: Mapped[str] = mapped_column(String(8), default="")
    portal_name: Mapped[str] = mapped_column(String(60), default="")
    portal_url: Mapped[str] = mapped_column(String(200), default="")
    region_type: Mapped[str] = mapped_column(String(20), default="省")  # 直辖市/省/自治区/特别行政区
    sort: Mapped[int] = mapped_column(Integer, default=0)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(300))
    role: Mapped[str] = mapped_column(String(20), default="user")
    province_code: Mapped[str | None] = mapped_column(String(8), nullable=True)
    default_timezone: Mapped[str] = mapped_column(String(50), default="Asia/Shanghai")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    documents: Mapped[list["MyDocument"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


class DocumentType(Base):
    __tablename__ = "document_types"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(60))
    issuer: Mapped[str] = mapped_column(String(100), default="")
    icon: Mapped[str] = mapped_column(String(20), default="🪪")
    default_ahead_days: Mapped[list] = mapped_column(JSON, default=list)
    valid_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    desc: Mapped[str] = mapped_column(String(300), default="")


class RenewalGuide(Base):
    __tablename__ = "renewal_guides"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_type_id: Mapped[int] = mapped_column(
        ForeignKey("document_types.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(120))
    region_code: Mapped[str | None] = mapped_column(String(8), nullable=True, index=True)
    link_mode: Mapped[str] = mapped_column(String(20), default="FIXED")
    materials: Mapped[list] = mapped_column(JSON, default=list)
    location: Mapped[str] = mapped_column(Text, default="")
    fee: Mapped[str] = mapped_column(String(300), default="")
    duration: Mapped[str] = mapped_column(String(200), default="")
    official_url: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(200), default="")
    updated_at: Mapped[date] = mapped_column(Date, default=date.today)
    disclaimer: Mapped[str] = mapped_column(
        String(200), default="以当地窗口实际要求为准，办理前请核实最新政策。"
    )


class MyDocument(Base):
    __tablename__ = "my_documents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    document_type_id: Mapped[int | None] = mapped_column(
        ForeignKey("document_types.id"), nullable=True
    )
    member_id: Mapped[int | None] = mapped_column(
        ForeignKey("family_members.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(80))
    doc_number_cipher: Mapped[str] = mapped_column(String(500), default="")
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expire_date: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(
        String(20), default="VALID"
    )  # VALID / EXPIRING / EXPIRED / ARCHIVED
    note: Mapped[str] = mapped_column(String(300), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    owner: Mapped["User"] = relationship(back_populates="documents")
    rules: Mapped[list["ReminderRule"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class ReminderRule(Base):
    __tablename__ = "reminder_rules"
    __table_args__ = (UniqueConstraint("document_id", "ahead_days"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("my_documents.id"), index=True
    )
    ahead_days: Mapped[int] = mapped_column(Integer)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    document: Mapped["MyDocument"] = relationship(back_populates="rules")


class ReminderJob(Base):
    __tablename__ = "reminder_jobs"
    __table_args__ = (UniqueConstraint("document_id", "rule_id", "remind_on"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("my_documents.id"), index=True
    )
    rule_id: Mapped[int] = mapped_column(ForeignKey("reminder_rules.id"))
    remind_on: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")  # PENDING/DONE
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AppNotification(Base):
    """到点后每天一次的"日常弹窗"记录：同一条提醒(job)每天只弹一次。

    status: PENDING=待弹窗 / DISMISSED=当天已忽略 / DONE=已处理。
    证件被处理(归档/续办/删除)或提醒被结清后，job 变为 DONE，"每日弹窗"随之停更。
    """

    __tablename__ = "app_notifications"
    __table_args__ = (UniqueConstraint("job_id", "notify_date"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("reminder_jobs.id", ondelete="CASCADE"), index=True
    )
    document_id: Mapped[int] = mapped_column(
        ForeignKey("my_documents.id", ondelete="CASCADE"), index=True
    )
    document_title: Mapped[str] = mapped_column(String(80), default="")
    content: Mapped[str] = mapped_column(Text, default="")
    notify_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class FamilyMember(Base):
    __tablename__ = "family_members"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    host_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    member_name: Mapped[str] = mapped_column(String(40))
    member_color: Mapped[str] = mapped_column(String(20), default="#3b82f6")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ExportLog(Base):
    __tablename__ = "export_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    scope: Mapped[str] = mapped_column(String(40), default="all")
    file_hash: Mapped[str] = mapped_column(String(80), default="")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(60))
    target: Mapped[str] = mapped_column(String(120), default="")
    detail: Mapped[str] = mapped_column(Text, default="")
    time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SystemConfig(Base):
    __tablename__ = "system_configs"
    key: Mapped[str] = mapped_column(String(60), primary_key=True)
    value: Mapped[str] = mapped_column(String(300), default="")