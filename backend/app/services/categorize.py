from __future__ import annotations

import re
import unicodedata
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.merchant_rule import MerchantRule
from app.models.transaction import Transaction

# Noise prefixes common on card statements
_TOKEN_JUNK = re.compile(
    r"^(?:\*|x+|loja|store|br|bra|brasil|sa|ltda|me|epp)$",
    re.IGNORECASE,
)
_INSTALLMENT_TAIL = re.compile(
    r"\s*(?:\(?\s*parcela\s+\d{1,2}\s+de\s+\d{1,2}\s*\)?|\d{1,2}/\d{1,2})\s*$",
    re.IGNORECASE,
)
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def normalize_description(description: str) -> str:
    """Lowercase, strip accents, collapse whitespace for matching."""
    text = _strip_accents(description or "").lower()
    text = _INSTALLMENT_TAIL.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_merchant_pattern(description: str) -> str:
    """
    Derive a stable merchant token from a raw card description.

    Examples:
      "IFOOD *IFOOD CLUBE" -> "ifood"
      "Uber Trip Sao Paulo" -> "uber"
      "Amazon Marketplace" -> "amazon"
      "Shell Box Posto 123" -> "shell"
    """
    text = normalize_description(description)
    if not text:
        return ""

    # Prefer token before '*' when present (IFOOD *IFOOD CLUBE)
    if "*" in text:
        left, right = text.split("*", 1)
        candidate = left.strip() or right.strip()
        text = candidate

    tokens = [t for t in _NON_ALNUM.split(text) if t]
    cleaned: list[str] = []
    for token in tokens:
        if _TOKEN_JUNK.match(token):
            continue
        if token.isdigit():
            continue
        if len(token) < 2:
            continue
        cleaned.append(token)

    if not cleaned:
        return text[:40].strip()

    # Drop leading noise prefixes like "pag"
    while cleaned and any(cleaned[0].startswith(p.rstrip("*")) for p in ("pag", "compra", "deb", "cred")):
        if len(cleaned) == 1:
            break
        cleaned = cleaned[1:]

    # Use first meaningful token; longer brands keep 1-2 tokens if short
    if len(cleaned[0]) >= 4:
        return cleaned[0][:80]
    if len(cleaned) >= 2:
        return f"{cleaned[0]} {cleaned[1]}"[:80]
    return cleaned[0][:80]


def categorize_description(db: Session, description: str) -> Optional[int]:
    lowered = normalize_description(description)
    merchant = extract_merchant_pattern(description)

    rules = list(db.scalars(select(MerchantRule)).all())
    # Prefer longer patterns to avoid weak short matches
    rules.sort(key=lambda r: len(r.pattern or ""), reverse=True)
    for rule in rules:
        pattern = (rule.pattern or "").lower().strip()
        if not pattern:
            continue
        if pattern in lowered or (merchant and pattern == merchant):
            return rule.category_id

    categories = db.scalars(select(Category)).all()
    best_id: Optional[int] = None
    best_score = 0
    uncategorized_id: Optional[int] = None

    for category in categories:
        if category.name == "Não categorizado":
            uncategorized_id = category.id
            continue
        if not category.keywords:
            continue
        keywords = [k.strip().lower() for k in category.keywords.split(",") if k.strip()]
        score = 0
        for kw in keywords:
            kw_norm = normalize_description(kw)
            if not kw_norm:
                continue
            if kw_norm in lowered or (merchant and kw_norm == merchant):
                # Longer keyword matches weigh more
                score += max(1, len(kw_norm) // 4)
        if score > best_score:
            best_score = score
            best_id = category.id

    if best_id is not None:
        return best_id
    return uncategorized_id


def ensure_merchant_rule(db: Session, pattern: str, category_id: int) -> MerchantRule:
    normalized = extract_merchant_pattern(pattern) or normalize_description(pattern)
    if not normalized:
        normalized = pattern.strip().lower()[:80]
    existing = db.scalar(
        select(MerchantRule).where(MerchantRule.pattern == normalized)
    )
    if existing:
        existing.category_id = category_id
        db.commit()
        db.refresh(existing)
        return existing
    rule = MerchantRule(pattern=normalized, category_id=category_id)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def apply_rules_to_uncategorized(db: Session) -> int:
    """Re-run categorization on uncategorized transactions. Returns updated count."""
    uncategorized = db.scalar(
        select(Category).where(Category.name == "Não categorizado")
    )
    query = select(Transaction)
    if uncategorized:
        query = query.where(
            (Transaction.category_id.is_(None))
            | (Transaction.category_id == uncategorized.id)
        )
    else:
        query = query.where(Transaction.category_id.is_(None))

    updated = 0
    for tx in db.scalars(query).all():
        new_id = categorize_description(db, tx.description)
        if new_id is None:
            continue
        if uncategorized and new_id == uncategorized.id:
            continue
        if tx.category_id != new_id:
            tx.category_id = new_id
            updated += 1
    if updated:
        db.commit()
    return updated
