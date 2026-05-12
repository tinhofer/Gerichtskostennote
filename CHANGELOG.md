# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- PDF-Renderer in `gerichtskostennote.pdf.render_pdf()` (ReportLab Platypus,
  A4-Layout mit Header-Block, Streitwert, Anwaltskosten-Tabelle, USt-Zeilen,
  Gerichtsgebühren-Tabelle, Gesamtsumme). Optional-Extra `pdf` zieht
  ReportLab.
- CLI dispatched auf PDF, wenn die Ausgabedatei `.pdf` endet — oder
  explizit per `-f pdf`. Markdown bleibt Default. PDF-Ausgabe auf stdout
  wird abgelehnt (Exit 2, Stderr-Hinweis).
- 10 zusätzliche Tests in `tests/test_pdf.py` (PDF-Header-Bytes, Inhalt via
  pypdf-Textextraktion, Format-Auflösung, CLI-PDF-Pfad, Fehlerpfad ohne `-o`).
- Test-Extra erweitert um `reportlab` und `pypdf`.
- CLI `gkn` (Konsolen-Skript `gerichtskostennote.cli:main`) und Markdown-
  Renderer (`gerichtskostennote.renderer`). Liest eine JSON-Beschreibung einer
  Kostennote (Streitwert, Anwaltsleistungen, Gerichtsgebühren, Header) und
  erzeugt ein vollständiges Markdown-Dokument mit Anwaltskosten-Tabelle,
  USt-Zeile, Gerichtsgebühren-Tabelle und Gesamtsumme.
- `examples/klage_15000.json` als Beispiel-Eingabe (Klage bei Streitwert 15 000
  EUR mit zwei Klägern; Total 2.424,15 EUR inkl. USt und GGG).
- Console-Script-Eintrag `gkn = "gerichtskostennote.cli:main"` in
  `pyproject.toml`; zusätzlich `python -m gerichtskostennote ...`.
- 16 zusätzliche Tests in `tests/test_renderer.py` (compute-Funktion, Markdown-
  Inhalt, CLI stdout/Datei/stdin, console_script-Smoke-Test).
- RATG-Modul `gerichtskostennote.ratg` mit `tarifsatz()`, `einheitssatz()` und
  `streitgenossenzuschlag()`. Cent-Präzision (Decimal, HALF_UP). Implementiert
  RATG Anl. 1 TP 1, TP 2, TP 3 Teil A inklusive der inkrementellen Stufe
  (je 1 450 EUR ein Schritt), Promille-Stufen oberhalb 36 340 EUR
  und Cap.
- 40 zusätzliche pytest-Worked-Example-Tests in `tests/test_ratg.py`
  (Bracket-Lookups, inkrementelle Stufe, Promille-Stufen, Cap-Verhalten,
  § 23 Einheitssatz mit 60 %/50 %-Stufen und Multiplikator,
  § 15 Streitgenossenzuschlag inkl. 50 %-Obergrenze, plus ein
  Integrations-Smoke-Test für eine Klage-Kostenposition).
- RATG-Tarifdaten in `data/ratg/`: `tp1.json`, `tp2.json`, `tp3a.json`,
  `einheitssatz.json`, `streitgenossenzuschlag.json`, `index.json` und
  `README.md`. Stand 14.04.2026; valorisiert nach BGBl. II Nr. 131/2023
  (in Kraft 1.5.2023).
- Python-Paket `gerichtskostennote` (`src/gerichtskostennote/`) mit GGG-
  Pauschalgebührenrechner für TP 1–4. Öffentliche API: `pauschalgebuehr()`,
  `Tarifpost`, `Ermaessigung`, `TarifpostNotFound`.
- 38 pytest-Worked-Example-Tests in `tests/test_ggg.py` (Bracket-Grenzen,
  Promille-/Hundertsatz-Erweiterung, Aufrundung nach § 6 Abs. 2 GGG,
  Ermäßigungen, Multiplikator-Stufen 150 %/200 % für TP 4 Z II/III).
- `pyproject.toml` (setuptools, src-Layout, Python ≥ 3.10).
- Strukturierte Tarifdaten zum Gerichtsgebührengesetz (GGG), Tarifposten 1–4
  (`data/ggg/tp1..tp4_*.json`), inklusive `index.json` und Schema-Doku.
  Erfasst sind Stufenbeträge gemäß Gesetz **und** valorisierte Beträge nach
  BGBl. II Nr. 51/2025 (in Kraft 1.4.2025).
- `data/ggg/README.md` mit Bracket-Semantik (über/bis exklusiv/inklusiv).

### Changed
- README.md umgeschrieben — Projekt ist eine österreichische Gerichtskostennote-
  Toolbox (GGG + RATG), nicht das ursprüngliche generische Claude-Code-Scaffold.
- `.github/workflows/ci.yml`: vom Node-Stub auf Python-CI (3.10–3.12) umgestellt;
  installiert das Paket editable und führt pytest aus.

## [0.1.0] - 2026-01-02

### Added
- Initial repository structure
- Basic project scaffolding
- README mit Projektstruktur, CONTRIBUTING.md, MIT License, EditorConfig,
  GitHub-Templates, CI-Workflow-Skeleton
- Referenz-PDFs: GGG- und RATG-Konsolidate (Stand 14.04.2026)
