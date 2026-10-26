"""Markdown renderer for a Gerichtskostennote.

Consumes a dict (typically loaded from JSON) and emits a Markdown document
combining GGG court fees and RATG attorney fees plus an optional VAT line.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from gerichtskostennote.ggg import Ermaessigung, pauschalgebuehr
from gerichtskostennote.ratg import (
    ErvKind,
    einheitssatz,
    erv_erhoehung,
    streitgenossenzuschlag,
    tagsatzung_verdienst,
    tarifsatz,
)

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
    erv: Decimal
    erv_kind: str | None
    netto: Decimal


@dataclass(frozen=True)
class _GerichtsRow:
    tp: str
    beschreibung: str
    betrag: Decimal


@dataclass(frozen=True)
class _BarauslageRow:
    """Barauslage / Reisekosten / Sonstige Auslagen, ohne USt-Behandlung."""

    datum: str | None
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
    barauslagen: list[_BarauslageRow]
    gerichtsgebuehren: list[_GerichtsRow]

    @property
    def anwalt_netto(self) -> Decimal:
        return sum((row.netto for row in self.leistungen), Decimal("0.00"))

    @property
    def barauslagen_summe(self) -> Decimal:
        return sum((row.betrag for row in self.barauslagen), Decimal("0.00"))

    @property
    def erv_summe(self) -> Decimal:
        return sum((row.erv for row in self.leistungen), Decimal("0.00"))

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
        return self.anwalt_brutto + self.barauslagen_summe + self.gerichts_summe


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
    default_fahrtkosten_raw = payload.get("default_fahrtkosten")
    default_fahrtkosten = (
        Decimal(str(default_fahrtkosten_raw))
        if default_fahrtkosten_raw is not None
        else None
    )

    rows: list[_LeistungRow] = []
    auto_auslagen: list[_BarauslageRow] = []
    for raw in payload.get("anwaltsleistungen", []):
        tp = raw["tp"]
        n_personen = int(raw.get("personen_einer_seite", default_personen))
        n_andere = int(raw.get("weitere_personen_andere_seite", 0))
        ermaess_multiplier = Decimal(str(raw.get("einheitssatz_multiplier", 1)))

        dauer_raw = raw.get("dauer_stunden")
        if dauer_raw is not None:
            verdienst = tagsatzung_verdienst(tp, streitwert, dauer_raw)
        else:
            verdienst = tarifsatz(tp, streitwert)
        es = einheitssatz(streitwert, verdienst, multiplier=ermaess_multiplier)
        sg = streitgenossenzuschlag(verdienst + es, n_personen, n_andere)

        erv_raw = raw.get("erv")
        erv_betrag = Decimal("0.00")
        erv_kind: str | None = None
        if erv_raw:
            if erv_raw is True:
                erv_kind = ErvKind.WEITERER.value
            else:
                # Accept short aliases.
                alias = {"weiter": "weiterer", "gb_fb": "grundbuch_firmenbuch"}
                erv_kind = alias.get(str(erv_raw), str(erv_raw))
            erv_betrag = erv_erhoehung(erv_kind)

        netto = verdienst + es + sg + erv_betrag
        rows.append(
            _LeistungRow(
                datum=raw.get("datum"),
                tp=tp,
                beschreibung=raw.get("beschreibung", ""),
                verdienst=verdienst,
                einheitssatz=es,
                streitgenossen=sg,
                erv=_q(erv_betrag),
                erv_kind=erv_kind,
                netto=_q(netto),
            )
        )

        # Per-Leistung Fahrtkosten → Barauslage.
        fahrt = raw.get("fahrtkosten")
        if fahrt:  # truthy (True, non-zero number, etc.)
            if fahrt is True:
                if default_fahrtkosten is None:
                    raise InputError(
                        "Anwaltsleistung enthält 'fahrtkosten: true', aber das "
                        "Pflichtfeld 'default_fahrtkosten' fehlt im Top-Level."
                    )
                fahrt_betrag = default_fahrtkosten
            else:
                fahrt_betrag = Decimal(str(fahrt))
            if fahrt_betrag < 0:
                raise InputError(
                    "Fahrtkosten dürfen nicht negativ sein"
                )
            descr_prefix = raw.get("beschreibung", "").strip()
            descr = (
                f"Fahrtkosten {descr_prefix}".strip()
                if descr_prefix
                else "Fahrtkosten"
            )
            auto_auslagen.append(
                _BarauslageRow(
                    datum=raw.get("datum"),
                    beschreibung=descr,
                    betrag=_q(fahrt_betrag),
                )
            )

    auslagen_rows: list[_BarauslageRow] = list(auto_auslagen)
    for raw in payload.get("barauslagen", []):
        try:
            betrag = Decimal(str(raw["betrag"]))
        except KeyError as exc:
            raise InputError(
                "Barauslage benötigt Pflichtfeld 'betrag'"
            ) from exc
        if betrag < 0:
            raise InputError("Barauslage 'betrag' darf nicht negativ sein")
        auslagen_rows.append(
            _BarauslageRow(
                datum=raw.get("datum"),
                beschreibung=raw.get("beschreibung", ""),
                betrag=_q(betrag),
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
        barauslagen=auslagen_rows,
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
            "| Datum | TP | Beschreibung | Verdienst | Einheitssatz | Streitgenossen | ERV | Netto |"
        )
        lines.append("|---|---|---|---:|---:|---:|---:|---:|")
        for r in note.leistungen:
            lines.append(
                f"| {r.datum or ''} | TP {r.tp.upper()} | {r.beschreibung} | "
                f"{_fmt(r.verdienst)} | {_fmt(r.einheitssatz)} | "
                f"{_fmt(r.streitgenossen)} | {_fmt(r.erv)} | {_fmt(r.netto)} |"
            )
        lines.append("")
        if note.erv_summe > 0:
            lines.append(
                f"_Davon ERV-Erhöhung gemäß § 23a RATG: {_fmt(note.erv_summe)} EUR._  "
            )
        lines.append(f"**Summe Anwaltskosten netto:** {_fmt(note.anwalt_netto)} EUR  ")
        lines.append(
            f"**USt ({note.umsatzsteuer_prozent:g} %):** {_fmt(note.umsatzsteuer)} EUR  "
        )
        lines.append(f"**Summe Anwaltskosten brutto:** {_fmt(note.anwalt_brutto)} EUR")
        lines.append("")

    if note.barauslagen:
        lines.append("## Barauslagen")
        lines.append("")
        lines.append("| Datum | Beschreibung | Betrag |")
        lines.append("|---|---|---:|")
        for a in note.barauslagen:
            lines.append(
                f"| {a.datum or ''} | {a.beschreibung} | {_fmt(a.betrag)} |"
            )
        lines.append("")
        lines.append(
            f"**Summe Barauslagen** (ohne USt): "
            f"{_fmt(note.barauslagen_summe)} EUR"
        )
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
