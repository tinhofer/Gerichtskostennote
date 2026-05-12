"""Command-line interface for rendering a Gerichtskostennote."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from gerichtskostennote.renderer import compute, render_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gkn",
        description="Erzeuge eine Gerichtskostennote (Markdown) aus einer JSON-Beschreibung.",
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
        help="Pfad zur Ausgabedatei. Default: stdout.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if str(args.input) == "-":
        payload = json.loads(sys.stdin.read())
    else:
        payload = json.loads(args.input.read_text())

    note = compute(payload)
    markdown = render_markdown(note)

    if args.output:
        args.output.write_text(markdown)
    else:
        sys.stdout.write(markdown)

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
