from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    color: str
    keywords: str


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    keywords: Optional[str] = None


class MerchantRuleCreate(BaseModel):
    pattern: str
    category_id: int


class MerchantRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pattern: str
    category_id: int


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    statement_id: int
    date: date
    description: str
    amount: float
    installment: Optional[str] = None
    category_id: Optional[int] = None
    category: Optional[CategoryOut] = None


class TransactionUpdate(BaseModel):
    category_id: Optional[int] = None
    remember_rule: bool = False
    rule_pattern: Optional[str] = None


class StatementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bank: str
    card_label: Optional[str] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    total_amount: float
    source_filename: str
    file_hash: str
    status: str
    created_at: datetime
    transaction_count: int = 0


class StatementDetail(StatementOut):
    transactions: list[TransactionOut] = Field(default_factory=list)


class CategoryBreakdown(BaseModel):
    category_id: Optional[int]
    name: str
    color: str
    total: float
    count: int


class DashboardSummary(BaseModel):
    month: str
    total_spent: float
    transaction_count: int
    uncategorized_count: int
    by_category: list[CategoryBreakdown]
    recent_transactions: list[TransactionOut]


class UploadResult(BaseModel):
    statement: StatementOut
    message: str


class InboxStatus(BaseModel):
    inbox_dir: str
    pending_pdfs: list[str]
    processed_count: int
