from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.category import Category
from app.models.merchant_rule import MerchantRule
from app.schemas import (
    CategoryOut,
    CategoryUpdate,
    MerchantRuleCreate,
    MerchantRuleOut,
    MerchantRuleUpdate,
    RecategorizeResult,
)
from app.services.categorize import apply_rules_to_uncategorized, ensure_merchant_rule

router = APIRouter()


@router.get("", response_model=List[CategoryOut])
def list_categories(db: Session = Depends(get_db)) -> List[Category]:
    return list(db.scalars(select(Category).order_by(Category.name)).all())


@router.patch("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
) -> Category:
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    if payload.name is not None:
        category.name = payload.name
    if payload.color is not None:
        category.color = payload.color
    if payload.keywords is not None:
        category.keywords = payload.keywords
    db.commit()
    db.refresh(category)
    return category


@router.get("/rules", response_model=List[MerchantRuleOut])
def list_rules(db: Session = Depends(get_db)) -> List[MerchantRule]:
    return list(db.scalars(select(MerchantRule).order_by(MerchantRule.pattern)).all())


@router.post("/rules", response_model=MerchantRuleOut)
def create_rule(
    payload: MerchantRuleCreate,
    db: Session = Depends(get_db),
) -> MerchantRule:
    category = db.get(Category, payload.category_id)
    if not category:
        raise HTTPException(status_code=400, detail="Invalid category")
    return ensure_merchant_rule(db, payload.pattern, payload.category_id)


@router.patch("/rules/{rule_id}", response_model=MerchantRuleOut)
def update_rule(
    rule_id: int,
    payload: MerchantRuleUpdate,
    db: Session = Depends(get_db),
) -> MerchantRule:
    rule = db.get(MerchantRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    if payload.category_id is not None:
        category = db.get(Category, payload.category_id)
        if not category:
            raise HTTPException(status_code=400, detail="Invalid category")
        rule.category_id = payload.category_id
    if payload.pattern is not None:
        pattern = payload.pattern.strip().lower()
        if not pattern:
            raise HTTPException(status_code=400, detail="Pattern cannot be empty")
        conflict = db.scalar(
            select(MerchantRule).where(
                MerchantRule.pattern == pattern,
                MerchantRule.id != rule_id,
            )
        )
        if conflict:
            raise HTTPException(status_code=409, detail="Pattern already exists")
        rule.pattern = pattern
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/rules/{rule_id}")
def delete_rule(rule_id: int, db: Session = Depends(get_db)) -> Dict[str, str]:
    rule = db.get(MerchantRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(rule)
    db.commit()
    return {"status": "deleted"}


@router.post("/recategorize", response_model=RecategorizeResult)
def recategorize_uncategorized(db: Session = Depends(get_db)) -> RecategorizeResult:
    updated = apply_rules_to_uncategorized(db)
    return RecategorizeResult(updated=updated)
