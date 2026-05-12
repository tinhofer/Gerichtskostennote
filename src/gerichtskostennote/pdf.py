"""PDF renderer for a Gerichtskostennote.

Uses ReportLab Platypus to produce a single-page A4 cost note. Install with
``pip install -e ".[pdf]"`` to pull in ReportLab.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
except ImportError as exc:  # pragma: no cover — import-time only
    raise ImportError(
        "PDF rendering requires the optional 'pdf' extra: pip install -e \".[pdf]\""
    ) from exc

from gerichtskostennote.renderer import Kostennote


def _fmt(amount: Decimal) -> str:
    return f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "KGN-Title",
            parent=base["Heading1"],
            fontSize=18,
            spaceAfter=6 * mm,
        ),
        "h2": ParagraphStyle(
            "KGN-H2",
            parent=base["Heading2"],
            fontSize=12,
            spaceBefore=4 * mm,
            spaceAfter=2 * mm,
        ),
        "body": ParagraphStyle(
            "KGN-Body",
            parent=base["BodyText"],
            fontSize=10,
            leading=13,
        ),
        "body_bold": ParagraphStyle(
            "KGN-BodyBold",
            parent=base["BodyText"],
            fontSize=10,
            leading=13,
            fontName="Helvetica-Bold",
        ),
        "right": ParagraphStyle(
            "KGN-Right",
            parent=base["BodyText"],
            fontSize=10,
            leading=13,
            alignment=2,  # TA_RIGHT
        ),
    }


def _header_paragraphs(note: Kostennote, styles: dict[str, ParagraphStyle]) -> list:
    flow: list = []
    h = note.header
    if h.get("aktenzeichen"):
        flow.append(Paragraph(f"<b>Aktenzeichen:</b> {h['aktenzeichen']}", styles["body"]))
    if h.get("gericht"):
        flow.append(Paragraph(f"<b>Gericht:</b> {h['gericht']}", styles["body"]))
    if h.get("klaeger"):
        flow.append(
            Paragraph(
                f"<b>Klagende Partei:</b> {', '.join(h['klaeger'])}", styles["body"]
            )
        )
    if h.get("beklagter"):
        flow.append(
            Paragraph(
                f"<b>Beklagte Partei:</b> {', '.join(h['beklagter'])}", styles["body"]
            )
        )
    if h.get("stand"):
        flow.append(Paragraph(f"<b>Stand:</b> {h['stand']}", styles["body"]))
    return flow


def _money_table(
    rows: list[list[str]],
    col_widths: list[float],
    right_align_from_col: int,
) -> Table:
    table = Table(rows, colWidths=col_widths, repeatRows=1)
    style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEEEEE")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (right_align_from_col, 0), (-1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]
    )
    table.setStyle(style)
    return table


def render_pdf(note: Kostennote, output: str | Path) -> Path:
    """Render ``note`` to a PDF file at ``output``.

    :param note: Computed Kostennote (see :func:`~gerichtskostennote.renderer.compute`).
    :param output: Destination path. Parent directory must exist.
    :returns: The resolved output path.
    """

    output_path = Path(output)
    styles = _styles()

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=note.title,
    )

    flow: list = [Paragraph(note.title, styles["title"])]
    flow.extend(_header_paragraphs(note, styles))
    flow.append(Spacer(1, 4 * mm))
    flow.append(
        Paragraph(
            f"<b>Streitwert:</b> {_fmt(note.streitwert)} EUR", styles["body"]
        )
    )

    if note.leistungen:
        flow.append(Paragraph("Anwaltskosten", styles["h2"]))
        rows = [
            [
                "Datum",
                "TP",
                "Beschreibung",
                "Verdienst",
                "ES",
                "SG",
                "Netto",
            ]
        ]
        for r in note.leistungen:
            rows.append(
                [
                    r.datum or "",
                    f"TP {r.tp.upper()}",
                    r.beschreibung,
                    _fmt(r.verdienst),
                    _fmt(r.einheitssatz),
                    _fmt(r.streitgenossen),
                    _fmt(r.netto),
                ]
            )
        # 170 mm usable width (A4 minus margins).
        flow.append(
            _money_table(
                rows,
                col_widths=[
                    22 * mm, 16 * mm, 50 * mm, 22 * mm, 20 * mm, 20 * mm, 20 * mm,
                ],
                right_align_from_col=3,
            )
        )
        flow.append(Spacer(1, 2 * mm))
        flow.append(
            Paragraph(
                f"<b>Summe Anwaltskosten netto:</b> {_fmt(note.anwalt_netto)} EUR",
                styles["body"],
            )
        )
        flow.append(
            Paragraph(
                f"<b>USt ({note.umsatzsteuer_prozent:g} %):</b> "
                f"{_fmt(note.umsatzsteuer)} EUR",
                styles["body"],
            )
        )
        flow.append(
            Paragraph(
                f"<b>Summe Anwaltskosten brutto:</b> "
                f"{_fmt(note.anwalt_brutto)} EUR",
                styles["body_bold"],
            )
        )

    if note.gerichtsgebuehren:
        flow.append(Paragraph("Gerichtsgebühren", styles["h2"]))
        rows = [["TP", "Beschreibung", "Betrag"]]
        for g in note.gerichtsgebuehren:
            rows.append([f"TP {g.tp.upper()}", g.beschreibung, _fmt(g.betrag)])
        flow.append(
            _money_table(
                rows,
                col_widths=[20 * mm, 130 * mm, 20 * mm],
                right_align_from_col=2,
            )
        )
        flow.append(Spacer(1, 2 * mm))
        flow.append(
            Paragraph(
                f"<b>Summe Gerichtsgebühren:</b> {_fmt(note.gerichts_summe)} EUR",
                styles["body_bold"],
            )
        )

    flow.append(Paragraph("Gesamt", styles["h2"]))
    flow.append(
        Paragraph(
            f"<b>Gesamtsumme: {_fmt(note.gesamt)} EUR</b>",
            styles["body_bold"],
        )
    )

    doc.build(flow)
    return output_path
