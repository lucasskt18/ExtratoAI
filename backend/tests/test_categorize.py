from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.seed import seed_categories
from app.db.session import Base
from app.models.category import Category
from app.services.categorize import (
    categorize_description,
    ensure_merchant_rule,
    extract_merchant_pattern,
    normalize_description,
)


@pytest.fixture()
def db_session(tmp_path: Path) -> Session:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},
    )
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSession()
    seed_categories(session)
    yield session
    session.close()


def test_normalize_and_merchant_helpers():
    assert "ifood" in normalize_description("IFOOD *IFOOD CLUBE")
    assert extract_merchant_pattern("IFOOD *IFOOD CLUBE Parcela 1/3") == "ifood"


def test_categorize_uses_keywords(db_session: Session):
    cat_id = categorize_description(db_session, "IFOOD *IFOOD CLUBE")
    category = db_session.get(Category, cat_id)
    assert category is not None
    assert category.name == "Alimentação"


def test_merchant_rule_overrides_keywords(db_session: Session):
    assinaturas = db_session.scalar(
        select(Category).where(Category.name == "Assinaturas")
    )
    assert assinaturas is not None
    ensure_merchant_rule(db_session, "IFOOD *IFOOD CLUBE", assinaturas.id)
    cat_id = categorize_description(db_session, "IFOOD *RESTAURANTE XYZ")
    assert cat_id == assinaturas.id
