from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.api.serializers import statement_out
from app.db.session import get_db
from app.models.category import Category
from app.models.statement import Statement
from app.models.transaction import Transaction
from app.schemas import ReviewQueueOut, StatementOut

router = APIRouter()


def _uncategorized_filter(db: Session):
    uncategorized = db.scalar(
        select(Category).where(Category.name == "Não categorizado")
    )
    if uncategorized:
        return or_(
            Transaction.category_id.is_(None),
            Transaction.category_id == uncategorized.id,
        )
    return Transaction.category_id.is_(None)


@router.get("", response_model=ReviewQueueOut)
def review_queue(db: Session = Depends(get_db)) -> ReviewQueueOut:
    needs_review_rows = db.execute(
        select(Statement, func.count(Transaction.id))
        .outerjoin(Transaction, Transaction.statement_id == Statement.id)
        .where(Statement.status == "needs_review")
        .group_by(Statement.id)
        .order_by(Statement.created_at.desc())
    ).all()
    statements = [statement_out(stmt, count) for stmt, count in needs_review_rows]

    uncategorized_txs = list(
        db.scalars(
            select(Transaction)
            .options(joinedload(Transaction.category))
            .where(_uncategorized_filter(db))
            .order_by(Transaction.date.desc(), Transaction.id.desc())
            .limit(100)
        )
        .unique()
        .all()
    )

    uncategorized_count = (
        db.scalar(
            select(func.count()).select_from(Transaction).where(_uncategorized_filter(db))
        )
        or 0
    )

    return ReviewQueueOut(
        statements_needs_review=statements,
        uncategorized_transactions=uncategorized_txs,
        needs_review_count=len(statements),
        uncategorized_count=uncategorized_count,
    )


@router.post("/statements/{statement_id}/mark-reviewed", response_model=StatementOut)
def mark_statement_reviewed(
    statement_id: int,
    db: Session = Depends(get_db),
) -> StatementOut:
    stmt = db.get(Statement, statement_id)
    if not stmt:
        raise HTTPException(status_code=404, detail="Statement not found")
    stmt.status = "processed"
    db.commit()
    db.refresh(stmt)
    count = (
        db.scalar(
            select(func.count())
            .select_from(Transaction)
            .where(Transaction.statement_id == stmt.id)
        )
        or 0
    )
    return statement_out(stmt, count)
