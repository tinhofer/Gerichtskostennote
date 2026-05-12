"""Command-line interface for rendering a Gerichtskostennote."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Literal

from gerichtskostennote.renderer import compute, render_markdown

Format = Literal["markdown", "pdf"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gkn",
        description="Erzeuge eine Gerichtskostennote aus einer JSON-Beschreibung.",
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Pfad zur Eingabedatei (JSON). Verwende '-' für stdin.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Pfad zur Ausgabedatei. Default: stdout (nur Markdown).",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=("markdown", "pdf"),
        help="Erzwingt das Ausgabeformat. Default: per Dateiendung erraten "
        "(.pdf → pdf, sonst markdown).",
    )
    return parser


def _resolve_format(output: Path | None, explicit: str | None) -> Format:
    if explicit:
        return explicit  # type: ignore[return-value]
    if output is not None and output.suffix.lower() == ".pdf":
        return "pdf"
    return "markdown"


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if str(args.input) == "-":
        payload = json.loads(sys.stdin.read())
    else:
        payload = json.loads(args.input.read_text())

    note = compute(payload)
    fmt: Format = _resolve_format(args.output, args.format)

    if fmt == "pdf":
        if args.output is None:
            print(
                "PDF-Ausgabe benötigt -o/--output (PDF auf stdout nicht unterstützt).",
                file=sys.stderr,
            )
            return 2
        # Import on demand so the core CLI works without the 'pdf' extra.
        from gerichtskostennote.pdf import render_pdf
        render_pdf(note, args.output)
        return 0

    markdown = render_markdown(note)
    if args.output:
        args.output.write_text(markdown)
    else:
        sys.stdout.write(markdown)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
