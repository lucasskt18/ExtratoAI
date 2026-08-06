"""Generate sample statement PDFs from text fixtures."""

from pathlib import Path

from fpdf import FPDF

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


def make_pdf(text_path: Path, pdf_path: Path) -> None:
    pdf = FPDF()
    pdf.set_auto_page_break(True, 15)
    pdf.add_page()
    pdf.set_margins(15, 15, 15)
    pdf.set_font("Helvetica", size=11)
    for line in text_path.read_text(encoding="utf-8").splitlines():
        safe = line.encode("latin-1", "replace").decode("latin-1")
        pdf.set_x(15)
        pdf.cell(0, 7, safe, new_x="LMARGIN", new_y="NEXT")
    pdf.output(str(pdf_path))


def main() -> None:
    for bank in ("nubank", "inter", "itau"):
        make_pdf(FIXTURES / f"{bank}_sample.txt", FIXTURES / f"{bank}_sample.pdf")
    print("Wrote sample PDFs to", FIXTURES)


if __name__ == "__main__":
    main()
