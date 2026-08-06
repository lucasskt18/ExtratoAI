from __future__ import annotations

import uuid
from pathlib import Path
from typing import Dict, List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.serializers import statement_out
from app.config import settings
from app.db.session import get_db
from app.models.statement import Statement
from app.models.transaction import Transaction
from app.schemas import InboxStatus, StatementDetail, StatementOut, UploadResult
from app.services.pdf import InvalidPdfError, find_pdf_offset
from app.services.pipeline import DuplicateStatementError, process_inbox, process_pdf

router = APIRouter()


@router.get("", response_model=List[StatementOut])
def list_statements(db: Session = Depends(get_db)) -> List[StatementOut]:
    rows = db.execute(
        select(Statement, func.count(Transaction.id))
        .outerjoin(Transaction, Transaction.statement_id == Statement.id)
        .group_by(Statement.id)
        .order_by(Statement.created_at.desc())
    ).all()
    return [statement_out(stmt, count) for stmt, count in rows]


@router.get("/inbox", response_model=InboxStatus)
def inbox_status(db: Session = Depends(get_db)) -> InboxStatus:
    settings.inbox_dir.mkdir(parents=True, exist_ok=True)
    pending = sorted(p.name for p in settings.inbox_dir.glob("*.pdf"))
    processed_count = db.scalar(select(func.count()).select_from(Statement)) or 0
    return InboxStatus(
        inbox_dir=str(settings.inbox_dir),
        pending_pdfs=pending,
        processed_count=processed_count,
    )


@router.post("/process-inbox", response_model=List[StatementOut])
def process_inbox_endpoint(db: Session = Depends(get_db)) -> List[StatementOut]:
    statements = process_inbox(db)
    return [statement_out(s, len(s.transactions)) for s in statements]


@router.post("/upload", response_model=UploadResult)
async def upload_statement(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> UploadResult:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Envie um arquivo .pdf")

    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    original = Path(file.filename).name
    # Write outside inbox so the watcher never races with the HTTP upload.
    dest = settings.uploads_dir / f"{uuid.uuid4().hex}_{original}"

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Arquivo vazio")

    offset = find_pdf_offset(raw)
    if offset < 0:
        raise HTTPException(
            status_code=400,
            detail=(
                f"'{original}' não parece um PDF válido. "
                "Baixe novamente a fatura no app do banco."
            ),
        )
    dest.write_bytes(raw[offset:])

    try:
        statement = process_pdf(db, dest, source_filename=original)
        message = "Fatura processada com sucesso"
    except DuplicateStatementError as exc:
        dest.unlink(missing_ok=True)
        raise HTTPException(
            status_code=409,
            detail=f"Esta fatura já foi importada (id={exc.statement_id})",
        ) from exc
    except InvalidPdfError as exc:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return UploadResult(
        statement=statement_out(statement, len(statement.transactions)),
        message=message,
    )


@router.get("/{statement_id}", response_model=StatementDetail)
def get_statement(statement_id: int, db: Session = Depends(get_db)) -> StatementDetail:
    stmt = db.scalar(
        select(Statement)
        .options(joinedload(Statement.transactions).joinedload(Transaction.category))
        .where(Statement.id == statement_id)
    )
    if not stmt:
        raise HTTPException(status_code=404, detail="Statement not found")
    base = statement_out(stmt, len(stmt.transactions))
    return StatementDetail(**base.model_dump(), transactions=stmt.transactions)


@router.delete("/{statement_id}")
def delete_statement(statement_id: int, db: Session = Depends(get_db)) -> Dict[str, str]:
    stmt = db.get(Statement, statement_id)
    if not stmt:
        raise HTTPException(status_code=404, detail="Statement not found")
    db.delete(stmt)
    db.commit()
    return {"status": "deleted"}
