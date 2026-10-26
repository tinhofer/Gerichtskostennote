"""Worked-example tests for the GGG Pauschalgebühr calculator.

Each test references the relevant Tarifpost and bracket so the expectation is
verifiable against the GGG PDF in the repo root.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from gerichtskostennote import Ermaessigung, Tarifpost, TarifpostNotFound, pauschalgebuehr


# ---------------------------------------------------------------------------
# TP 1 — Zivilprozess 1. Instanz (Streitwert)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "streitwert,expected",
    [
        (50, 33),         # bracket 1: 0–150
        (150, 33),        # exact 'bis' boundary → still in bracket 1
        (151, 62),        # one euro above 150 → bracket 2
        (300, 62),
        (700, 89),
        (2_000, 148),
        (25_000, 1_030),  # bracket 7: example referenced in README
        (35_000, 1_030),
        (35_001, 2_023),
        (350_000, 10_123),
    ],
)
def test_tp1_brackets_valorized(streitwert: int, expected: int) -> None:
    assert pauschalgebuehr("1", streitwert) == Decimal(expected)


def test_tp1_uses_statutory_amount_when_valorized_false() -> None:
    # über 7 000 bis 35 000 → 792 EUR (Gesetz) vs. 1 030 EUR (valorisiert)
    assert pauschalgebuehr("1", 25_000, valorized=False) == Decimal("792")


def test_tp1_above_350k_percent_extension() -> None:
    # über 350 000 → 1,2 % vom Streitwert zuzüglich 7 908 EUR (valorisiert).
    # Beispiel: 500 000 → 1.2% * 500 000 = 6 000 + 7 908 = 13 908 EUR
    assert pauschalgebuehr("1", 500_000) == Decimal("13908")
    # Aufrundung auf nächsthöheren Euro (§ 6 Abs. 2):
    # 500 001 → 1.2% * 500 001 = 6 000.012 → aufgerundet 6 001 + 7 908 = 13 909
    assert pauschalgebuehr("1", 500_001) == Decimal("13909")


def test_tp1_ermaessigung_rueckziehung_vor_zustellung() -> None:
    # 25 000 EUR → 1 030 EUR; Anm. 3: ein Viertel → 257.50
    assert pauschalgebuehr(
        "1", 25_000, ermaessigung=Ermaessigung.RUECKZIEHUNG_VOR_ZUSTELLUNG
    ) == Decimal("257.50")


def test_tp1_ermaessigung_einstweilige_verfuegung() -> None:
    assert pauschalgebuehr(
        "1", 25_000, ermaessigung=Ermaessigung.EINSTWEILIGE_VERFUEGUNG
    ) == Decimal("515")


# ---------------------------------------------------------------------------
# TP 2 — Berufung / Rekurs 2. Instanz (Berufungsinteresse)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "interesse,expected",
    [
        (50, 26),
        (3_500, 395),
        (50_000, 2_976),
        (350_000, 14_887),
    ],
)
def test_tp2_brackets_valorized(interesse: int, expected: int) -> None:
    assert pauschalgebuehr("2", interesse) == Decimal(expected)


def test_tp2_above_350k_extension() -> None:
    # 1,8% + 11 487 EUR Sockel (valorisiert)
    # 400 000 → 1.8% * 400 000 = 7 200 + 11 487 = 18 687
    assert pauschalgebuehr("2", 400_000) == Decimal("18687")


# ---------------------------------------------------------------------------
# TP 3 — Revision / § 615 ZPO
# ---------------------------------------------------------------------------


def test_tp3a_bracket() -> None:
    # bis 2 000 EUR → 297 (valorisiert)
    assert pauschalgebuehr("3a", 1_500) == Decimal("297")
    # über 70 000 bis 140 000 → 7 939
    assert pauschalgebuehr("3a", 100_000) == Decimal("7939")


def test_tp3a_extension() -> None:
    # 2,4% + 15 318 EUR Sockel (valorisiert)
    # 500 000 → 2.4% * 500 000 = 12 000 + 15 318 = 27 318
    assert pauschalgebuehr("3a", 500_000) == Decimal("27318")


def test_tp3b_percent_with_minimum() -> None:
    # 5% vom Streitwert, mindestens 7 652 (valorisiert)
    # 100 000 → 5 000 < 7 652 → 7 652
    assert pauschalgebuehr("3b", 100_000) == Decimal("7652")
    # 200 000 → 10 000 > 7 652 → 10 000
    assert pauschalgebuehr("3b", 200_000) == Decimal("10000")
    # Aufrundung: 100 003 → 5 000.15 → 5 001, immer noch unter Mindestbetrag
    assert pauschalgebuehr("3b", 100_003) == Decimal("7652")


def test_tp3b_statutory_minimum() -> None:
    assert pauschalgebuehr("3b", 100_000, valorized=False) == Decimal("5884")


# ---------------------------------------------------------------------------
# TP 4 — Exekutionsverfahren
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "anspruch,expected",
    [
        (50, 36),
        (150, 36),
        (151, 66),
        (25_000, 260),
        (50_000, 390),
        (70_000, 390),  # exact boundary, top bracket
    ],
)
def test_tp4_I_a_brackets(anspruch: int, expected: int) -> None:
    assert pauschalgebuehr("4Ia", anspruch) == Decimal(expected)


def test_tp4_I_a_above_70k_promille_extension() -> None:
    # 390 EUR Sockel + 2,7 ‰ vom Überschießenden (valorisiert).
    # 100 000 EUR → 390 + ceil(30 000 * 2.7 / 1000) = 390 + 81 = 471
    assert pauschalgebuehr("4Ia", 100_000) == Decimal("471")
    # 100 001 EUR → 390 + ceil(30 001 * 2.7 / 1000) = 390 + ceil(81.0027) = 390 + 82 = 472
    assert pauschalgebuehr("4Ia", 100_001) == Decimal("472")


def test_tp4_I_b_fixed() -> None:
    assert pauschalgebuehr("4Ib", 0) == Decimal("19")
    assert pauschalgebuehr("4Ib", 1_000_000) == Decimal("19")
    assert pauschalgebuehr("4Ib", 0, valorized=False) == Decimal("15")


def test_tp4_II_a_is_150_percent_of_4_I_a() -> None:
    # TP 4 Z I lit. a bei 25 000 = 260 EUR; 150% = 390 EUR
    assert pauschalgebuehr("4IIa", 25_000) == Decimal("390")
    # Bei der Promille-Stufe: 100 000 → 471 EUR (Z I); 150% = 706,50 → aufgerundet 707
    assert pauschalgebuehr("4IIa", 100_000) == Decimal("707")


def test_tp4_III_a_is_200_percent_of_4_I_a() -> None:
    assert pauschalgebuehr("4IIIa", 25_000) == Decimal("520")  # 2 * 260
    assert pauschalgebuehr("4IIIa", 100_000) == Decimal("942")  # 2 * 471


def test_tp4_fixed_higher_instances() -> None:
    assert pauschalgebuehr("4IIb", 0) == Decimal("40")
    assert pauschalgebuehr("4IIIb", 0) == Decimal("60")


def test_tp4_ermaessigung_rueckziehung_vor_bewilligung() -> None:
    # Anm. 2: Hälfte
    assert pauschalgebuehr(
        "4Ia", 25_000, ermaessigung=Ermaessigung.RUECKZIEHUNG_VOR_BEWILLIGUNG
    ) == Decimal("130")


# ---------------------------------------------------------------------------
# General behavior
# ---------------------------------------------------------------------------


def test_enum_keys_accepted() -> None:
    assert pauschalgebuehr(Tarifpost.TP1, 25_000) == Decimal("1030")


def test_unknown_tarifpost_raises() -> None:
    with pytest.raises(TarifpostNotFound):
        pauschalgebuehr("99", 1_000)


def test_negative_basis_rejected() -> None:
    with pytest.raises(ValueError):
        pauschalgebuehr("1", -1)


# ---------------------------------------------------------------------------
# Datenintegrität: Valorisierung BGBl. II Nr. 227/2026
# ---------------------------------------------------------------------------


def _walk(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v)


@pytest.mark.parametrize(
    "filename",
    [
        "tp1_zivilprozess_erste_instanz.json",
        "tp2_zivilprozess_zweite_instanz.json",
        "tp3_zivilprozess_dritte_instanz.json",
        "tp4_exekutionsverfahren.json",
    ],
)
def test_every_2025_value_has_a_higher_2026_value(filename: str) -> None:
    import json
    from pathlib import Path

    data = json.loads(
        (Path(__file__).parent.parent / "data" / "ggg" / filename).read_text()
    )
    checked = 0
    for node in _walk(data):
        for key, old in node.items():
            if not key.endswith("_ab_2025_04_01"):
                continue
            new_key = key.replace("_ab_2025_04_01", "_ab_2026_08_01")
            assert new_key in node, f"{filename}: {key} ohne {new_key}"
            assert node[new_key] > old, f"{filename}: {new_key} nicht höher als {key}"
            checked += 1
    assert checked > 0


# ---------------------------------------------------------------------------
# Datenintegrität: Budgetbegleitgesetz 2027-2028 (BGBl. I Nr. 62/2026)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "filename,path,jn_neu,ev_neu",
    [
        ("tp1_zivilprozess_erste_instanz.json", ("Z_I", "spezialgebuehren"), 410, 205),
        ("tp2_zivilprozess_zweite_instanz.json", ("spezialgebuehren",), 449, 224),
        ("tp3_zivilprozess_dritte_instanz.json", ("spezialgebuehren",), 671, 335),
    ],
)
def test_bbg_2026_spezialgebuehren(filename, path, jn_neu, ev_neu) -> None:
    import json
    from pathlib import Path

    node = json.loads(
        (Path(__file__).parent.parent / "data" / "ggg" / filename).read_text()
    )
    for key in path:
        node = node[key]
    assert node["jn_49_2_2a_2b"]["gilt_bis"] == "2026-09-30"
    assert node["jn_49_2_2a_2d"]["betrag_ab_2026_10_01"] == jn_neu
    assert node["jn_49_2_2a_2d"]["gilt_ab"] == "2026-10-01"
    ev = next(v for k, v in node.items() if k.startswith("ev_382b_382d_eo"))
    assert ev["betrag_ab_2026_10_01"] == ev_neu
    assert ev["gilt_ab"] == "2026-10-01"
