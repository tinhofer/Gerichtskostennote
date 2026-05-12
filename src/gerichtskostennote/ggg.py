"""Pauschalgebühren-Berechnung nach Gerichtsgebührengesetz (GGG)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import ROUND_CEILING, Decimal
from enum import Enum
from pathlib import Path
from typing import Final

_DATA_DIR: Final = Path(__file__).resolve().parents[2] / "data" / "ggg"


class TarifpostNotFound(KeyError):
    """Raised when an unknown Tarifpost key is requested."""


class Tarifpost(str, Enum):
    """Stable identifiers for the supported Tarifposten.

    The string value matches the ``tp`` argument accepted by
    :func:`pauschalgebuehr`.
    """

    TP1 = "1"
    TP2 = "2"
    TP3A = "3a"
    TP3B = "3b"
    TP4_I_A = "4Ia"
    TP4_I_B = "4Ib"
    TP4_II_A = "4IIa"
    TP4_II_B = "4IIb"
    TP4_III_A = "4IIIa"
    TP4_III_B = "4IIIb"


class Ermaessigung(str, Enum):
    """GGG bracket-fee reductions implemented as flat multipliers."""

    RUECKZIEHUNG_VOR_ZUSTELLUNG = "rueckziehung_vor_zustellung"  # TP 1 Anm. 3 → 1/4
    RUECKZIEHUNG_ERSTE_TAGSATZUNG = "rueckziehung_erste_tagsatzung"  # TP 1 Anm. 4 → 1/2
    EINSTWEILIGE_VERFUEGUNG = "einstweilige_verfuegung"  # → 1/2
    RUECKZIEHUNG_VOR_BEWILLIGUNG = "rueckziehung_vor_bewilligung"  # TP 4 Anm. 2 → 1/2


_ERMAESSIGUNGS_FAKTOR: Final[dict[Ermaessigung, Decimal]] = {
    Ermaessigung.RUECKZIEHUNG_VOR_ZUSTELLUNG: Decimal("0.25"),
    Ermaessigung.RUECKZIEHUNG_ERSTE_TAGSATZUNG: Decimal("0.5"),
    Ermaessigung.EINSTWEILIGE_VERFUEGUNG: Decimal("0.5"),
    Ermaessigung.RUECKZIEHUNG_VOR_BEWILLIGUNG: Decimal("0.5"),
}


@dataclass(frozen=True)
class _Bracket:
    ueber: Decimal
    bis: Decimal
    betrag_gesetz: Decimal
    betrag_valorisiert: Decimal


@dataclass(frozen=True)
class _Extension:
    """Open-ended top stage: prozentsatz × basis + sockel."""

    threshold: Decimal
    prozentsatz: Decimal  # Hundertsatz oder Promille — siehe `is_promille`
    is_promille: bool
    sockel_gesetz: Decimal
    sockel_valorisiert: Decimal
    # If True, only the part of the basis above `threshold` is multiplied.
    apply_to_overflow_only: bool


@dataclass(frozen=True)
class _FixedFee:
    betrag_gesetz: Decimal
    betrag_valorisiert: Decimal


@dataclass(frozen=True)
class _PercentMinimum:
    """TP 3 lit. b style: prozentsatz × basis, mindestens Betrag."""

    prozentsatz: Decimal
    mindestbetrag_gesetz: Decimal
    mindestbetrag_valorisiert: Decimal


@dataclass(frozen=True)
class _MultiplierOf:
    """TP 4 Z II/III lit. a: fixed multiplier of another Tarifpost."""

    base: Tarifpost
    faktor: Decimal


_CACHE: dict[Tarifpost, object] = {}


def _D(value) -> Decimal:
    return Decimal(str(value))


def _load() -> None:
    if _CACHE:
        return

    tp1 = json.loads((_DATA_DIR / "tp1_zivilprozess_erste_instanz.json").read_text())
    _CACHE[Tarifpost.TP1] = (
        [_bracket(b) for b in tp1["Z_I"]["brackets"]],
        _Extension(
            threshold=_D(350000),
            prozentsatz=_D(tp1["Z_I"]["ueber_350000"]["prozentsatz"]),
            is_promille=False,
            sockel_gesetz=_D(tp1["Z_I"]["ueber_350000"]["sockel_gesetz"]),
            sockel_valorisiert=_D(tp1["Z_I"]["ueber_350000"]["sockel_ab_2025_04_01"]),
            apply_to_overflow_only=False,
        ),
    )

    tp2 = json.loads((_DATA_DIR / "tp2_zivilprozess_zweite_instanz.json").read_text())
    _CACHE[Tarifpost.TP2] = (
        [_bracket(b) for b in tp2["brackets"]],
        _Extension(
            threshold=_D(350000),
            prozentsatz=_D(tp2["ueber_350000"]["prozentsatz"]),
            is_promille=False,
            sockel_gesetz=_D(tp2["ueber_350000"]["sockel_gesetz"]),
            sockel_valorisiert=_D(tp2["ueber_350000"]["sockel_ab_2025_04_01"]),
            apply_to_overflow_only=False,
        ),
    )

    tp3 = json.loads((_DATA_DIR / "tp3_zivilprozess_dritte_instanz.json").read_text())
    _CACHE[Tarifpost.TP3A] = (
        [_bracket(b) for b in tp3["lit_a"]["brackets"]],
        _Extension(
            threshold=_D(350000),
            prozentsatz=_D(tp3["lit_a"]["ueber_350000"]["prozentsatz"]),
            is_promille=False,
            sockel_gesetz=_D(tp3["lit_a"]["ueber_350000"]["sockel_gesetz"]),
            sockel_valorisiert=_D(
                tp3["lit_a"]["ueber_350000"]["sockel_ab_2025_04_01"]
            ),
            apply_to_overflow_only=False,
        ),
    )
    _CACHE[Tarifpost.TP3B] = _PercentMinimum(
        prozentsatz=_D(tp3["lit_b"]["prozentsatz"]),
        mindestbetrag_gesetz=_D(tp3["lit_b"]["mindestbetrag_gesetz"]),
        mindestbetrag_valorisiert=_D(tp3["lit_b"]["mindestbetrag_ab_2025_04_01"]),
    )

    tp4 = json.loads((_DATA_DIR / "tp4_exekutionsverfahren.json").read_text())
    _CACHE[Tarifpost.TP4_I_A] = (
        [_bracket(b) for b in tp4["Z_I"]["lit_a"]["brackets"]],
        _Extension(
            threshold=_D(70000),
            prozentsatz=_D(tp4["Z_I"]["lit_a"]["ueber_70000"]["promille_ueberschiessend"]),
            is_promille=True,
            sockel_gesetz=_D(tp4["Z_I"]["lit_a"]["ueber_70000"]["sockel_gesetz"]),
            sockel_valorisiert=_D(
                tp4["Z_I"]["lit_a"]["ueber_70000"]["sockel_ab_2025_04_01"]
            ),
            apply_to_overflow_only=True,
        ),
    )
    _CACHE[Tarifpost.TP4_I_B] = _FixedFee(
        betrag_gesetz=_D(tp4["Z_I"]["lit_b"]["betrag_gesetz"]),
        betrag_valorisiert=_D(tp4["Z_I"]["lit_b"]["betrag_ab_2025_04_01"]),
    )
    _CACHE[Tarifpost.TP4_II_A] = _MultiplierOf(
        base=Tarifpost.TP4_I_A, faktor=_D("1.5")
    )
    _CACHE[Tarifpost.TP4_II_B] = _FixedFee(
        betrag_gesetz=_D(tp4["Z_II"]["lit_b"]["betrag_gesetz"]),
        betrag_valorisiert=_D(tp4["Z_II"]["lit_b"]["betrag_ab_2025_04_01"]),
    )
    _CACHE[Tarifpost.TP4_III_A] = _MultiplierOf(
        base=Tarifpost.TP4_I_A, faktor=_D("2.0")
    )
    _CACHE[Tarifpost.TP4_III_B] = _FixedFee(
        betrag_gesetz=_D(tp4["Z_III"]["lit_b"]["betrag_gesetz"]),
        betrag_valorisiert=_D(tp4["Z_III"]["lit_b"]["betrag_ab_2025_04_01"]),
    )


def _bracket(raw: dict) -> _Bracket:
    return _Bracket(
        ueber=_D(raw["ueber"]),
        bis=_D(raw["bis"]),
        betrag_gesetz=_D(raw["betrag_gesetz"]),
        betrag_valorisiert=_D(raw["betrag_ab_2025_04_01"]),
    )


def _ceil_euro(amount: Decimal) -> Decimal:
    """§ 6 Abs. 2 GGG: Hundertsatz-/Tausendsatzgebühren auf den nächsthöheren Euro."""

    return amount.quantize(Decimal("1"), rounding=ROUND_CEILING)


def _resolve_tp(tp: str | Tarifpost) -> Tarifpost:
    if isinstance(tp, Tarifpost):
        return tp
    try:
        return Tarifpost(tp)
    except ValueError as exc:
        raise TarifpostNotFound(tp) from exc


def pauschalgebuehr(
    tp: str | Tarifpost,
    basis: float | int | Decimal,
    *,
    valorized: bool = True,
    ermaessigung: Ermaessigung | None = None,
) -> Decimal:
    """Pauschalgebühr nach GGG.

    :param tp: Tarifpost-Kennung (siehe :class:`Tarifpost`), z. B. ``"1"``,
        ``"3a"``, ``"4Ia"``.
    :param basis: Bemessungsgrundlage (Streitwert / Berufungsinteresse /
        Anspruch) in Euro.
    :param valorized: Falls ``True`` (default), wird der seit 1.4.2025
        gemäß BGBl. II Nr. 51/2025 valorisierte Betrag herangezogen,
        sonst der im GGG-Tarif selbst angeführte Betrag.
    :param ermaessigung: Optionaler Reduktionsfaktor (z. B.
        ``Ermaessigung.RUECKZIEHUNG_VOR_ZUSTELLUNG`` → 1/4 nach Anm. 3 zu TP 1).
        Auf das Endergebnis wird der Faktor angewendet; eine § 6 Abs. 2
        Aufrundung greift nur bei Hundertsatz-/Tausendsatzteilen,
        nicht bei Reduktionen.
    :returns: Gebühr in Euro als :class:`Decimal`. Hundertsatz- und
        Tausendsatzanteile werden gemäß § 6 Abs. 2 GGG auf den
        nächsthöheren Euro aufgerundet.
    """

    _load()
    key = _resolve_tp(tp)
    spec = _CACHE.get(key)
    if spec is None:
        raise TarifpostNotFound(tp)

    basis_d = _D(basis)
    if basis_d < 0:
        raise ValueError("Bemessungsgrundlage darf nicht negativ sein")

    if isinstance(spec, tuple):
        brackets, ext = spec
        result = _bracket_or_extension(brackets, ext, basis_d, valorized)
    elif isinstance(spec, _FixedFee):
        result = spec.betrag_valorisiert if valorized else spec.betrag_gesetz
    elif isinstance(spec, _PercentMinimum):
        raw = basis_d * spec.prozentsatz / Decimal(100)
        mindest = (
            spec.mindestbetrag_valorisiert if valorized else spec.mindestbetrag_gesetz
        )
        result = max(_ceil_euro(raw), mindest)
    elif isinstance(spec, _MultiplierOf):
        base_fee = pauschalgebuehr(spec.base, basis_d, valorized=valorized)
        result = _ceil_euro(base_fee * spec.faktor)
    else:  # pragma: no cover — defensive
        raise TarifpostNotFound(tp)

    if ermaessigung is not None:
        faktor = _ERMAESSIGUNGS_FAKTOR[ermaessigung]
        result = result * faktor

    return result


def _bracket_or_extension(
    brackets: list[_Bracket],
    ext: _Extension,
    basis: Decimal,
    valorized: bool,
) -> Decimal:
    # GGG bracket semantics: ueber exclusive, bis inclusive.
    for b in brackets:
        if b.ueber < basis <= b.bis:
            return b.betrag_valorisiert if valorized else b.betrag_gesetz

    # Below the lowest bracket (basis <= first.ueber, typically 0) → first bracket.
    if basis <= brackets[0].bis:
        return brackets[0].betrag_valorisiert if valorized else brackets[0].betrag_gesetz

    # Above all brackets: extension stage.
    sockel = ext.sockel_valorisiert if valorized else ext.sockel_gesetz
    divisor = Decimal(1000) if ext.is_promille else Decimal(100)
    multiplied_basis = (basis - ext.threshold) if ext.apply_to_overflow_only else basis
    variable_part = _ceil_euro(multiplied_basis * ext.prozentsatz / divisor)
    return sockel + variable_part
