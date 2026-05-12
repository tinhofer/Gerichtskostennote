"""Markdown renderer for a Gerichtskostennote.

Consumes a dict (typically loaded from JSON) and emits a Markdown document
combining GGG court fees and RATG attorney fees plus an optional VAT line.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from gerichtskostennote.ggg import Ermaessigung, pauschalgebuehr
from gerichtskostennote.ratg import einheitssatz, streitgenossenzuschlag, tarifsatz

_CENT = Decimal("0.01")


class InputError(ValueError):
    """Raised when a Kostennote input dict is malformed."""


@dataclass(frozen=True)
class _LeistungRow:
    datum: str | None
    tp: str
    beschreibung: str
    verdienst: Decimal
    einheitssatz: Decimal
    streitgenossen: Decimal
    netto: Decimal


@dataclass(frozen=True)
class _GerichtsRow:
    tp: str
    beschreibung: str
    betrag: Decimal


@dataclass(frozen=True)
class Kostennote:
    """Computed view of a cost note; carries Markdown serialization."""

    title: str
    header: dict[str, Any]
    streitwert: Decimal
    umsatzsteuer_prozent: Decimal
    leistungen: list[_LeistungRow]
    gerichtsgebuehren: list[_GerichtsRow]

    @property
    def anwalt_netto(self) -> Decimal:
        return sum((row.netto for row in self.leistungen), Decimal("0.00"))

    @property
    def umsatzsteuer(self) -> Decimal:
        return _q(self.anwalt_netto * self.umsatzsteuer_prozent / Decimal(100))

    @property
    def anwalt_brutto(self) -> Decimal:
        return self.anwalt_netto + self.umsatzsteuer

    @property
    def gerichts_summe(self) -> Decimal:
        return sum((row.betrag for row in self.gerichtsgebuehren), Decimal("0.00"))

    @property
    def gesamt(self) -> Decimal:
        return self.anwalt_brutto + self.gerichts_summe


def _q(amount: Decimal) -> Decimal:
    return amount.quantize(_CENT, rounding=ROUND_HALF_UP)


def _fmt(amount: Decimal) -> str:
    return f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def compute(payload: dict[str, Any]) -> Kostennote:
    """Compute all rows + totals from an input payload."""

    try:
        streitwert = Decimal(str(payload["streitwert"]))
    except KeyError as exc:
        raise InputError("Pflichtfeld 'streitwert' fehlt") from exc

    ust = Decimal(str(payload.get("umsatzsteuer_prozent", 20)))
    default_personen = int(payload.get("default_personen_einer_seite", 1))

    rows: list[_LeistungRow] = []
    for raw in payload.get("anwaltsleistungen", []):
        tp = raw["tp"]
        n_personen = int(raw.get("personen_einer_seite", default_personen))
        n_andere = int(raw.get("weitere_personen_andere_seite", 0))
        ermaess_multiplier = Decimal(str(raw.get("einheitssatz_multiplier", 1)))

        verdienst = tarifsatz(tp, streitwert)
        es = einheitssatz(streitwert, verdienst, multiplier=ermaess_multiplier)
        sg = streitgenossenzuschlag(verdienst + es, n_personen, n_andere)
        netto = verdienst + es + sg
        rows.append(
            _LeistungRow(
                datum=raw.get("datum"),
                tp=tp,
                beschreibung=raw.get("beschreibung", ""),
                verdienst=verdienst,
                einheitssatz=es,
                streitgenossen=sg,
                netto=_q(netto),
            )
        )

    gericht_rows: list[_GerichtsRow] = []
    for raw in payload.get("gerichtsgebuehren", []):
        tp = raw["tp"]
        ermaessigung = raw.get("ermaessigung")
        ermaess_enum = Ermaessigung(ermaessigung) if ermaessigung else None
        basis = Decimal(str(raw.get("bemessungsgrundlage", streitwert)))
        betrag = pauschalgebuehr(tp, basis, ermaessigung=ermaess_enum)
        gericht_rows.append(
            _GerichtsRow(
                tp=tp,
                beschreibung=raw.get("beschreibung", ""),
                betrag=_q(Decimal(betrag)),
            )
        )

    return Kostennote(
        title=payload.get("title", "Kostennote"),
        header=payload.get("header", {}),
        streitwert=streitwert,
        umsatzsteuer_prozent=ust,
        leistungen=rows,
        gerichtsgebuehren=gericht_rows,
    )


def render_markdown(note: Kostennote) -> str:
    """Render a Kostennote as Markdown."""

    lines: list[str] = []
    lines.append(f"# {note.title}")
    lines.append("")

    h = note.header
    if h:
        if h.get("aktenzeichen"):
            lines.append(f"**Aktenzeichen:** {h['aktenzeichen']}  ")
        if h.get("gericht"):
            lines.append(f"**Gericht:** {h['gericht']}  ")
        if h.get("klaeger"):
            lines.append(f"**Klagende Partei:** {', '.join(h['klaeger'])}  ")
        if h.get("beklagter"):
            lines.append(f"**Beklagte Partei:** {', '.join(h['beklagter'])}  ")
        if h.get("stand"):
            lines.append(f"**Stand:** {h['stand']}  ")
        lines.append("")

    lines.append(f"**Streitwert:** {_fmt(note.streitwert)} EUR")
    lines.append("")

    if note.leistungen:
        lines.append("## Anwaltskosten")
        lines.append("")
        lines.append(
            "| Datum | TP | Beschreibung | Verdienst | Einheitssatz | Streitgenossen | Netto |"
        )
        lines.append("|---|---|---|---:|---:|---:|---:|")
        for r in note.leistungen:
            lines.append(
                f"| {r.datum or ''} | TP {r.tp.upper()} | {r.beschreibung} | "
                f"{_fmt(r.verdienst)} | {_fmt(r.einheitssatz)} | "
                f"{_fmt(r.streitgenossen)} | {_fmt(r.netto)} |"
            )
        lines.append("")
        lines.append(f"**Summe Anwaltskosten netto:** {_fmt(note.anwalt_netto)} EUR  ")
        lines.append(
            f"**USt ({note.umsatzsteuer_prozent:g} %):** {_fmt(note.umsatzsteuer)} EUR  "
        )
        lines.append(f"**Summe Anwaltskosten brutto:** {_fmt(note.anwalt_brutto)} EUR")
        lines.append("")

    if note.gerichtsgebuehren:
        lines.append("## Gerichtsgebühren")
        lines.append("")
        lines.append("| TP | Beschreibung | Betrag |")
        lines.append("|---|---|---:|")
        for g in note.gerichtsgebuehren:
            lines.append(
                f"| TP {g.tp.upper()} | {g.beschreibung} | {_fmt(g.betrag)} |"
            )
        lines.append("")
        lines.append(f"**Summe Gerichtsgebühren:** {_fmt(note.gerichts_summe)} EUR")
        lines.append("")

    lines.append("## Gesamt")
    lines.append("")
    lines.append(f"**Gesamtsumme:** {_fmt(note.gesamt)} EUR")
    lines.append("")

    return "\n".join(lines)
