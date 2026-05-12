# Gerichtskostennote

Werkzeuge und strukturierte Daten zur Berechnung einer **Gerichtskostennote** nach österreichischem Recht — auf Basis des **Gerichtsgebührengesetzes (GGG)** für Gerichtsgebühren und des **Rechtsanwaltstarifgesetzes (RATG)** für Rechtsanwaltskosten.

> Status: Frühphase. Aktuell sind die GGG-Tarifposten 1–4 (Zivilprozess erste/zweite/dritte Instanz, Exekutionsverfahren) als maschinenlesbares JSON erfasst. RATG-Tarifdaten und eine Berechnungsbibliothek folgen.

## Zielbild

1. **Tarifdaten als Single Source of Truth** — GGG- und RATG-Tarife in versionierten JSON-Dateien, mit Stand-Datum und Valorisierungs-Tracking.
2. **Berechnungsbibliothek** (Python) — Pauschalgebühr nach Streitwert, Anwaltskosten nach Tarifpost/Leistung, Reduktionen (Anm. 3, 4 TP 1), Streitgenossenzuschlag, Einheitssatz.
3. **Erstellung der Kostennote** — strukturierte Eingabe (Streitwert, Verfahrensart, Leistungen) → fertige Note (Markdown, später PDF).

## Inhalt des Repos

| Pfad | Inhalt |
|---|---|
| `data/ggg/` | GGG-Tarifposten als JSON (TP 1, 2, 3, 4 + Index + Schema-Doku) |
| `20260414 Gerichtsgebührengesetz_gesamt.pdf` | RIS-Konsolidat GGG, Stand 14.04.2026 |
| `20260414 Rechtsanwaltstarifgesetz _gesamt.pdf` | RIS-Konsolidat RATG, Stand 14.04.2026 |
| `20260414 RIS - Rechtsanwaltstarifgesetz Anl. 1 - Bundesrecht konsolidiert.pdf` | RATG Anlage 1 (Tarif) |

Siehe [`data/ggg/README.md`](data/ggg/README.md) für die Tarifdaten-Struktur.

## Schnellbeispiel (manuell, ohne Bibliothek)

Streitwert 25.000 EUR, Zivilprozess 1. Instanz, kein Rückzug, keine Sonderregel:

→ Stufe TP 1: „über 7.000 Euro bis 35.000 Euro" → **974 EUR** (valorisiert ab 1.4.2025, BGBl. II Nr. 51/2025).

```json
{
  "ueber": 7000,
  "bis": 35000,
  "betrag_gesetz": 792,
  "betrag_ab_2025_04_01": 974,
  "anmerkung": 7
}
```

## Roadmap

- [x] GGG TP 1–4 strukturiert erfassen
- [ ] GGG TP 5–8 (Insolvenz, Außerstreit, Pflegschaft, Verlassenschaft)
- [ ] GGG TP 9–15 (Eintragungs- und Justizverwaltungsgebühren)
- [ ] RATG Tarifposten + Einheitssatz + Streitgenossenzuschlag als JSON
- [ ] Python-Modul `gerichtskostennote` mit Tests gegen Worked Examples aus dem GGG
- [ ] CLI `gkn` (Eingabe Streitwert/Verfahren → Note)
- [ ] Markdown- und PDF-Renderer

## Quellen

Die Tarifdaten sind aus den RIS-Konsolidaten (Bundeskanzleramt Österreich) extrahiert. URL-Muster für die Geltende Fassung:

- GGG: <https://www.ris.bka.gv.at/GeltendeFassung.wxe?Abfrage=Bundesnormen&Gesetzesnummer=10002651>
- RATG: <https://www.ris.bka.gv.at/GeltendeFassung.wxe?Abfrage=Bundesnormen&Gesetzesnummer=10002603>

Die Valorisierung erfolgt durch Verordnung der Bundesministerin für Justiz nach § 31a GGG, zuletzt **BGBl. II Nr. 51/2025** (in Kraft 1.4.2025).

## Mitwirken

Siehe [CONTRIBUTING.md](CONTRIBUTING.md). Korrekturen an Tarifwerten sind besonders willkommen — bitte mit Verweis auf RIS-Fundstelle.

## Lizenz

MIT — siehe [LICENSE](LICENSE). Die im Repo abgelegten RIS-Konsolidate sind Bundesrecht und gemeinfrei (§ 7 UrhG).

## Haftung

Dieses Projekt liefert Werkzeuge, kein Rechtsanwalt-Ersatz. Tarifwerte können sich durch Novellen oder Valorisierungsverordnungen jederzeit ändern. Vor Einreichung einer Kostennote eigene Prüfung erforderlich.
