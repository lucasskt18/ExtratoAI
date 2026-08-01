from __future__ import annotations

import csv
import io
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models.transaction import Transaction

router = APIRouter()


@router.get("/csv")
def export_csv(
    month: Optional[str] = Query(None, description="YYYY-MM"),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    query = (
        select(Transaction)
        .options(joinedload(Transaction.category), joinedload(Transaction.statement))
        .order_by(Transaction.date.asc(), Transaction.id.asc())
    )

    if month:
        try:
            year_s, month_s = month.split("-")
            year, mon = int(year_s), int(month_s)
            start = date(year, mon, 1)
            end = date(year + 1, 1, 1) if mon == 12 else date(year, mon + 1, 1)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid month format") from exc
        query = query.where(Transaction.date >= start, Transaction.date < end)

    txs = list(db.scalars(query).unique().all())

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["date", "description", "amount", "installment", "category", "bank", "statement"]
    )
    for tx in txs:
        writer.writerow(
            [
                tx.date.isoformat(),
                tx.description,
                f"{tx.amount:.2f}",
                tx.installment or "",
                tx.category.name if tx.category else "",
                tx.statement.bank if tx.statement else "",
                tx.statement.source_filename if tx.statement else "",
            ]
        )

    buffer.seek(0)
    filename = f"extratoai_{month or 'all'}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
