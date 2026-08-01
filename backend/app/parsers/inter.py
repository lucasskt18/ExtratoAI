from __future__ import annotations

import re
from datetime import date
from typing import Optional

from app.parsers.base import ParsedStatement, ParsedTransaction, parse_br_date, parse_brl_amount

MONTH_MAP = {
    "jan": 1,
    "fev": 2,
    "mar": 3,
    "abr": 4,
    "mai": 5,
    "jun": 6,
    "jul": 7,
    "ago": 8,
    "set": 9,
    "out": 10,
    "nov": 11,
    "dez": 12,
}

# Real Inter statement lines:
# 05 de abr. 2026 DROGARIA VIVA BEM CEN - R$ 41,95
# 10 de abr. 2026 PAGAMENTO ON LINE - + R$ 2.292,57
LINE_PT = re.compile(
    r"^(\d{1,2})\s+de\s+([a-z]{3})\.?\s+(\d{4})\s+(.+?)\s+-\s+(\+?\s*R\$\s*[\d.]+,\d{2})$",
    re.IGNORECASE,
)

# Fallback: DD/MM/YYYY Description amount
LINE_SLASH = re.compile(
    r"^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(-?R?\$?\s*[\d.]+,\d{2})$",
)

INSTALLMENT_RE = re.compile(
    r"\(?\s*Parcela\s+(\d{1,2})\s+de\s+(\d{1,2})\s*\)?",
    re.IGNORECASE,
)
# Prefer "Fatura atual" — "Total da sua fatura" often sits next to the credit limit in layout.
TOTAL_ATUAL_RE = re.compile(
    r"fatura\s+atual\s*R\$\s*([\d.]+,\d{2})",
    re.IGNORECASE,
)
TOTAL_FALLBACK_RE = re.compile(
    r"total\s+da\s+(?:sua\s+)?fatura\s*R\$\s*([\d.]+,\d{2})",
    re.IGNORECASE,
)
DUE_RE = re.compile(r"(?:vencimento|data\s+de\s+vencimento)[^\d]*(\d{2}/\d{2}/\d{4})", re.IGNORECASE)


def _parse_pt_date(day: str, month_token: str, year: str) -> Optional[date]:
    month = MONTH_MAP.get(month_token.lower()[:3])
    if not month:
        return None
    try:
        return date(int(year), month, int(day))
    except ValueError:
        return None


def parse_inter(text: str) -> ParsedStatement:
    transactions = []
    seen = set()

    for raw_line in text.splitlines():
        line = " ".join(raw_line.split())
        if not line:
            continue

        tx_date = None
        description = None
        amount = None

        m = LINE_PT.match(line)
        if m:
            tx_date = _parse_pt_date(m.group(1), m.group(2), m.group(3))
            description = m.group(4).strip()
            amount_raw = m.group(5).strip()
            is_credit = amount_raw.lstrip().startswith("+")
            amount = parse_brl_amount(amount_raw.replace("+", ""))
            if amount is not None and is_credit:
                amount = -abs(amount)
            elif amount is not None:
                amount = abs(amount)
        else:
            m = LINE_SLASH.match(line)
            if not m:
                continue
            tx_date = parse_br_date(m.group(1))
            description = m.group(2).strip()
            amount = parse_brl_amount(m.group(3))

        if tx_date is None or amount is None or not description:
            continue

        lowered = description.lower()
        if any(
            k in lowered
            for k in (
                "pagamento efetuado",
                "saldo anterior",
                "limite de crédito",
                "total cartão",
                "fatura atual",
            )
        ):
            continue

        installment_match = INSTALLMENT_RE.search(description)
        installment = None
        if installment_match:
            installment = (
                f"{int(installment_match.group(1))}/{int(installment_match.group(2))}"
            )

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

    period_end = None
    due_match = DUE_RE.search(text)
    if due_match:
        period_end = parse_br_date(due_match.group(1))

    total_amount = sum(t.amount for t in transactions if t.amount > 0)
    total_match = TOTAL_ATUAL_RE.search(text) or TOTAL_FALLBACK_RE.search(text)
    if total_match:
        parsed_total = parse_brl_amount(total_match.group(1))
        if parsed_total is not None:
            total_amount = abs(parsed_total)

    return ParsedStatement(
        bank="inter",
        transactions=transactions,
        card_label="Inter",
        period_start=None,
        period_end=period_end,
        total_amount=total_amount,
        confidence=0.85 if transactions else 0.2,
    )
