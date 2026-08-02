from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models.category import Category
from app.models.statement import Statement
from app.models.transaction import Transaction
from app.schemas import CategoryBreakdown, DashboardSummary, StatementOut, TransactionOut
from app.services.dates import InvalidMonthFormatError, month_bounds

router = APIRouter()


def _statement_out(stmt: Statement, count: int = 0) -> StatementOut:
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


def _build_breakdown(
    txs: List[Transaction],
    categories: Dict[int, Category],
    uncategorized_id: Optional[int],
) -> tuple[float, int, int, list[CategoryBreakdown]]:
    totals: Dict[Optional[int], dict] = defaultdict(
        lambda: {"total": 0.0, "count": 0, "name": "Sem categoria", "color": "#9CA3AF"}
    )
    spent = 0.0
    uncategorized_count = 0
    positive_count = 0

    for tx in txs:
        if tx.amount <= 0:
            continue
        amount = abs(tx.amount)
        spent += amount
        positive_count += 1
        cat_id = tx.category_id
        if cat_id in categories:
            totals[cat_id]["name"] = categories[cat_id].name
            totals[cat_id]["color"] = categories[cat_id].color
        totals[cat_id]["total"] += amount
        totals[cat_id]["count"] += 1
        if cat_id is None or cat_id == uncategorized_id:
            uncategorized_count += 1

    by_category = [
        CategoryBreakdown(
            category_id=cat_id,
            name=data["name"],
            color=data["color"],
            total=round(data["total"], 2),
            count=data["count"],
        )
        for cat_id, data in sorted(
            totals.items(), key=lambda x: x[1]["total"], reverse=True
        )
    ]
    return spent, positive_count, uncategorized_count, by_category


@router.get("/dashboard", response_model=DashboardSummary)
def dashboard_summary(
    month: Optional[str] = Query(None, description="YYYY-MM"),
    db: Session = Depends(get_db),
) -> DashboardSummary:
    if not month:
        today = date.today()
        month = f"{today.year:04d}-{today.month:02d}"
    try:
        start, end = month_bounds(month)
    except InvalidMonthFormatError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Prefer billing-cycle view: statements whose due/close date falls in this month
    billing_statements = list(
        db.scalars(
            select(Statement)
            .where(Statement.period_end.is_not(None))
            .where(Statement.period_end >= start, Statement.period_end < end)
            .order_by(Statement.period_end.desc())
        ).all()
    )

    view_mode = "billing" if billing_statements else "calendar"
    statement_outs: list[StatementOut] = []

    if view_mode == "billing":
        stmt_ids = [s.id for s in billing_statements]
        txs = list(
            db.scalars(
                select(Transaction)
                .options(joinedload(Transaction.category))
                .where(Transaction.statement_id.in_(stmt_ids))
                .order_by(Transaction.date.desc(), Transaction.id.desc())
            )
            .unique()
            .all()
        )
        for stmt in billing_statements:
            count = sum(1 for t in txs if t.statement_id == stmt.id)
            statement_outs.append(_statement_out(stmt, count))
        invoice_total = round(sum(s.total_amount for s in billing_statements), 2)
    else:
        # Calendar fallback: only txs not already tied to a bill with a due date
        billed_stmt_ids = list(
            db.scalars(
                select(Statement.id).where(Statement.period_end.is_not(None))
            ).all()
        )
        query = (
            select(Transaction)
            .options(joinedload(Transaction.category))
            .where(Transaction.date >= start, Transaction.date < end)
            .order_by(Transaction.date.desc(), Transaction.id.desc())
        )
        if billed_stmt_ids:
            query = query.where(Transaction.statement_id.not_in(billed_stmt_ids))
        txs = list(db.scalars(query).unique().all())
        invoice_total = None

    uncategorized = db.scalar(
        select(Category).where(Category.name == "Não categorizado")
    )
    uncategorized_id = uncategorized.id if uncategorized else None
    categories = {c.id: c for c in db.scalars(select(Category)).all()}

    charges_total, positive_count, uncategorized_count, by_category = _build_breakdown(
        txs, categories, uncategorized_id
    )

    # In billing mode the headline matches the PDF "Total desta fatura"
    total_spent = invoice_total if invoice_total is not None else round(charges_total, 2)

    recent = [TransactionOut.model_validate(tx) for tx in txs[:80]]

    return DashboardSummary(
        month=month,
        total_spent=total_spent if total_spent is not None else 0.0,
        charges_total=round(charges_total, 2),
        invoice_total=invoice_total,
        view_mode=view_mode,
        transaction_count=positive_count,
        uncategorized_count=uncategorized_count,
        by_category=by_category,
        recent_transactions=recent,
        statements=statement_outs,
    )
