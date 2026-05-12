"""Entlohnungsberechnung nach Rechtsanwaltstarifgesetz (RATG)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal
from enum import Enum
from pathlib import Path
from typing import Final

from gerichtskostennote.ggg import TarifpostNotFound

_DATA_DIR: Final = Path(__file__).resolve().parents[2] / "data" / "ratg"

_CENT: Final = Decimal("0.01")


__all__ = [
    "TarifpostNotFound",
    "Tarifpost",
    "ErvKind",
    "tarifsatz",
    "tagsatzung_verdienst",
    "einheitssatz",
    "streitgenossenzuschlag",
    "erv_erhoehung",
]


class Tarifpost(str, Enum):
    """Supported RATG Tarifposten (Anl. 1)."""

    TP1 = "1"
    TP2 = "2"
    TP3A = "3a"
    TP3B = "3b"
    TP3C = "3c"


class ErvKind(str, Enum):
    """Erhöhungsarten nach § 23a RATG."""

    EINLEITEND = "einleitend"
    WEITERER = "weiterer"
    GRUNDBUCH_FIRMENBUCH = "grundbuch_firmenbuch"


@dataclass(frozen=True)
class _Bracket:
    ueber: Decimal
    bis: Decimal
    betrag_gesetz: Decimal
    betrag_valorisiert: Decimal


@dataclass(frozen=True)
class _TPSpec:
    brackets: tuple[_Bracket, ...]
    step_gesetz: Decimal
    step_valorisiert: Decimal
    promille_lower_vT: Decimal
    promille_upper_vT: Decimal
    cap_gesetz: Decimal
    cap_valorisiert: Decimal


_CACHE: dict[Tarifpost, _TPSpec] = {}

# Shared overflow thresholds (RATG Anl. 1; identical across TP 1, 2, 3A and other
# bracket-driven Tarifposten — see data/ratg/index.json#shared_overflow_rules).
_THRESHOLD_INCREMENTAL_LOWER: Final = Decimal(10170)
_THRESHOLD_INCREMENTAL_UPPER: Final = Decimal(34820)
_INCREMENTAL_STEP_SIZE: Final = Decimal(1450)
_THRESHOLD_EXTRA_STEP_UPPER: Final = Decimal(36340)
_THRESHOLD_PROMILLE_UPPER: Final = Decimal(363360)


def _D(value) -> Decimal:
    return Decimal(str(value))


def _bracket(raw: dict) -> _Bracket:
    return _Bracket(
        ueber=_D(raw["ueber"]),
        bis=_D(raw["bis"]),
        betrag_gesetz=_D(raw["betrag_gesetz"]),
        betrag_valorisiert=_D(raw["betrag_ab_2023_05_01"]),
    )


def _load() -> None:
    if _CACHE:
        return
    for tp, filename in (
        (Tarifpost.TP1, "tp1.json"),
        (Tarifpost.TP2, "tp2.json"),
        (Tarifpost.TP3A, "tp3a.json"),
        (Tarifpost.TP3B, "tp3b.json"),
        (Tarifpost.TP3C, "tp3c.json"),
    ):
        raw = json.loads((_DATA_DIR / filename).read_text())
        _CACHE[tp] = _TPSpec(
            brackets=tuple(_bracket(b) for b in raw["brackets"]),
            step_gesetz=_D(raw["step_per_1450_above_10170"]["betrag_gesetz"]),
            step_valorisiert=_D(
                raw["step_per_1450_above_10170"]["betrag_ab_2023_05_01"]
            ),
            promille_lower_vT=_D(raw["promille_36340_to_363360_vT"]),
            promille_upper_vT=_D(raw["promille_above_363360_vT"]),
            cap_gesetz=_D(raw["cap"]["betrag_gesetz"]),
            cap_valorisiert=_D(raw["cap"]["betrag_ab_2023_05_01"]),
        )


def _resolve_tp(tp: str | Tarifpost) -> Tarifpost:
    if isinstance(tp, Tarifpost):
        return tp
    try:
        return Tarifpost(tp)
    except ValueError as exc:
        raise TarifpostNotFound(tp) from exc


def _to_cents(amount: Decimal) -> Decimal:
    return amount.quantize(_CENT, rounding=ROUND_HALF_UP)


def tarifsatz(
    tp: str | Tarifpost,
    basis: float | int | Decimal,
    *,
    valorized: bool = True,
) -> Decimal:
    """Tariflicher Entlohnungsbetrag (Verdienstsumme im Sinn der RATG-Diktion)
    für eine einzelne Leistung nach RATG Anl. 1.

    :param tp: Tarifpost-Kennung (z. B. ``"1"``, ``"2"``, ``"3a"``).
    :param basis: Bemessungsgrundlage in Euro.
    :param valorized: ``True`` (default) → Beträge nach BGBl. II Nr. 131/2023
        (in Kraft seit 1.5.2023); ``False`` → Gesetzeswortlaut.
    :returns: Verdienstsumme als :class:`Decimal` mit Cent-Präzision.
    """

    _load()
    spec = _CACHE.get(_resolve_tp(tp))
    if spec is None:  # pragma: no cover — defensive
        raise TarifpostNotFound(tp)
    basis_d = _D(basis)
    if basis_d < 0:
        raise ValueError("Bemessungsgrundlage darf nicht negativ sein")

    step = spec.step_valorisiert if valorized else spec.step_gesetz
    cap = spec.cap_valorisiert if valorized else spec.cap_gesetz

    # Stage 1: fixed brackets up to 10 170 EUR.
    if basis_d <= spec.brackets[0].bis:
        return min(
            _to_cents(
                spec.brackets[0].betrag_valorisiert
                if valorized
                else spec.brackets[0].betrag_gesetz
            ),
            cap,
        )

    base_at_10170: Decimal | None = None
    for b in spec.brackets:
        if b.ueber < basis_d <= b.bis:
            return min(
                _to_cents(b.betrag_valorisiert if valorized else b.betrag_gesetz),
                cap,
            )
        if b.bis == _THRESHOLD_INCREMENTAL_LOWER:
            base_at_10170 = b.betrag_valorisiert if valorized else b.betrag_gesetz

    assert base_at_10170 is not None, "RATG TP data must terminate at 10 170 EUR"

    # Stage 2: incremental — über 10 170 Euro bis einschließlich 34 820 Euro
    if basis_d <= _THRESHOLD_INCREMENTAL_UPPER:
        steps = (
            (basis_d - _THRESHOLD_INCREMENTAL_LOWER) / _INCREMENTAL_STEP_SIZE
        ).quantize(Decimal("1"), rounding=ROUND_CEILING)
        return min(_to_cents(base_at_10170 + steps * step), cap)

    # Stage 3: one extra step — über 34 820 bis einschließlich 36 340
    steps_to_34820 = (
        (_THRESHOLD_INCREMENTAL_UPPER - _THRESHOLD_INCREMENTAL_LOWER)
        / _INCREMENTAL_STEP_SIZE
    ).quantize(Decimal("1"), rounding=ROUND_CEILING)
    base_at_36340 = base_at_10170 + (steps_to_34820 + Decimal(1)) * step
    if basis_d <= _THRESHOLD_EXTRA_STEP_UPPER:
        return min(_to_cents(base_at_36340), cap)

    # Stage 4: promille on Mehrbetrag — über 36 340 EUR
    promille1 = spec.promille_lower_vT
    promille2 = spec.promille_upper_vT
    if basis_d <= _THRESHOLD_PROMILLE_UPPER:
        ueberschuss = basis_d - _THRESHOLD_EXTRA_STEP_UPPER
        variable = ueberschuss * promille1 / Decimal(1000)
        return min(_to_cents(base_at_36340 + variable), cap)

    # Stage 5: two promille slices — über 363 360 EUR
    slice_lower = (
        _THRESHOLD_PROMILLE_UPPER - _THRESHOLD_EXTRA_STEP_UPPER
    ) * promille1 / Decimal(1000)
    slice_upper = (basis_d - _THRESHOLD_PROMILLE_UPPER) * promille2 / Decimal(1000)
    return min(_to_cents(base_at_36340 + slice_lower + slice_upper), cap)


def einheitssatz(
    basis: float | int | Decimal,
    verdienstsumme: float | int | Decimal,
    *,
    multiplier: int | Decimal = 1,
) -> Decimal:
    """Einheitssatz nach § 23 RATG.

    :param basis: Streitwert (entscheidet zwischen 60 % und 50 %).
    :param verdienstsumme: Tarifsatz für die Hauptleistung (z. B. der
        Rückgabewert von :func:`tarifsatz`).
    :param multiplier: Multiplikator für Spezialfälle nach § 23 Abs. 5–9
        (Verdoppelung, Verdreifachung, Vervierfachung). Default 1.
    :returns: Einheitssatz in Euro (Cent-Präzision).
    """

    basis_d = _D(basis)
    verdienst_d = _D(verdienstsumme)
    if basis_d < 0 or verdienst_d < 0:
        raise ValueError("Streitwert und Verdienstsumme dürfen nicht negativ sein")
    satz = Decimal("0.60") if basis_d <= _THRESHOLD_INCREMENTAL_LOWER else Decimal("0.50")
    return _to_cents(verdienst_d * satz * _D(multiplier))


def streitgenossenzuschlag(
    grundlage: float | int | Decimal,
    anzahl_personen_einer_seite: int,
    weitere_personen_andere_seite: int = 0,
) -> Decimal:
    """Streitgenossenzuschlag nach § 15 RATG.

    Regel:
      * 10 % bei zwei vertretenen/gegenüberstehenden Personen auf einer Seite.
      * Zusätzlich 5 % je weitere Person (gleichgültig welche Seite).
      * Höchstens 50 % insgesamt.

    :param grundlage: Verdienstsumme einschließlich Einheitssatz (ohne
        Reisekosten/Auslagen).
    :param anzahl_personen_einer_seite: Anzahl der vom Anwalt vertretenen
        oder ihm gegenüberstehenden Personen auf der zählungsauslösenden Seite
        (≥ 2 für Zuschlag).
    :param weitere_personen_andere_seite: Anzahl weiterer Personen auf der
        anderen Seite (jede mit +5 %).
    :returns: Zuschlagsbetrag in Euro (Cent-Präzision); 0 wenn kein Zuschlag
        zusteht.
    """

    grundlage_d = _D(grundlage)
    if grundlage_d < 0:
        raise ValueError("Grundlage darf nicht negativ sein")
    if anzahl_personen_einer_seite < 0 or weitere_personen_andere_seite < 0:
        raise ValueError("Personenzahlen dürfen nicht negativ sein")
    if anzahl_personen_einer_seite < 2:
        return Decimal("0.00")

    # 10 % für die zweite Person auf der ersten Seite, je 5 % für jede weitere
    # Person (auf welcher Seite auch immer).
    weitere = (anzahl_personen_einer_seite - 2) + weitere_personen_andere_seite
    prozent = Decimal(10) + Decimal(5) * weitere
    prozent = min(prozent, Decimal(50))
    return _to_cents(grundlage_d * prozent / Decimal(100))


def tagsatzung_verdienst(
    tp: str | Tarifpost,
    basis: float | int | Decimal,
    dauer_stunden: int | float | Decimal = 1,
    *,
    valorized: bool = True,
) -> Decimal:
    """Verdienst für eine Tagsatzung nach TP 3A/3B/3C Abschnitt II RATG.

    Regel (TP 3 Abschnitt II): „für die erste Stunde jeder Tagsatzung die im
    Abschnitt I festgesetzte Entlohnung, für jede weitere, wenn auch nur
    begonnene Stunde einer Tagsatzung die Hälfte dieser Entlohnung".

    :param tp: Tarifpost (``"3a"``, ``"3b"`` oder ``"3c"``).
    :param basis: Bemessungsgrundlage.
    :param dauer_stunden: Dauer der Tagsatzung in Stunden. Wird auf die
        nächste ganze Stunde aufgerundet ("auch nur begonnene Stunde"). ≤ 1
        bedeutet 1 Stunde (= einfacher Abschnitt-I-Wert).
    :returns: Verdienst in Euro mit Cent-Präzision.

    Hinweis: Anm. 14-Caps für die zweite/weitere Stunde sind aktuell noch
    nicht implementiert — relevant erst bei sehr hohen Streitwerten.
    """

    erste_stunde = tarifsatz(tp, basis, valorized=valorized)
    # Aufrunden auf "auch nur begonnene Stunde".
    dauer_d = _D(dauer_stunden)
    if dauer_d <= 0:
        raise ValueError("dauer_stunden muss positiv sein")
    stunden_ceil = dauer_d.quantize(Decimal("1"), rounding=ROUND_CEILING)
    if stunden_ceil <= 1:
        return _to_cents(erste_stunde)
    weitere = int(stunden_ceil - 1)
    halbe = _to_cents(erste_stunde / Decimal(2))
    return _to_cents(erste_stunde + halbe * Decimal(weitere))


_ERV_CACHE: dict[ErvKind, tuple[Decimal, Decimal]] = {}


def _load_erv() -> None:
    if _ERV_CACHE:
        return
    raw = json.loads((_DATA_DIR / "erv.json").read_text())
    for kind in ErvKind:
        entry = raw["kinds"][kind.value]
        _ERV_CACHE[kind] = (
            _D(entry["betrag_gesetz"]),
            _D(entry["betrag_ab_2023_05_01"]),
        )


def erv_erhoehung(kind: str | ErvKind, *, valorized: bool = True) -> Decimal:
    """Erhöhungsbetrag nach § 23a RATG für ERV-eingebrachte Schriftsätze.

    :param kind: ``"einleitend"`` (verfahrenseinleitender Schriftsatz),
        ``"weiterer"`` (jeder weitere ERV-Schriftsatz) oder
        ``"grundbuch_firmenbuch"`` (Urkundensammlung GB/FB).
    :param valorized: ``True`` → BGBl. II Nr. 131/2023 (5,00 / 2,60 / 9,50);
        ``False`` → Gesetzeswortlaut (3,60 / 1,80 / 7,00).
    """

    _load_erv()
    try:
        kind_enum = ErvKind(kind) if not isinstance(kind, ErvKind) else kind
    except ValueError as exc:
        raise ValueError(
            f"Unbekannte ERV-Art: {kind!r}. "
            "Erlaubt: 'einleitend', 'weiterer', 'grundbuch_firmenbuch'."
        ) from exc
    gesetz, val = _ERV_CACHE[kind_enum]
    return val if valorized else gesetz
