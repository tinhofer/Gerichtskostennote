"""Worked-example tests for RATG TP 1/2/3A tariff and § 23/§ 15 rules."""

from __future__ import annotations

from decimal import Decimal

import pytest

from gerichtskostennote import (
    TarifpostNotFound,
    einheitssatz,
    streitgenossenzuschlag,
    tarifsatz,
)
from gerichtskostennote.ratg import Tarifpost as RatgTarifpost


# ---------------------------------------------------------------------------
# tarifsatz — bracket lookups (12 fixed stages up to 10 170 EUR)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "basis,expected",
    [
        # bis 40 → Anm. 1 = 4.20 (valorisiert) bzw. 2.70 (Gesetz)
        (40, "4.20"),
        # Genau am 'bis'-Boundary → noch im niedrigeren Bracket
        (70, "5.90"),
        (71, "7.50"),
        (10_170, "35.10"),
    ],
)
def test_tp1_brackets_valorized(basis: int, expected: str) -> None:
    assert tarifsatz("1", basis) == Decimal(expected)


def test_tp1_statutory_amount() -> None:
    assert tarifsatz("1", 10_170, valorized=False) == Decimal("23.30")


@pytest.mark.parametrize(
    "basis,expected",
    [
        (40, "17.90"),
        (3_000, "87.00"),
        (10_170, "173.80"),
    ],
)
def test_tp2_brackets(basis: int, expected: str) -> None:
    assert tarifsatz("2", basis) == Decimal(expected)


@pytest.mark.parametrize(
    "basis,expected",
    [
        (40, "35.10"),
        (5_000, "208.20"),  # über 3 630 bis 5 450 → Anm. 10 = 208.20
        (10_170, "346.60"),  # über 7 270 bis 10 170 → Anm. 12 = 346.60
    ],
)
def test_tp3a_brackets(basis: int, expected: str) -> None:
    assert tarifsatz("3a", basis) == Decimal(expected)


# ---------------------------------------------------------------------------
# tarifsatz — incremental stage (über 10 170 bis 34 820 EUR, je 1 450 EUR)
# ---------------------------------------------------------------------------


def test_tp3a_incremental_15000() -> None:
    # Bei Streitwert 15 000 EUR:
    #   ceil((15 000 - 10 170) / 1 450) = ceil(3.33) = 4 Schritte á 35.10
    #   346.60 + 4 * 35.10 = 487.00
    assert tarifsatz("3a", 15_000) == Decimal("487.00")


def test_tp3a_incremental_just_above_10170() -> None:
    # 10 171 EUR → 1 Schritt
    assert tarifsatz("3a", 10_171) == Decimal("381.70")  # 346.60 + 35.10


def test_tp3a_full_incremental_at_34820() -> None:
    # Genau 34 820: ceil(17.0) = 17 Schritte
    # 346.60 + 17 * 35.10 = 346.60 + 596.70 = 943.30
    assert tarifsatz("3a", 34_820) == Decimal("943.30")


def test_tp3a_extra_step_between_34820_and_36340() -> None:
    # 34 821 bis 36 340 → 17 Schritte + 1 = 18 Schritte
    # 346.60 + 18 * 35.10 = 346.60 + 631.80 = 978.40
    assert tarifsatz("3a", 35_000) == Decimal("978.40")
    assert tarifsatz("3a", 36_340) == Decimal("978.40")


# ---------------------------------------------------------------------------
# tarifsatz — Promille-Stufen oberhalb von 36 340 EUR
# ---------------------------------------------------------------------------


def test_tp3a_promille_first_slice() -> None:
    # 100 000 EUR → 978.40 + (100 000 - 36 340) * 1 / 1 000 = 978.40 + 63.66
    assert tarifsatz("3a", 100_000) == Decimal("1042.06")


def test_tp3a_promille_at_363360() -> None:
    # Genau am oberen Promille-Boundary:
    # 978.40 + (363 360 - 36 340) * 1 / 1 000 = 978.40 + 327.02 = 1 305.42
    assert tarifsatz("3a", 363_360) == Decimal("1305.42")


def test_tp3a_promille_second_slice() -> None:
    # 1 000 000 EUR:
    # 978.40 + (363 360 - 36 340) * 1/1000 + (1 000 000 - 363 360) * 0.5/1000
    # = 978.40 + 327.02 + 318.32 = 1 623.74
    assert tarifsatz("3a", 1_000_000) == Decimal("1623.74")


def test_tp1_promille_for_very_high_basis() -> None:
    # TP 1 Promille1 = 0.1 vT, Promille2 = 0.05 vT
    # base_at_36340 für TP 1: 35.10 + 18 * 4.20 = 35.10 + 75.60 = 110.70
    # bei 100 000: 110.70 + (100 000 - 36 340) * 0.1/1000 = 110.70 + 6.366 = 117.07
    assert tarifsatz("1", 100_000) == Decimal("117.07")


