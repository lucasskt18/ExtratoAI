from __future__ import annotations

import re
from datetime import date

from app.parsers.base import ParsedStatement, ParsedTransaction, parse_br_date, parse_brl_amount

# Inter-style: DD/MM/YYYY Description amount
LINE_RE = re.compile(
    r"^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(-?R?\$?\s*[\d.]+,\d{2})$",
)
INSTALLMENT_RE = re.compile(r"(\d{1,2}/\d{1,2})")
PERIOD_RE = re.compile(
    r"(?:período|periodo|vencimento)[^\d]*(\d{2}/\d{2}/\d{4}).*?(\d{2}/\d{2}/\d{4})",
    re.IGNORECASE | re.DOTALL,
)
TOTAL_RE = re.compile(
    r"(?:total\s+da\s+fatura|valor\s+total)[^\d-]*(-?R?\$?\s*[\d.]+,\d{2})",
    re.IGNORECASE,
)


def parse_inter(text: str) -> ParsedStatement:
    transactions: list[ParsedTransaction] = []
    seen: set[tuple[date, str, float]] = set()

    for raw_line in text.splitlines():
        line = " ".join(raw_line.split())
        m = LINE_RE.match(line)
        if not m:
            continue
        tx_date = parse_br_date(m.group(1))
        description = m.group(2).strip()
        amount = parse_brl_amount(m.group(3))
        if tx_date is None or amount is None:
            continue

        lowered = description.lower()
        if any(k in lowered for k in ("pagamento efetuado", "saldo anterior", "limite de crédito")):
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

    return ParsedStatement(
        bank="inter",
        transactions=transactions,
        card_label="Inter",
        period_start=period_start,
        period_end=period_end,
        total_amount=total_amount,
        confidence=0.85 if transactions else 0.2,
    )
