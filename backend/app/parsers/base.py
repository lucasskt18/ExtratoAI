from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Callable, Optional


@dataclass
class ParsedTransaction:
    date: date
    description: str
    amount: float
    installment: Optional[str] = None


@dataclass
class ParsedStatement:
    bank: str
    transactions: list[ParsedTransaction] = field(default_factory=list)
    card_label: Optional[str] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    total_amount: float = 0.0
    confidence: float = 1.0


BANK_HINTS = [
    ("nubank", ["nubank", "nu pagamentos", "nuconta"]),
    ("inter", ["banco inter", "inter medium", "interpag"]),
    ("itau", ["itaú", "itau", "banco itaú"]),
    ("c6", ["c6 bank", "banco c6"]),
]


def detect_bank(text: str) -> str:
    lowered = text.lower()
    for bank, hints in BANK_HINTS:
        if any(h in lowered for h in hints):
            return bank
    return "generic"


def parse_brl_amount(raw: str) -> Optional[float]:
    cleaned = raw.strip().replace("R$", "").replace(" ", "")
    if not cleaned:
        return None
    # Brazilian format: 1.234,56 or -1.234,56
    negative = cleaned.startswith("-") or cleaned.endswith("-")
    cleaned = cleaned.replace("-", "")
    if "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    try:
        value = float(cleaned)
    except ValueError:
        return None
    return -abs(value) if negative else value


def parse_br_date(raw: str, default_year: Optional[int] = None) -> Optional[date]:
    raw = raw.strip()
    m = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", raw)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return date(year, month, day)
    m = re.match(r"^(\d{2})/(\d{2})$", raw)
    if m and default_year:
        day, month = int(m.group(1)), int(m.group(2))
        return date(default_year, month, day)
    return None


def parse_statement_text(text: str) -> ParsedStatement:
    from app.parsers.generic import parse_generic
    from app.parsers.inter import parse_inter
    from app.parsers.nubank import parse_nubank

    bank = detect_bank(text)
    parsers: dict[str, Callable[[str], ParsedStatement]] = {
        "nubank": parse_nubank,
        "inter": parse_inter,
        "generic": parse_generic,
    }
    parser = parsers.get(bank, parse_generic)
    result = parser(text)
    result.bank = bank if bank != "generic" else result.bank
    if not result.transactions and bank != "generic":
        fallback = parse_generic(text)
        if len(fallback.transactions) > len(result.transactions):
            fallback.bank = bank
            fallback.confidence = 0.5
            return fallback
    return result
