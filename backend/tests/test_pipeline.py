from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.seed import seed_categories
from app.db.session import Base
from app.models.category import Category
from app.parsers import parse_statement_text
from app.services.categorize import categorize_description
from app.services.pdf import transaction_fingerprint


@pytest.fixture()
def db_session(tmp_path: Path):
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


def test_categorize_ifood(db_session):
    cat_id = categorize_description(db_session, "IFOOD *IFOOD CLUBE")
    category = db_session.get(Category, cat_id)
    assert category is not None
    assert category.name == "Alimentação"


def test_categorize_netflix(db_session):
    cat_id = categorize_description(db_session, "NETFLIX.COM")
    category = db_session.get(Category, cat_id)
    assert category is not None
    assert category.name == "Assinaturas"


def test_fingerprint_stable():
    a = transaction_fingerprint("2026-03-01", "IFOOD", 89.9)
    b = transaction_fingerprint("2026-03-01", "ifood", 89.90)
    assert a == b


def test_parse_and_categorize_flow(db_session):
    text = (Path(__file__).parent / "fixtures" / "nubank_sample.txt").read_text(
        encoding="utf-8"
    )
    parsed = parse_statement_text(text)
    cats = {
        categorize_description(db_session, t.description) for t in parsed.transactions
    }
    assert None not in cats
    names = {
        db_session.get(Category, cid).name for cid in cats if cid is not None
    }
    assert "Alimentação" in names
    assert "Assinaturas" in names
