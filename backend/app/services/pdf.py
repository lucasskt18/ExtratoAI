from __future__ import annotations

import hashlib
from pathlib import Path

import pdfplumber


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_text_from_pdf(path: Path) -> str:
    parts: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if text.strip():
                parts.append(text)
            else:
                # Fallback: try tables joined as text rows
                tables = page.extract_tables() or []
                for table in tables:
                    for row in table:
                        cells = [c.strip() for c in row if c and str(c).strip()]
                        if cells:
                            parts.append(" ".join(cells))
    return "\n".join(parts).strip()


def transaction_fingerprint(tx_date: str, description: str, amount: float) -> str:
    raw = f"{tx_date}|{description.strip().lower()}|{amount:.2f}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
