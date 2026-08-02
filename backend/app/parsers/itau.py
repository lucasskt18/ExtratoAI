from __future__ import annotations

import re
import unicodedata
from datetime import date
from typing import Optional

from app.parsers.base import ParsedStatement, ParsedTransaction, parse_br_date, parse_brl_amount

# 20/01 PadariaESAOJOAODEMBR 16,50 ...
# 26/01 DROGARIASOCIALJDLTDS 13,99 Multaporatraso 2,00% 0,40
TX_LINE = re.compile(
    r"^(\d{2}/\d{2})\s+(.+?)\s+(-?\d{1,3}(?:\.\d{3})*,\d{2})\b"
)

DUE_RE = re.compile(
    r"Vencimento[:\s]*(\d{2}/\d{2}/\d{4})",
    re.IGNORECASE,
)
ISSUE_RE = re.compile(
    r"Emiss[aã]o[:\s]*(\d{2}/\d{2}/\d{4})",
    re.IGNORECASE,
)
TOTAL_RE = re.compile(
    r"Totaldesta\s*fatura\s*(-?\d{1,3}(?:\.\d{3})*,\d{2})",
    re.IGNORECASE,
)
TOTAL_ALT_RE = re.compile(
    r"O\s*total\s*da\s*sua\s*fatura\s*[ée]?.*?R\$\s*(-?\d{1,3}(?:\.\d{3})*,\d{2})",
    re.IGNORECASE | re.DOTALL,
)

SKIP_DESC_TOKENS = (
    "pagamento",
    "pagamentos",
    "limitedisponivel",
    "limitedisponível",
    "limitetotalutilizado",
    "limitetotaldecredito",
    "limitetotaldecrédito",
    "limitemaximo",
    "limitemáximo",
    "totaldospagamentos",
    "totaldafaturaanterior",
    "lancamentosatuais",
    "lançamentosatuais",
    "totaldoslancamentos",
    "totaldoslançamentos",
)


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _norm(value: str) -> str:
    return _strip_accents(value).lower().replace(" ", "")


def _infer_anchor_date(text: str) -> date:
    for pattern in (DUE_RE, ISSUE_RE):
        match = pattern.search(text)
        if match:
            parsed = parse_br_date(match.group(1))
            if parsed:
                return parsed
    years = [int(y) for y in re.findall(r"\b(20\d{2})\b", text)]
    year = years[0] if years else date.today().year
    return date(year, date.today().month, 1)


def _resolve_tx_date(day_month: str, anchor: date) -> Optional[date]:
    parsed = parse_br_date(day_month, default_year=anchor.year)
    if parsed is None:
        return None
    # Statement can span Dec→Jan: if tx month is after due/issue month, use previous year
    if parsed.month > anchor.month:
        try:
            return date(anchor.year - 1, parsed.month, parsed.day)
        except ValueError:
            return parsed
    return parsed


def _should_skip_line(description: str, full_line: str) -> bool:
    blob = _norm(f"{description} {full_line}")
    return any(token in blob for token in SKIP_DESC_TOKENS)


def _clean_description(raw: str) -> str:
    # Keep merchant token; drop trailing category crumbs glued without spaces later
    desc = raw.strip()
    # Cut common right-column leftovers that sometimes leak before the amount group
    for marker in (
        " Enca",
        " Multa",
        " Juros",
        " IOF",
        " Credito",
        " Crédito",
        " Total",
        " Limite",
    ):
        idx = desc.find(marker)
        if idx > 0:
            desc = desc[:idx]
    return " ".join(desc.split())


def parse_itau(text: str) -> ParsedStatement:
    compact = " ".join(text.split())
    anchor = _infer_anchor_date(text)

    total_amount = 0.0
    total_match = TOTAL_RE.search(compact) or TOTAL_ALT_RE.search(compact)
    if total_match:
        parsed_total = parse_brl_amount(total_match.group(1))
        if parsed_total is not None:
            total_amount = abs(parsed_total)

    transactions: list[ParsedTransaction] = []
    seen: set[tuple[date, str, float]] = set()

    for raw_line in text.splitlines():
        line = " ".join(raw_line.split())
        match = TX_LINE.match(line)
        if not match:
            continue

        description = _clean_description(match.group(2))
        if not description or _should_skip_line(description, line):
            continue

        amount = parse_brl_amount(match.group(3))
        if amount is None:
            continue
        # Purchases/fees on the statement are expenses (positive)
        amount = abs(amount)

        tx_date = _resolve_tx_date(match.group(1), anchor)
        if tx_date is None:
            continue

        key = (tx_date, description.lower(), round(amount, 2))
        if key in seen:
            continue
        seen.add(key)
        transactions.append(
            ParsedTransaction(
                date=tx_date,
                description=description,
                amount=amount,
            )
        )

    if not total_amount and transactions:
        total_amount = sum(t.amount for t in transactions)

    return ParsedStatement(
        bank="itau",
        transactions=transactions,
        card_label="Itaú",
        period_end=anchor if DUE_RE.search(text) else None,
        total_amount=total_amount,
        confidence=0.9 if transactions else 0.2,
    )
