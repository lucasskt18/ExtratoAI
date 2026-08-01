from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.merchant_rule import MerchantRule


def categorize_description(db: Session, description: str) -> Optional[int]:
    lowered = description.lower()

    rules = db.scalars(select(MerchantRule)).all()
    for rule in rules:
        if rule.pattern.lower() in lowered:
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
        score = sum(1 for kw in keywords if kw in lowered)
        if score > best_score:
            best_score = score
            best_id = category.id

    if best_id is not None:
        return best_id
    return uncategorized_id


def ensure_merchant_rule(db: Session, pattern: str, category_id: int) -> MerchantRule:
    existing = db.scalar(
        select(MerchantRule).where(MerchantRule.pattern == pattern.lower())
    )
    if existing:
        existing.category_id = category_id
        db.commit()
        db.refresh(existing)
        return existing
    rule = MerchantRule(pattern=pattern.lower(), category_id=category_id)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule
