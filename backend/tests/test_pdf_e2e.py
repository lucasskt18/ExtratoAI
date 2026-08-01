from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db.seed import seed_categories
from app.db.session import Base
from app.models.statement import Statement
from app.services.pipeline import process_pdf
from app.services.pdf import extract_text_from_pdf


FIXTURES = Path(__file__).parent / "fixtures"


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


def test_extract_nubank_pdf_text():
    pdf = FIXTURES / "nubank_sample.pdf"
    assert pdf.exists()
    text = extract_text_from_pdf(pdf)
    assert "Nubank" in text or "nubank" in text.lower()
    assert "IFOOD" in text.upper()


def test_process_nubank_pdf(db_session, tmp_path: Path):
    src = FIXTURES / "nubank_sample.pdf"
    dest = tmp_path / "nubank_sample.pdf"
    dest.write_bytes(src.read_bytes())
    statement = process_pdf(db_session, dest, move_to_processed=False)
    assert statement.bank == "nubank"
    assert len(statement.transactions) >= 5
    db_session.refresh(statement)
    saved = db_session.scalar(select(Statement).where(Statement.id == statement.id))
    assert saved is not None
    assert saved.total_amount > 0


def test_process_inter_pdf(db_session, tmp_path: Path):
    src = FIXTURES / "inter_sample.pdf"
    dest = tmp_path / "inter_sample.pdf"
    dest.write_bytes(src.read_bytes())
    statement = process_pdf(db_session, dest, move_to_processed=False)
    assert statement.bank == "inter"
    assert len(statement.transactions) >= 5
