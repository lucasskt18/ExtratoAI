from __future__ import annotations

import re
from datetime import date

from app.parsers.base import ParsedStatement, ParsedTransaction, parse_br_date, parse_brl_amount

LINE_RE = re.compile(
    r"^(\d{2}/\d{2}(?:/\d{4})?)\s+(.+?)\s+(-?R?\$?\s*[\d.]+,\d{2})$",
)


def parse_generic(text: str) -> ParsedStatement:
    year_matches = [int(y) for y in re.findall(r"\b(20\d{2})\b", text)]
    default_year = year_matches[-1] if year_matches else date.today().year
    transactions: list[ParsedTransaction] = []
    seen: set[tuple[date, str, float]] = set()

    for raw_line in text.splitlines():
        line = " ".join(raw_line.split())
        m = LINE_RE.match(line)
        if not m:
            continue
        tx_date = parse_br_date(m.group(1), default_year=default_year)
        description = m.group(2).strip()
        amount = parse_brl_amount(m.group(3))
        if tx_date is None or amount is None:
            continue
        key = (tx_date, description.lower(), round(amount, 2))
        if key in seen:
            continue
        seen.add(key)
        transactions.append(
            ParsedTransaction(date=tx_date, description=description, amount=amount)
        )

    total = sum(t.amount for t in transactions if t.amount > 0)
    return ParsedStatement(
        bank="generic",
        transactions=transactions,
        total_amount=total,
        confidence=0.6 if transactions else 0.1,
    )
