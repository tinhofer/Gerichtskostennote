# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Tagsatzungs-Stundenfaktor** für TP 3 Abschnitt II: Pro Anwaltsleistung kann
  `dauer_stunden` (z. B. 2, 3, 4) angegeben werden. Erste Stunde voller
  Tarifsatz, jede weitere angefangene Stunde die Hälfte (TP 3 Abschnitt II
  RATG). Bruchstunden werden auf die nächste ganze Stunde aufgerundet
  („auch nur begonnene Stunde"). Neue API-Funktion
  `ratg.tagsatzung_verdienst(tp, basis, dauer_stunden=1)`. 11 neue Tests.
- **`CLAUDE.md`** mit Orientierung für künftige Agent-Sessions (Repo-Layout,
  Schema, Konventionen, offene Punkte, Workflow).
- **Fahrtkosten-Shortcut** im Kostennote-Schema: Top-level
  `default_fahrtkosten` definiert den Standardbetrag (z. B. EUR 4,80 pro
  Gerichtsbehandlung). Pro Anwaltsleistung kann `fahrtkosten: true` (=
  Default) oder ein eigener Wert gesetzt werden. Es wird automatisch eine
  Barauslage-Position „Fahrtkosten &lt;Leistungsbeschreibung>" mit dem
  passenden Datum erzeugt. Fehlt oder `false` → keine Fahrtkosten — passt
  für auswärtige Verhandlungen, bei denen statt Fahrtkosten der doppelte
  Einheitssatz nach § 23 Abs. 5 RATG (`einheitssatz_multiplier: 2`)
  zusteht. 7 neue Tests, alle 140 grün.
- **Barauslagen-Sektion** im Kostennote-Schema und Renderer (Markdown + PDF).
  Eingabe als Liste `barauslagen` mit `betrag` (Pflicht), `beschreibung` und
  `datum` (optional). Werden ohne USt in die Gesamtsumme aufgenommen und
  separat ausgewiesen — passt für Reisekosten/Fahrtkosten, Porto, etc.
- 6 neue Tests in `tests/test_renderer.py` (Barauslagen außerhalb der
  USt-Basis, Mehrfacheinträge, Pflichtfeld- und Negativ-Validierung,
  Markdown-Sektion, Sektion-Auslassung bei leerer Liste).
- **§ 23a RATG (Web-ERV)** als richtiges Feature: pro Anwaltsleistung kann
  jetzt `"erv": "einleitend"` (5,00 EUR valorisiert), `"weiterer"`
  (2,60 EUR; Alias `true`) oder `"grundbuch_firmenbuch"` (9,50 EUR) gesetzt
  werden. Die ERV-Erhöhung fließt in den Netto-Betrag und damit die
  USt-Basis ein; ist gemäß § 23a Satz 3 RATG aber bei der Bemessung von
  Einheitssatz und Streitgenossenzuschlag ausgenommen. Markdown- und PDF-
  Tabellen haben eine neue ERV-Spalte plus Gesamtsummen-Hinweis.
- `data/ratg/erv.json` mit den drei § 23a-Stufen (Anm. 1–3) inkl.
  Gesetzes- und valorisierten Werten (BGBl. II Nr. 131/2023 ab 1.5.2023).
- `ratg.erv_erhoehung(kind, *, valorized=True)` und `ratg.ErvKind` Enum.
- 7 neue Tests in `tests/test_renderer.py` (ERV-Lookups, Boolean-Alias,
  Bestätigung dass ES/SG ohne ERV gerechnet werden, Markdown-Inhalt,
  Fehlerpfad bei unbekanntem Kind).
- RATG-Tarifdaten für **TP 3 Teil B** (Berufungen, Berufungsbeantwortungen,
  Rekurse, Rekursbeantwortungen, Beschwerden) und **TP 3 Teil C** (Revisionen,
  Revisionsrekurse, Rekurse an den OGH) als `data/ratg/tp3b.json` und
  `data/ratg/tp3c.json`. Werte nach BGBl. II Nr. 131/2023 (ab 1.5.2023).
- `ratg.Tarifpost` erweitert um `TP3B = "3b"` und `TP3C = "3c"`; die
  bestehenden API-Funktionen (`tarifsatz`, `einheitssatz`,
  `streitgenossenzuschlag`) funktionieren ohne weitere Änderungen mit den
  neuen Keys.
- Beispiel-Eingabe `examples/berufung_50000.json` (Berufung,
  Berufungsinteresse 50.000 EUR → Gesamt 5.041,38 EUR inkl. GGG TP 2 und USt).
- 16 zusätzliche Tests in `tests/test_ratg.py`: Bracket-Lookups,
  inkrementelle Stufe, Promille-Stufen (1,25 ‰ / 0,625 ‰ für TP 3B; 1,5 ‰ /
  0,75 ‰ für TP 3C), Cap-Verhalten und ein Berufungs-Integrations-Smoke-Test.
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
