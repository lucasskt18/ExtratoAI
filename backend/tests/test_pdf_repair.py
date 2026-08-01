from pathlib import Path

from app.services.pdf import extract_text_from_pdf, find_pdf_offset, repair_pdf_file


def test_repair_leading_nulls(tmp_path: Path):
    src = Path(__file__).parent / "fixtures" / "nubank_sample.pdf"
    dirty = tmp_path / "dirty.pdf"
    dirty.write_bytes(b"\x00" * 1000 + src.read_bytes())

    assert find_pdf_offset(dirty.read_bytes()) == 1000
    changed, msg = repair_pdf_file(dirty)
    assert changed is True
    assert dirty.read_bytes().startswith(b"%PDF")
    text = extract_text_from_pdf(dirty)
    assert "IFOOD" in text.upper() or "Nubank" in text or "nubank" in text.lower()
