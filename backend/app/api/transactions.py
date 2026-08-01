from __future__ import annotations

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models.category import Category
from app.models.transaction import Transaction
from app.schemas import TransactionOut, TransactionUpdate
from app.services.categorize import ensure_merchant_rule

router = APIRouter()


@router.get("", response_model=List[TransactionOut])
def list_transactions(
    month: Optional[str] = Query(None, description="YYYY-MM"),
    category_id: Optional[int] = None,
    uncategorized: bool = False,
    db: Session = Depends(get_db),
) -> List[Transaction]:
    query = (
        select(Transaction)
        .options(joinedload(Transaction.category))
        .order_by(Transaction.date.desc(), Transaction.id.desc())
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

    if category_id is not None:
        query = query.where(Transaction.category_id == category_id)

    if uncategorized:
        uncategorized_cat = db.scalar(
            select(Category).where(Category.name == "Não categorizado")
        )
        if uncategorized_cat:
            query = query.where(
                (Transaction.category_id.is_(None))
                | (Transaction.category_id == uncategorized_cat.id)
            )
        else:
            query = query.where(Transaction.category_id.is_(None))

    return list(db.scalars(query).unique().all())


@router.patch("/{transaction_id}", response_model=TransactionOut)
def update_transaction(
    transaction_id: int,
    payload: TransactionUpdate,
    db: Session = Depends(get_db),
) -> Transaction:
    tx = db.scalar(
        select(Transaction)
        .options(joinedload(Transaction.category))
        .where(Transaction.id == transaction_id)
    )
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if payload.category_id is not None:
        category = db.get(Category, payload.category_id)
        if not category:
            raise HTTPException(status_code=400, detail="Invalid category")
        tx.category_id = payload.category_id

        if payload.remember_rule:
            pattern = payload.rule_pattern or tx.description.split()[0]
            ensure_merchant_rule(db, pattern, payload.category_id)

    db.commit()
    db.refresh(tx)
    return tx
