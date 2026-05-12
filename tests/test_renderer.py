"""Tests for the Kostennote renderer + CLI."""

from __future__ import annotations

import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

from gerichtskostennote.cli import main as cli_main
from gerichtskostennote.renderer import (
    InputError,
    compute,
    render_markdown,
)


EXAMPLE_PATH = Path(__file__).parent.parent / "examples" / "klage_15000.json"


def _example_payload() -> dict:
    return json.loads(EXAMPLE_PATH.read_text())


# ---------------------------------------------------------------------------
# compute() — totals
# ---------------------------------------------------------------------------


def test_compute_streitwert_passed_through() -> None:
    note = compute(_example_payload())
    assert note.streitwert == Decimal("15000")


def test_compute_first_leistung_klage_tp3a() -> None:
    note = compute(_example_payload())
    row = note.leistungen[0]
    assert row.tp == "3a"
    assert row.verdienst == Decimal("487.00")
    assert row.einheitssatz == Decimal("243.50")
    assert row.streitgenossen == Decimal("73.05")
    assert row.netto == Decimal("803.55")


def test_compute_second_leistung_schriftsatz_tp2() -> None:
    note = compute(_example_payload())
    row = note.leistungen[1]
    # TP 2 bei 15 000: 173.80 + ceil((15000-10170)/1450) * 17.90 = 173.80 + 4*17.90 = 245.40
    assert row.verdienst == Decimal("245.40")
    assert row.einheitssatz == Decimal("122.70")  # 50 % über 10 170
    assert row.streitgenossen == Decimal("36.81")  # 10 % auf 368.10
    assert row.netto == Decimal("404.91")


def test_compute_anwalt_totals() -> None:
    note = compute(_example_payload())
    assert note.anwalt_netto == Decimal("1208.46")
    assert note.umsatzsteuer == Decimal("241.69")
    assert note.anwalt_brutto == Decimal("1450.15")


def test_compute_gerichtsgebuehren() -> None:
    note = compute(_example_payload())
    assert len(note.gerichtsgebuehren) == 1
    assert note.gerichtsgebuehren[0].betrag == Decimal("974")  # TP 1 valorisiert
    assert note.gerichts_summe == Decimal("974")


def test_compute_gesamtsumme() -> None:
    note = compute(_example_payload())
    assert note.gesamt == Decimal("2424.15")


def test_compute_missing_streitwert_rejected() -> None:
    with pytest.raises(InputError):
        compute({})


def test_compute_minimal_payload_only_streitwert() -> None:
    note = compute({"streitwert": 1000})
    assert note.streitwert == Decimal("1000")
    assert note.leistungen == []
    assert note.gerichtsgebuehren == []
    assert note.gesamt == Decimal("0.00")


def test_compute_respects_per_leistung_personen_override() -> None:
    payload = {
        "streitwert": 5000,
        "default_personen_einer_seite": 2,
        "anwaltsleistungen": [
            {"tp": "3a", "beschreibung": "A", "personen_einer_seite": 1},
            {"tp": "3a", "beschreibung": "B"},  # falls back to default
        ],
    }
    note = compute(payload)
    assert note.leistungen[0].streitgenossen == Decimal("0.00")
    assert note.leistungen[1].streitgenossen > 0


def test_compute_with_ggg_ermaessigung() -> None:
    payload = {
        "streitwert": 25_000,
        "gerichtsgebuehren": [
            {
                "tp": "1",
                "beschreibung": "Klage zurückgezogen vor Zustellung",
                "ermaessigung": "rueckziehung_vor_zustellung",
            }
        ],
    }
    note = compute(payload)
    # 974 / 4 = 243.50
    assert note.gerichtsgebuehren[0].betrag == Decimal("243.50")


# ---------------------------------------------------------------------------
# render_markdown()
# ---------------------------------------------------------------------------


def test_render_markdown_contains_key_facts() -> None:
    note = compute(_example_payload())
    md = render_markdown(note)
    # Header
    assert "# Kostennote" in md
    assert "1 Cg 123/26x" in md
    assert "Hans Mustermann, Maria Mustermann" in md
    # Table headers
    assert "| Datum | TP | Beschreibung |" in md
    # Computed amounts (German number formatting)
    assert "487,00" in md  # TP 3a verdienst
    assert "974,00" in md  # GGG TP 1
    assert "2.424,15" in md  # Gesamt


def test_render_markdown_omits_empty_sections() -> None:
    note = compute({"streitwert": 1000})
    md = render_markdown(note)
    assert "## Anwaltskosten" not in md
    assert "## Gerichtsgebühren" not in md
    assert "## Gesamt" in md


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_cli_writes_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli_main([str(EXAMPLE_PATH)])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "# Kostennote" in out
    assert "2.424,15" in out


def test_cli_writes_to_output_file(tmp_path: Path) -> None:
    target = tmp_path / "note.md"
    exit_code = cli_main([str(EXAMPLE_PATH), "-o", str(target)])
    assert exit_code == 0
    assert "# Kostennote" in target.read_text()


def test_cli_reads_stdin(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    import io
    monkeypatch.setattr("sys.stdin", io.StringIO('{"streitwert": 1000}'))
    exit_code = cli_main(["-"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "# Kostennote" in out


def test_console_script_installed() -> None:
    """Smoke-test the installed `gkn` console_script entry point."""
    result = subprocess.run(
        [sys.executable, "-m", "gerichtskostennote", str(EXAMPLE_PATH)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "# Kostennote" in result.stdout
