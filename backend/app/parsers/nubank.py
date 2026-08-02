from __future__ import annotations

import re
from datetime import date

from app.parsers.base import (
    MONTH_MAP,
    ParsedStatement,
    ParsedTransaction,
    parse_br_date,
    parse_brl_amount,
)

# Nubank-style lines: DD MMM Description value
# or DD/MM Description R$ value
LINE_DD_MMM = re.compile(
    r"^(\d{2})\s+([A-Z]{3})\s+(.+?)\s+(-?R?\$?\s*[\d.]+,\d{2})$",
    re.IGNORECASE,
)
LINE_DD_MM = re.compile(
    r"^(\d{2}/\d{2}(?:/\d{4})?)\s+(.+?)\s+(-?R?\$?\s*[\d.]+,\d{2})$",
)
INSTALLMENT_RE = re.compile(r"(\d{1,2}/\d{1,2})", re.IGNORECASE)
PERIOD_RE = re.compile(
    r"(\d{2}/\d{2}/\d{4})\s*(?:a|até|-)\s*(\d{2}/\d{2}/\d{4})",
    re.IGNORECASE,
)
TOTAL_RE = re.compile(
    r"(?:total|valor\s+total|total\s+da\s+fatura)[^\d-]*(-?R?\$?\s*[\d.]+,\d{2})",
    re.IGNORECASE,
)


def _infer_year(text: str) -> int:
    years = [int(y) for y in re.findall(r"\b(20\d{2})\b", text)]
    return years[-1] if years else date.today().year


def parse_nubank(text: str) -> ParsedStatement:
    year = _infer_year(text)
    transactions: list[ParsedTransaction] = []
    seen: set[tuple[date, str, float]] = set()

    for raw_line in text.splitlines():
        line = " ".join(raw_line.split())
        if not line:
            continue

        m = LINE_DD_MMM.match(line)
        if m:
            day = int(m.group(1))
            month = MONTH_MAP.get(m.group(2).upper())
            if not month:
                continue
            description = m.group(3).strip()
            amount = parse_brl_amount(m.group(4))
            if amount is None:
                continue
            tx_date = date(year, month, day)
        else:
            m = LINE_DD_MM.match(line)
            if not m:
                continue
            tx_date = parse_br_date(m.group(1), default_year=year)
            description = m.group(2).strip()
            amount = parse_brl_amount(m.group(3))
            if tx_date is None or amount is None:
                continue

        # Skip payment/credit summary lines often present in Nubank PDFs
        lowered = description.lower()
        if any(k in lowered for k in ("pagamento recebido", "saldo anterior", "limite total")):
            continue

        installment_match = INSTALLMENT_RE.search(description)
        installment = installment_match.group(1) if installment_match else None
        key = (tx_date, description.lower(), round(amount, 2))
        if key in seen:
            continue
        seen.add(key)
        transactions.append(
            ParsedTransaction(
                date=tx_date,
                description=description,
                amount=amount,
                installment=installment,
            )
        )

    period_start = period_end = None
    period_match = PERIOD_RE.search(text)
    if period_match:
        period_start = parse_br_date(period_match.group(1))
        period_end = parse_br_date(period_match.group(2))

    total_amount = sum(t.amount for t in transactions if t.amount > 0)
    total_match = TOTAL_RE.search(text)
    if total_match:
        parsed_total = parse_brl_amount(total_match.group(1))
        if parsed_total is not None:
            total_amount = abs(parsed_total)

    confidence = 0.9 if transactions else 0.2
    return ParsedStatement(
        bank="nubank",
        transactions=transactions,
        card_label="Nubank",
        period_start=period_start,
        period_end=period_end,
        total_amount=total_amount,
        confidence=confidence,
    )
