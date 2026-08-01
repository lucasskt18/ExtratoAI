from __future__ import annotations

import logging
import shutil
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.statement import Statement
from app.models.transaction import Transaction
from app.parsers import parse_statement_text
from app.services.categorize import categorize_description
from app.services.pdf import extract_text_from_pdf, file_sha256, transaction_fingerprint

logger = logging.getLogger(__name__)


class DuplicateStatementError(Exception):
    def __init__(self, statement_id: int):
        self.statement_id = statement_id
        super().__init__(f"Statement already processed: {statement_id}")


def process_pdf(db: Session, path: Path, move_to_processed: bool = True) -> Statement:
    if not path.exists() or path.suffix.lower() != ".pdf":
        raise ValueError(f"Invalid PDF path: {path}")

    file_hash = file_sha256(path)
    existing = db.scalar(select(Statement).where(Statement.file_hash == file_hash))
    if existing:
        raise DuplicateStatementError(existing.id)

    text = extract_text_from_pdf(path)
    if not text:
        statement = Statement(
            bank="unknown",
            source_filename=path.name,
            file_hash=file_hash,
            status="needs_review",
            raw_text_preview="",
            total_amount=0.0,
        )
        db.add(statement)
        db.commit()
        db.refresh(statement)
        _maybe_move(path, move_to_processed)
        return statement

    parsed = parse_statement_text(text)
    statement = Statement(
        bank=parsed.bank,
        card_label=parsed.card_label,
        period_start=parsed.period_start,
        period_end=parsed.period_end,
        total_amount=parsed.total_amount,
        source_filename=path.name,
        file_hash=file_hash,
        status="needs_review" if parsed.confidence < 0.5 or not parsed.transactions else "processed",
        raw_text_preview=text[:2000],
    )
    db.add(statement)
    db.flush()

    for tx in parsed.transactions:
        category_id = categorize_description(db, tx.description)
        db.add(
            Transaction(
                statement_id=statement.id,
                date=tx.date,
                description=tx.description,
                amount=tx.amount,
                installment=tx.installment,
                category_id=category_id,
                fingerprint=transaction_fingerprint(
                    tx.date.isoformat(), tx.description, tx.amount
                ),
            )
        )

    if not statement.total_amount and parsed.transactions:
        statement.total_amount = sum(t.amount for t in parsed.transactions if t.amount > 0)

    db.commit()
    db.refresh(statement)
    _maybe_move(path, move_to_processed)
    logger.info(
        "Processed %s as %s with %d transactions",
        path.name,
        statement.bank,
        len(parsed.transactions),
    )
    return statement


def _maybe_move(path: Path, move_to_processed: bool) -> None:
    if not move_to_processed:
        return
    settings.processed_dir.mkdir(parents=True, exist_ok=True)
    dest = settings.processed_dir / path.name
    if dest.exists():
        stem, suffix = path.stem, path.suffix
        i = 1
        while dest.exists():
            dest = settings.processed_dir / f"{stem}_{i}{suffix}"
            i += 1
    shutil.move(str(path), str(dest))


def process_inbox(db: Session) -> list[Statement]:
    settings.inbox_dir.mkdir(parents=True, exist_ok=True)
    results: list[Statement] = []
    for path in sorted(settings.inbox_dir.glob("*.pdf")):
        try:
            results.append(process_pdf(db, path))
        except DuplicateStatementError:
            _maybe_move(path, True)
        except Exception:
            logger.exception("Failed to process %s", path)
    return results
