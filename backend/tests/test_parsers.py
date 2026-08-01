from pathlib import Path

from app.parsers.inter import parse_inter
from app.parsers.nubank import parse_nubank
from app.parsers.base import detect_bank, parse_statement_text

FIXTURES = Path(__file__).parent / "fixtures"


def test_detect_nubank():
    text = (FIXTURES / "nubank_sample.txt").read_text(encoding="utf-8")
    assert detect_bank(text) == "nubank"


def test_detect_inter():
    text = (FIXTURES / "inter_sample.txt").read_text(encoding="utf-8")
    assert detect_bank(text) == "inter"


def test_parse_nubank_transactions():
    text = (FIXTURES / "nubank_sample.txt").read_text(encoding="utf-8")
    result = parse_nubank(text)
    assert result.bank == "nubank"
    assert len(result.transactions) >= 7
    descriptions = [t.description.lower() for t in result.transactions]
    assert any("ifood" in d for d in descriptions)
    assert not any("pagamento recebido" in d for d in descriptions)
    assert result.total_amount == 1234.56


def test_parse_inter_transactions():
    text = (FIXTURES / "inter_sample.txt").read_text(encoding="utf-8")
    result = parse_inter(text)
    assert result.bank == "inter"
    assert len(result.transactions) >= 6
    assert not any("pagamento efetuado" in t.description.lower() for t in result.transactions)


def test_parse_statement_text_routes():
    text = (FIXTURES / "nubank_sample.txt").read_text(encoding="utf-8")
    result = parse_statement_text(text)
    assert result.bank == "nubank"
    assert result.transactions
