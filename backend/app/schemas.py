# -*- coding: utf-8 -*-
from datetime import date

from pydantic import BaseModel, Field


class RegisterIn(BaseModel):
    username: str = Field(min_length=2, max_length=20)
    password: str = Field(min_length=8, max_length=64)


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    province_code: str | None = None

    class Config:
        from_attributes = True


class ProfileIn(BaseModel):
    province_code: str | None = Field(default=None, max_length=8)


class ProvinceOut(BaseModel):
    code: str
    name: str
    jtw_code: str = ""
    portal_name: str = ""
    portal_url: str = ""
    region_type: str = "省"

    class Config:
        from_attributes = True


class DocumentTypeOut(BaseModel):
    id: int
    code: str
    name: str
    icon: str
    issuer: str
    default_ahead_days: list[int] = []
    valid_years: int | None = None
    desc: str = ""

    class Config:
        from_attributes = True


class ReminderRuleIn(BaseModel):
    ahead_days: int = Field(ge=0, le=3650)
    enabled: bool = True


class DocumentIn(BaseModel):
    document_type_id: int | None = None
    member_id: int | None = None
    title: str = Field(min_length=1, max_length=80)
    doc_number: str = Field(default="", max_length=64)
    expire_date: date | None = None
    start_date: date | None = None
    valid_years: int | None = Field(default=None, ge=1, le=60)
    note: str = Field(default="", max_length=300)

    def resolve_expire_date(self) -> date | None:
        if self.expire_date:
            return self.expire_date
        if self.start_date and self.valid_years:
            from .services.expiry_calc import compute_expire_date

            return compute_expire_date(self.start_date, self.valid_years)
        return None


class DocumentOut(BaseModel):
    id: int
    document_type_id: int | None
    member_id: int | None
    member_name: str = ""
    member_color: str = ""
    type_name: str = ""
    type_icon: str = "🪪"
    title: str
    doc_number_masked: str = ""
    start_date: date | None = None
    valid_years: int | None = None
    expire_date: date
    days_left: int
    status: str
    note: str = ""

    class Config:
        from_attributes = True


class ReminderOut(BaseModel):
    id: int
    document_id: int
    doc_title: str
    type_name: str = ""
    type_icon: str = "🪪"
    expire_date: date
    remind_on: date
    days_left: int
    ahead_days: int
    status: str

    class Config:
        from_attributes = True


LINK_MODES = ("FIXED", "PROVINCE_PORTAL", "PROVINCE_JTW")


class GuideIn(BaseModel):
    document_type_id: int
    title: str
    region_code: str | None = Field(default=None, max_length=8)
    link_mode: str = "FIXED"
    materials: list[str] = []
    location: str = ""
    fee: str = ""
    duration: str = ""
    official_url: str = ""
    source: str = Field(min_length=1)
    updated_at: date | None = None
    disclaimer: str = "以当地窗口实际要求为准，办理前请核实最新政策。"


class GuideOut(BaseModel):
    id: int
    document_type_id: int
    type_name: str = ""
    type_icon: str = "🪪"
    title: str
    region_code: str | None = None
    region_name: str = ""
    link_mode: str = "FIXED"
    materials: list[str] = []
    location: str = ""
    fee: str = ""
    duration: str = ""
    official_url: str = ""
    source: str = ""
    updated_at: date | None = None
    disclaimer: str = ""

    class Config:
        from_attributes = True


class FamilyMemberIn(BaseModel):
    member_name: str = Field(min_length=1, max_length=40)
    member_color: str = "#3b82f6"


class FamilyMemberOut(BaseModel):
    id: int
    member_name: str
    member_color: str
    doc_count: int = 0

    class Config:
        from_attributes = True