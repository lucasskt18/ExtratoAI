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

# C6 layouts often look like:
# 15/03/2026 IFOOD *IFOOD           89,90
# 15 MAR IFOOD *IFOOD R$ 89,90
LINE_SLASH = re.compile(
    r"^(\d{2}/\d{2}(?:/\d{4})?)\s+(.+?)\s+(-?R?\$?\s*[\d.]+,\d{2})$",
)
LINE_DD_MMM = re.compile(
    r"^(\d{2})\s+([A-Z]{3})\s+(.+?)\s+(-?R?\$?\s*[\d.]+,\d{2})$",
    re.IGNORECASE,
)
INSTALLMENT_RE = re.compile(
    r"(?:parcela\s+)?(\d{1,2})\s*/\s*(\d{1,2})",
    re.IGNORECASE,
)
PERIOD_RE = re.compile(
    r"(\d{2}/\d{2}/\d{4})\s*(?:a|até|-)\s*(\d{2}/\d{2}/\d{4})",
    re.IGNORECASE,
)
DUE_RE = re.compile(
    r"(?:vencimento|data\s+de\s+vencimento)[^\d]*(\d{2}/\d{2}/\d{4})",
    re.IGNORECASE,
)
TOTAL_RE = re.compile(
    r"(?:total|valor\s+total|total\s+da\s+fatura|valor\s+da\s+fatura)"
    r"[^\d-]*(-?R?\$?\s*[\d.]+,\d{2})",
    re.IGNORECASE,
)

SKIP_TOKENS = (
    "pagamento recebido",
    "pagamento efetuado",
    "saldo anterior",
    "limite total",
    "limite de credito",
    "limite de crédito",
    "fatura anterior",
)


def _infer_year(text: str) -> int:
    years = [int(y) for y in re.findall(r"\b(20\d{2})\b", text)]
    return years[-1] if years else date.today().year


def parse_c6(text: str) -> ParsedStatement:
    year = _infer_year(text)
    transactions: list[ParsedTransaction] = []
    seen: set[tuple[date, str, float]] = set()

    for raw_line in text.splitlines():
        line = " ".join(raw_line.split())
        if not line:
            continue

        tx_date = None
        description = None
        amount = None

        m = LINE_DD_MMM.match(line)
        if m:
            day = int(m.group(1))
            month = MONTH_MAP.get(m.group(2).upper())
            if not month:
                continue
            try:
                tx_date = date(year, month, day)
            except ValueError:
                continue
            description = m.group(3).strip()
            amount = parse_brl_amount(m.group(4))
        else:
            m = LINE_SLASH.match(line)
            if not m:
                continue
            tx_date = parse_br_date(m.group(1), default_year=year)
            description = m.group(2).strip()
            amount = parse_brl_amount(m.group(3))

        if tx_date is None or amount is None or not description:
            continue

        lowered = description.lower()
        if any(k in lowered for k in SKIP_TOKENS):
            continue

        installment = None
        inst = INSTALLMENT_RE.search(description)
        if inst:
            installment = f"{int(inst.group(1))}/{int(inst.group(2))}"

        key = (tx_date, description.lower(), round(amount, 2))
        if key in seen:
            continue
        seen.add(key)
        transactions.append(
            ParsedTransaction(
                date=tx_date,
                description=description,
                amount=abs(amount) if amount > 0 else amount,
                installment=installment,
            )
        )

    period_start = period_end = None
    period_match = PERIOD_RE.search(text)
    if period_match:
        period_start = parse_br_date(period_match.group(1))
        period_end = parse_br_date(period_match.group(2))
    elif DUE_RE.search(text):
        period_end = parse_br_date(DUE_RE.search(text).group(1))

    total_amount = sum(t.amount for t in transactions if t.amount > 0)
    total_match = TOTAL_RE.search(text)
    if total_match:
        parsed_total = parse_brl_amount(total_match.group(1))
        if parsed_total is not None:
            total_amount = abs(parsed_total)

    return ParsedStatement(
        bank="c6",
        transactions=transactions,
        card_label="C6 Bank",
        period_start=period_start,
        period_end=period_end,
        total_amount=total_amount,
        confidence=0.85 if transactions else 0.2,
    )
