from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models.category import Category
from app.models.transaction import Transaction
from app.schemas import CategoryBreakdown, DashboardSummary, TransactionOut
from app.services.dates import InvalidMonthFormatError, month_bounds

router = APIRouter()


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

    txs = list(
        db.scalars(
            select(Transaction)
            .options(joinedload(Transaction.category))
            .where(Transaction.date >= start, Transaction.date < end)
            .order_by(Transaction.date.desc(), Transaction.id.desc())
        )
        .unique()
        .all()
    )

    uncategorized = db.scalar(
        select(Category).where(Category.name == "Não categorizado")
    )
    uncategorized_id = uncategorized.id if uncategorized else None

    totals: Dict[Optional[int], dict] = defaultdict(
        lambda: {"total": 0.0, "count": 0, "name": "Sem categoria", "color": "#9CA3AF"}
    )
    categories = {c.id: c for c in db.scalars(select(Category)).all()}

    spent = 0.0
    uncategorized_count = 0
    for tx in txs:
        amount = abs(tx.amount) if tx.amount > 0 else 0.0
        if tx.amount <= 0:
            continue
        spent += amount
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
        for cat_id, data in sorted(totals.items(), key=lambda x: x[1]["total"], reverse=True)
    ]

    recent = [TransactionOut.model_validate(tx) for tx in txs[:50]]

    return DashboardSummary(
        month=month,
        total_spent=round(spent, 2),
        transaction_count=len([t for t in txs if t.amount > 0]),
        uncategorized_count=uncategorized_count,
        by_category=by_category,
        recent_transactions=recent,
    )