# ---------------------------------------------------------------------------
# tarifsatz — Cap-Verhalten
# ---------------------------------------------------------------------------


def test_tp1_cap_at_very_high_basis() -> None:
    # TP 1 cap (valorisiert) = 312.20 EUR — bei extrem hohem Streitwert greift Cap
    assert tarifsatz("1", 100_000_000) == Decimal("312.20")


def test_tp2_cap_at_very_high_basis() -> None:
    assert tarifsatz("2", 100_000_000) == Decimal("1558.20")


def test_tp3a_cap_at_very_high_basis() -> None:
    assert tarifsatz("3a", 100_000_000) == Decimal("20770.60")


# ---------------------------------------------------------------------------
# tarifsatz — Misc.
# ---------------------------------------------------------------------------


def test_enum_keys_accepted() -> None:
    assert tarifsatz(RatgTarifpost.TP3A, 5_000) == Decimal("208.20")


def test_unknown_tarifpost_rejected() -> None:
    with pytest.raises(TarifpostNotFound):
        tarifsatz("99", 1_000)


def test_negative_basis_rejected() -> None:
    with pytest.raises(ValueError):
        tarifsatz("1", -1)


# ---------------------------------------------------------------------------
# § 23 Einheitssatz
# ---------------------------------------------------------------------------


def test_einheitssatz_60_percent_below_threshold() -> None:
    # TP 3A bei 5 000 EUR → 208.20; ES = 60 % = 124.92
    verdienst = tarifsatz("3a", 5_000)
    assert einheitssatz(5_000, verdienst) == Decimal("124.92")


def test_einheitssatz_60_percent_at_exact_threshold() -> None:
    # Streitwert genau 10 170 EUR → 60 %
    verdienst = tarifsatz("3a", 10_170)
    assert einheitssatz(10_170, verdienst) == Decimal("207.96")  # 346.60 * 0.60


def test_einheitssatz_50_percent_above_threshold() -> None:
    # Streitwert über 10 170 EUR → 50 %
    verdienst = tarifsatz("3a", 15_000)  # 487.00
    assert einheitssatz(15_000, verdienst) == Decimal("243.50")


def test_einheitssatz_multiplier_doubled() -> None:
    # § 23 Abs. 5 etc.: Verdoppelung
    verdienst = tarifsatz("3a", 5_000)  # 208.20
    assert einheitssatz(5_000, verdienst, multiplier=2) == Decimal("249.84")


def test_einheitssatz_rejects_negative() -> None:
    with pytest.raises(ValueError):
        einheitssatz(-1, 100)


# ---------------------------------------------------------------------------
# § 15 Streitgenossenzuschlag
# ---------------------------------------------------------------------------


def test_streitgenossen_zero_when_only_one_party() -> None:
    assert streitgenossenzuschlag(1_000, 1) == Decimal("0.00")


def test_streitgenossen_zero_when_zero_personen() -> None:
    assert streitgenossenzuschlag(1_000, 0) == Decimal("0.00")


def test_streitgenossen_10_percent_for_two_on_one_side() -> None:
    assert streitgenossenzuschlag(1_000, 2) == Decimal("100.00")


def test_streitgenossen_15_percent_for_three_on_one_side() -> None:
    # 10 % + 1 weitere × 5 % = 15 %
    assert streitgenossenzuschlag(1_000, 3) == Decimal("150.00")


def test_streitgenossen_with_additional_on_other_side() -> None:
    # 2 Personen auf einer Seite (= 10 %) + 1 weitere Person auf der anderen
    # Seite (+ 5 %) = 15 %
    assert streitgenossenzuschlag(1_000, 2, weitere_personen_andere_seite=1) == Decimal(
        "150.00"
    )


def test_streitgenossen_capped_at_50_percent() -> None:
    # 2 + 50 weitere → würden 260 % bedeuten, kappt bei 50 %
    assert streitgenossenzuschlag(1_000, 52) == Decimal("500.00")


def test_streitgenossen_at_exact_cap_boundary() -> None:
    # 10 weitere Personen → 10% + 9 * 5% = 55% → kappt bei 50 %
    assert streitgenossenzuschlag(1_000, 11) == Decimal("500.00")
    # 9 weitere Personen → 10% + 8 * 5% = 50 % → kein Cap-Eingriff
    assert streitgenossenzuschlag(1_000, 10) == Decimal("500.00")


def test_streitgenossen_rejects_negative_basis() -> None:
    with pytest.raises(ValueError):
        streitgenossenzuschlag(-1, 2)


def test_streitgenossen_rejects_negative_counts() -> None:
    with pytest.raises(ValueError):
        streitgenossenzuschlag(100, -1)
    with pytest.raises(ValueError):
        streitgenossenzuschlag(100, 2, weitere_personen_andere_seite=-1)


