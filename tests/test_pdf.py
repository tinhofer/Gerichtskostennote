"""Tests for the PDF renderer + CLI PDF dispatch."""

from __future__ import annotations

from pathlib import Path

import pytest

from gerichtskostennote.cli import _resolve_format, main as cli_main
from gerichtskostennote.renderer import compute

reportlab = pytest.importorskip("reportlab")
pypdf = pytest.importorskip("pypdf")

from gerichtskostennote.pdf import render_pdf  # noqa: E402 — must follow importorskip


EXAMPLE_PATH = Path(__file__).parent.parent / "examples" / "klage_15000.json"


def _pdf_text(path: Path) -> str:
    """Concatenate text from every page of a PDF."""
    reader = pypdf.PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def test_render_pdf_produces_valid_pdf(tmp_path: Path) -> None:
    import json
    note = compute(json.loads(EXAMPLE_PATH.read_text()))
    target = tmp_path / "note.pdf"
    render_pdf(note, target)

    assert target.exists()
    assert target.stat().st_size > 500  # not just an empty file
    assert target.read_bytes()[:4] == b"%PDF"


def test_render_pdf_contains_key_facts(tmp_path: Path) -> None:
    import json
    note = compute(json.loads(EXAMPLE_PATH.read_text()))
    target = tmp_path / "note.pdf"
    render_pdf(note, target)

    text = _pdf_text(target)
    assert "Kostennote" in text
    assert "1 Cg 123/26x" in text
    assert "Hans Mustermann" in text
    assert "Streitwert" in text
    assert "15.000,00" in text
    # Anwaltskosten totals
    assert "487,00" in text
    assert "1.208,46" in text or "1.208,46" in text.replace(" ", "")
    assert "241,69" in text  # USt
    assert "1.450,15" in text  # brutto
    # GGG
    assert "974,00" in text
    # Gesamt
    assert "2.424,15" in text


def test_render_pdf_handles_minimal_payload(tmp_path: Path) -> None:
    """An almost-empty payload should still produce a valid PDF without crashing."""
    note = compute({"streitwert": 1000})
    target = tmp_path / "minimal.pdf"
    render_pdf(note, target)
    assert target.read_bytes()[:4] == b"%PDF"
    text = _pdf_text(target)
    assert "Gesamtsumme" in text


def test_render_pdf_returns_path(tmp_path: Path) -> None:
    note = compute({"streitwert": 1000})
    target = tmp_path / "ret.pdf"
    result = render_pdf(note, target)
    assert result == target


# ---------------------------------------------------------------------------
# CLI dispatch
# ---------------------------------------------------------------------------


def test_resolve_format_pdf_by_suffix(tmp_path: Path) -> None:
    assert _resolve_format(tmp_path / "note.pdf", None) == "pdf"
    assert _resolve_format(tmp_path / "note.PDF", None) == "pdf"


def test_resolve_format_markdown_default(tmp_path: Path) -> None:
    assert _resolve_format(None, None) == "markdown"
    assert _resolve_format(tmp_path / "note.md", None) == "markdown"
    assert _resolve_format(tmp_path / "note.txt", None) == "markdown"


def test_resolve_format_explicit_overrides_suffix(tmp_path: Path) -> None:
    # Explicit flag wins
    assert _resolve_format(tmp_path / "note.md", "pdf") == "pdf"
    assert _resolve_format(tmp_path / "note.pdf", "markdown") == "markdown"


def test_cli_writes_pdf_when_output_ends_in_pdf(tmp_path: Path) -> None:
    target = tmp_path / "fromcli.pdf"
    exit_code = cli_main([str(EXAMPLE_PATH), "-o", str(target)])
    assert exit_code == 0
    assert target.read_bytes()[:4] == b"%PDF"
    text = _pdf_text(target)
    assert "2.424,15" in text


def test_cli_pdf_via_explicit_format(tmp_path: Path) -> None:
    target = tmp_path / "note.out"  # non-pdf suffix
    exit_code = cli_main([str(EXAMPLE_PATH), "-o", str(target), "-f", "pdf"])
    assert exit_code == 0
    assert target.read_bytes()[:4] == b"%PDF"


def test_cli_pdf_without_output_returns_error(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli_main([str(EXAMPLE_PATH), "-f", "pdf"])
    assert exit_code == 2
    err = capsys.readouterr().err
    assert "PDF" in err
