# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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
