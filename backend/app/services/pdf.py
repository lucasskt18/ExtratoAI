from __future__ import annotations

import hashlib
import io
import logging
from pathlib import Path
from typing import Optional, Tuple

import pdfplumber

logger = logging.getLogger(__name__)

PDF_MAGIC = b"%PDF"


class InvalidPdfError(ValueError):
    """Raised when a file is not a readable PDF."""


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def find_pdf_offset(data: bytes) -> int:
    return data.find(PDF_MAGIC)


def is_pdf_bytes(data: bytes) -> bool:
    return find_pdf_offset(data) >= 0


def repair_pdf_file(path: Path) -> Tuple[bool, Optional[str]]:
    """
    If the file has junk/null bytes before %PDF (common race corruption),
    rewrite it starting at the PDF header. Returns (changed, message).
    """
    data = path.read_bytes()
    if not data:
        return False, "Arquivo vazio"

    offset = find_pdf_offset(data)
    if offset < 0:
        return False, "Arquivo não contém cabeçalho PDF válido (%PDF)"

    if offset == 0 and data.startswith(PDF_MAGIC):
        return False, None

    repaired = data[offset:]
    path.write_bytes(repaired)
    msg = f"PDF reparado: removidos {offset} bytes inválidos no início"
    logger.warning("%s (%s)", msg, path.name)
    return True, msg


def ensure_readable_pdf(path: Path) -> None:
    """Validate/repair PDF before opening with pdfplumber."""
    if not path.exists():
        raise InvalidPdfError(f"Arquivo não encontrado: {path.name}")

    data = path.read_bytes()
    if len(data) < 8:
        raise InvalidPdfError(
            f"'{path.name}' está vazio ou incompleto. Espere o download terminar e tente de novo."
        )

    offset = find_pdf_offset(data)
    if offset < 0:
        raise InvalidPdfError(
            f"'{path.name}' não parece um PDF válido. "
            "Baixe novamente a fatura do app do banco (arquivo .pdf)."
        )

    if offset > 0:
        repair_pdf_file(path)


def extract_text_from_pdf(path: Path) -> str:
    ensure_readable_pdf(path)
    parts = []
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                if text.strip():
                    parts.append(text)
                else:
                    tables = page.extract_tables() or []
                    for table in tables:
                        for row in table:
                            cells = [c.strip() for c in row if c and str(c).strip()]
                            if cells:
                                parts.append(" ".join(cells))
    except Exception as exc:
        raise InvalidPdfError(
            f"Não foi possível ler '{path.name}'. "
            "O PDF pode estar corrompido, protegido por senha ou ser só imagem. "
            f"Detalhe: {exc}"
        ) from exc
    return "\n".join(parts).strip()


def extract_text_from_bytes(data: bytes, filename: str = "upload.pdf") -> str:
    offset = find_pdf_offset(data)
    if offset < 0:
        raise InvalidPdfError(
            f"'{filename}' não parece um PDF válido. Baixe novamente a fatura do banco."
        )
    payload = data[offset:]
    parts = []
    try:
        with pdfplumber.open(io.BytesIO(payload)) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                if text.strip():
                    parts.append(text)
    except Exception as exc:
        raise InvalidPdfError(
            f"Não foi possível ler '{filename}'. Detalhe: {exc}"
        ) from exc
    return "\n".join(parts).strip()


def transaction_fingerprint(tx_date: str, description: str, amount: float) -> str:
    raw = f"{tx_date}|{description.strip().lower()}|{amount:.2f}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