# ---------------------------------------------------------------------------
# Integration smoke test — full Kostenposition für eine Klage
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# TP 3 Teil B — Berufungen, Rekurse, Beschwerden
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "basis,expected",
    [
        (40, "43.70"),         # bracket 1
        (3_000, "216.90"),     # über 1 820 bis 3 630 → Anm. 9
        (10_170, "433.20"),    # Top bracket
    ],
)
def test_tp3b_brackets(basis: int, expected: str) -> None:
    assert tarifsatz("3b", basis) == Decimal(expected)


def test_tp3b_incremental_at_15000() -> None:
    # ceil((15 000 - 10 170) / 1 450) = 4 Schritte á 43.70
    # 433.20 + 4 * 43.70 = 433.20 + 174.80 = 608.00
    assert tarifsatz("3b", 15_000) == Decimal("608.00")


def test_tp3b_extra_step_at_36340() -> None:
    # Genau am Übergangspunkt: 433.20 + 18 * 43.70 = 1 219.80
    assert tarifsatz("3b", 36_340) == Decimal("1219.80")


def test_tp3b_promille_first_slice() -> None:
    # 50 000 → 1 219.80 + (50 000 - 36 340) * 1.25 / 1 000
    # = 1 219.80 + 13 660 * 0.00125 = 1 219.80 + 17.075 → 1 236.88
    assert tarifsatz("3b", 50_000) == Decimal("1236.88")


def test_tp3b_cap_at_very_high_basis() -> None:
    assert tarifsatz("3b", 100_000_000) == Decimal("25963.20")


# ---------------------------------------------------------------------------
# TP 3 Teil C — Revisionen, OGH-Schriftsätze
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "basis,expected",
    [
        (40, "52.50"),
        (3_000, "260.20"),
        (10_170, "519.60"),
    ],
)
def test_tp3c_brackets(basis: int, expected: str) -> None:
    assert tarifsatz("3c", basis) == Decimal(expected)


def test_tp3c_incremental_at_15000() -> None:
    # 519.60 + 4 * 52.50 = 519.60 + 210.00 = 729.60
    assert tarifsatz("3c", 15_000) == Decimal("729.60")


def test_tp3c_extra_step_at_36340() -> None:
    # 519.60 + 18 * 52.50 = 519.60 + 945.00 = 1 464.60
    assert tarifsatz("3c", 36_340) == Decimal("1464.60")


def test_tp3c_promille_first_slice() -> None:
    # 100 000 → 1 464.60 + (100 000 - 36 340) * 1.5 / 1 000
    # = 1 464.60 + 63 660 * 0.0015 = 1 464.60 + 95.49 = 1 560.09
    assert tarifsatz("3c", 100_000) == Decimal("1560.09")


def test_tp3c_promille_second_slice() -> None:
    # 1 000 000 → 1 464.60 + slice1 + slice2
    # slice1 = (363 360 - 36 340) * 1.5 / 1 000 = 327 020 * 0.0015 = 490.53
    # slice2 = (1 000 000 - 363 360) * 0.75 / 1 000 = 636 640 * 0.00075 = 477.48
    # Total = 1 464.60 + 490.53 + 477.48 = 2 432.61
    assert tarifsatz("3c", 1_000_000) == Decimal("2432.61")


def test_tp3c_cap_at_very_high_basis() -> None:
    assert tarifsatz("3c", 100_000_000) == Decimal("31155.80")


# ---------------------------------------------------------------------------
# Integration smoke test — Berufung-Kostenposition
# ---------------------------------------------------------------------------


def test_kostenposition_berufung_50000_streitwert() -> None:
    """Klassische Berufungs-Kostenposition: TP 3B, Berufungsinteresse 50 000 EUR,
    Berufungswerber tritt allein auf."""
    bw = Decimal("50000")

    verdienst = tarifsatz("3b", bw)        # 1236.88
    es = einheitssatz(bw, verdienst)       # 50 % → 618.44

    assert verdienst == Decimal("1236.88")
    assert es == Decimal("618.44")
    assert verdienst + es == Decimal("1855.32")


def test_kostenposition_klage_15000_streitwert() -> None:
    """Typische Kostenposition: Klage nach TP 3A, Streitwert 15 000 EUR,
    Kläger vertritt zwei Personen gegen einen Beklagten."""
    sw = Decimal("15000")

    verdienst = tarifsatz("3a", sw)         # 487.00
    es = einheitssatz(sw, verdienst)        # 50 % → 243.50
    sg = streitgenossenzuschlag(verdienst + es, 2)  # 10 % auf 730.50 = 73.05

    assert verdienst == Decimal("487.00")
    assert es == Decimal("243.50")
    assert sg == Decimal("73.05")
    assert verdienst + es + sg == Decimal("803.55")
