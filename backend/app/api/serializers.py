from __future__ import annotations

from app.models.statement import Statement
from app.schemas import StatementOut


def statement_out(stmt: Statement, count: int = 0) -> StatementOut:
    return StatementOut(
        id=stmt.id,
        bank=stmt.bank,
        card_label=stmt.card_label,
        period_start=stmt.period_start,
        period_end=stmt.period_end,
        total_amount=stmt.total_amount,
        source_filename=stmt.source_filename,
        file_hash=stmt.file_hash,
        status=stmt.status,
        created_at=stmt.created_at,
        transaction_count=count,
    )
