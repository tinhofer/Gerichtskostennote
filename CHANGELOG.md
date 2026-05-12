# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Strukturierte Tarifdaten zum Gerichtsgebührengesetz (GGG), Tarifposten 1–4
  (`data/ggg/tp1..tp4_*.json`), inklusive `index.json` und Schema-Doku.
  Erfasst sind Stufenbeträge gemäß Gesetz **und** valorisierte Beträge nach
  BGBl. II Nr. 51/2025 (in Kraft 1.4.2025).
- `data/ggg/README.md` mit Bracket-Semantik (über/bis exklusiv/inklusiv).

### Changed
- README.md umgeschrieben — Projekt ist eine österreichische Gerichtskostennote-
  Toolbox (GGG + RATG), nicht das ursprüngliche generische Claude-Code-Scaffold.

## [0.1.0] - 2026-01-02

### Added
- Initial repository structure
- Basic project scaffolding
- README mit Projektstruktur, CONTRIBUTING.md, MIT License, EditorConfig,
  GitHub-Templates, CI-Workflow-Skeleton
- Referenz-PDFs: GGG- und RATG-Konsolidate (Stand 14.04.2026)
