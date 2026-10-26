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
        (50, 31),         # bracket 1: 0–150
        (150, 31),        # exact 'bis' boundary → still in bracket 1
        (151, 59),        # one euro above 150 → bracket 2
        (300, 59),
        (700, 84),
        (2_000, 140),
        (25_000, 974),    # bracket 7: example referenced in README
        (35_000, 974),
        (35_001, 1_914),
        (350_000, 9_576),
    ],
)
def test_tp1_brackets_valorized(streitwert: int, expected: int) -> None:
    assert pauschalgebuehr("1", streitwert) == Decimal(expected)


def test_tp1_uses_statutory_amount_when_valorized_false() -> None:
    # über 7 000 bis 35 000 → 792 EUR (Gesetz) vs. 974 EUR (valorisiert)
    assert pauschalgebuehr("1", 25_000, valorized=False) == Decimal("792")


def test_tp1_above_350k_percent_extension() -> None:
    # über 350 000 → 1,2 % vom Streitwert zuzüglich 6 964 EUR (valorisiert).
    # Beispiel: 500 000 → 1.2% * 500 000 = 6 000 + 6 964 = 12 964 EUR
    assert pauschalgebuehr("1", 500_000) == Decimal("12964")
    # Aufrundung auf nächsthöheren Euro (§ 6 Abs. 2):
    # 500 001 → 1.2% * 500 001 = 6 000.012 → aufgerundet 6 001 + 6 964 = 12 965
    assert pauschalgebuehr("1", 500_001) == Decimal("12965")


def test_tp1_ermaessigung_rueckziehung_vor_zustellung() -> None:
    # 25 000 EUR → 974 EUR; Anm. 3: ein Viertel → 243.50
    assert pauschalgebuehr(
        "1", 25_000, ermaessigung=Ermaessigung.RUECKZIEHUNG_VOR_ZUSTELLUNG
    ) == Decimal("243.50")


def test_tp1_ermaessigung_einstweilige_verfuegung() -> None:
    assert pauschalgebuehr(
        "1", 25_000, ermaessigung=Ermaessigung.EINSTWEILIGE_VERFUEGUNG
    ) == Decimal("487")


# ---------------------------------------------------------------------------
# TP 2 — Berufung / Rekurs 2. Instanz (Berufungsinteresse)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "interesse,expected",
    [
        (50, 25),
        (3_500, 374),
        (50_000, 2_815),
        (350_000, 14_083),
    ],
)
def test_tp2_brackets_valorized(interesse: int, expected: int) -> None:
    assert pauschalgebuehr("2", interesse) == Decimal(expected)


def test_tp2_above_350k_extension() -> None:
    # 1,8% + 10 106 EUR Sockel (valorisiert)
    # 400 000 → 1.8% * 400 000 = 7 200 + 10 106 = 17 306
    assert pauschalgebuehr("2", 400_000) == Decimal("17306")


# ---------------------------------------------------------------------------
# TP 3 — Revision / § 615 ZPO
# ---------------------------------------------------------------------------


def test_tp3a_bracket() -> None:
    # bis 2 000 EUR → 281 (valorisiert)
    assert pauschalgebuehr("3a", 1_500) == Decimal("281")
    # über 70 000 bis 140 000 → 7 510
    assert pauschalgebuehr("3a", 100_000) == Decimal("7510")


def test_tp3a_extension() -> None:
    # 2,4% + 13 477 EUR Sockel (valorisiert)
    # 500 000 → 2.4% * 500 000 = 12 000 + 13 477 = 25 477
    assert pauschalgebuehr("3a", 500_000) == Decimal("25477")


def test_tp3b_percent_with_minimum() -> None:
    # 5% vom Streitwert, mindestens 7 239 (valorisiert)
    # 100 000 → 5 000 < 7 239 → 7 239
    assert pauschalgebuehr("3b", 100_000) == Decimal("7239")
    # 200 000 → 10 000 > 7 239 → 10 000
    assert pauschalgebuehr("3b", 200_000) == Decimal("10000")
    # Aufrundung: 100 003 → 5 000.15 → 5 001, immer noch unter Mindestbetrag
    assert pauschalgebuehr("3b", 100_003) == Decimal("7239")


def test_tp3b_statutory_minimum() -> None:
    assert pauschalgebuehr("3b", 100_000, valorized=False) == Decimal("5884")


# ---------------------------------------------------------------------------
# TP 4 — Exekutionsverfahren
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "anspruch,expected",
    [
        (50, 34),
        (150, 34),
        (151, 62),
        (25_000, 246),
        (50_000, 369),
        (70_000, 369),  # exact boundary, top bracket
    ],
)
def test_tp4_I_a_brackets(anspruch: int, expected: int) -> None:
    assert pauschalgebuehr("4Ia", anspruch) == Decimal(expected)


def test_tp4_I_a_above_70k_promille_extension() -> None:
    # 369 EUR Sockel + 2,7 ‰ vom Überschießenden (valorisiert).
    # 100 000 EUR → 369 + ceil(30 000 * 2.7 / 1000) = 369 + ceil(81) = 369 + 81 = 450
    assert pauschalgebuehr("4Ia", 100_000) == Decimal("450")
    # 100 001 EUR → 369 + ceil(30 001 * 2.7 / 1000) = 369 + ceil(81.0027) = 369 + 82 = 451
    assert pauschalgebuehr("4Ia", 100_001) == Decimal("451")


def test_tp4_I_b_fixed() -> None:
    assert pauschalgebuehr("4Ib", 0) == Decimal("18")
    assert pauschalgebuehr("4Ib", 1_000_000) == Decimal("18")
    assert pauschalgebuehr("4Ib", 0, valorized=False) == Decimal("15")


def test_tp4_II_a_is_150_percent_of_4_I_a() -> None:
    # TP 4 Z I lit. a bei 25 000 = 246 EUR; 150% = 369 EUR
    assert pauschalgebuehr("4IIa", 25_000) == Decimal("369")
    # Bei der Promille-Stufe: 100 000 → 450 EUR (Z I); 150% = 675 EUR
    assert pauschalgebuehr("4IIa", 100_000) == Decimal("675")


def test_tp4_III_a_is_200_percent_of_4_I_a() -> None:
    assert pauschalgebuehr("4IIIa", 25_000) == Decimal("492")  # 2 * 246
    assert pauschalgebuehr("4IIIa", 100_000) == Decimal("900")  # 2 * 450


def test_tp4_fixed_higher_instances() -> None:
    assert pauschalgebuehr("4IIb", 0) == Decimal("38")
    assert pauschalgebuehr("4IIIb", 0) == Decimal("57")


def test_tp4_ermaessigung_rueckziehung_vor_bewilligung() -> None:
    # Anm. 2: Hälfte
    assert pauschalgebuehr(
        "4Ia", 25_000, ermaessigung=Ermaessigung.RUECKZIEHUNG_VOR_BEWILLIGUNG
    ) == Decimal("123")


# ---------------------------------------------------------------------------
# General behavior
# ---------------------------------------------------------------------------


def test_enum_keys_accepted() -> None:
    assert pauschalgebuehr(Tarifpost.TP1, 25_000) == Decimal("974")


def test_unknown_tarifpost_raises() -> None:
    with pytest.raises(TarifpostNotFound):
        pauschalgebuehr("99", 1_000)


def test_negative_basis_rejected() -> None:
    with pytest.raises(ValueError):
        pauschalgebuehr("1", -1)
