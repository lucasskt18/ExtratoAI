from pathlib import Path

from app.parsers.inter import parse_inter
from app.parsers.itau import parse_itau
from app.parsers.nubank import parse_nubank
from app.parsers.base import detect_bank, parse_statement_text

FIXTURES = Path(__file__).parent / "fixtures"


def test_detect_nubank():
    text = (FIXTURES / "nubank_sample.txt").read_text(encoding="utf-8")
    assert detect_bank(text) == "nubank"


def test_detect_inter():
    text = (FIXTURES / "inter_sample.txt").read_text(encoding="utf-8")
    assert detect_bank(text) == "inter"


def test_detect_itau():
    text = (FIXTURES / "itau_sample.txt").read_text(encoding="utf-8")
    assert detect_bank(text) == "itau"


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
    assert len(result.transactions) >= 7
    assert any(t.installment == "1/3" for t in result.transactions)
    assert any(t.amount < 0 for t in result.transactions)  # pagamento
    assert not any("pagamento efetuado" in t.description.lower() for t in result.transactions)
    assert result.total_amount == 890.25


def test_parse_itau_transactions():
    text = (FIXTURES / "itau_sample.txt").read_text(encoding="utf-8")
    result = parse_itau(text)
    assert result.bank == "itau"
    assert abs(result.total_amount - 46.21) < 0.01
    assert len(result.transactions) == 13

    amounts = [round(t.amount, 2) for t in result.transactions]
    assert 943.79 not in amounts
    assert 990.0 not in amounts
    # First monetary value on mixed lines (purchase, not side-column fee)
    assert 13.99 in amounts
    assert 16.50 in amounts
    assert 30.98 in amounts
    assert 0.4 in amounts  # MULTA standalone charge

    descriptions = " ".join(t.description.lower() for t in result.transactions)
    assert "pagamento" not in descriptions
    assert "limite" not in descriptions
    assert "padaria" in descriptions


def test_parse_statement_text_routes_itau():
    text = (FIXTURES / "itau_sample.txt").read_text(encoding="utf-8")
    result = parse_statement_text(text)
    assert result.bank == "itau"
    assert abs(result.total_amount - 46.21) < 0.01


def test_parse_statement_text_routes():
    text = (FIXTURES / "nubank_sample.txt").read_text(encoding="utf-8")
    result = parse_statement_text(text)
    assert result.bank == "nubank"
    assert result.transactions
