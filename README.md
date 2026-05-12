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

Siehe [`data/ggg/README.md`](data/ggg/README.md) und [`data/ratg/README.md`](data/ratg/README.md) für die Tarifdaten-Struktur.

## Installation & Verwendung

```bash
pip install -e .              # Bibliothek + CLI (`gkn`) im Editable-Modus
pip install -e ".[test]"      # mit pytest
python -m pytest              # 94 Tests (GGG TP 1–4 + RATG TP 1/2/3A + Renderer/CLI)
```

### CLI: vollständige Kostennote aus JSON

```bash
gkn examples/klage_15000.json                  # nach stdout
gkn examples/klage_15000.json -o kosten.md     # in Datei
python -m gerichtskostennote -                  # liest JSON von stdin
```

Eingabe-Schema (siehe [`examples/klage_15000.json`](examples/klage_15000.json)):

```json
{
  "title": "Kostennote",
  "header": {
    "aktenzeichen": "1 Cg 123/26x",
    "gericht": "BG Innere Stadt Wien",
    "klaeger": ["Hans Mustermann", "Maria Mustermann"],
    "beklagter": ["XYZ GmbH"],
    "stand": "2026-05-12"
  },
  "streitwert": 15000,
  "umsatzsteuer_prozent": 20,
  "default_personen_einer_seite": 2,
  "anwaltsleistungen": [
    { "datum": "2026-03-15", "tp": "3a", "beschreibung": "Klage" }
  ],
  "gerichtsgebuehren": [
    { "tp": "1", "beschreibung": "Pauschalgebühr Klage 1. Instanz" }
  ]
}
```

Optional je Anwaltsleistung: `personen_einer_seite`, `weitere_personen_andere_seite`, `einheitssatz_multiplier` (für § 23 Abs. 5–9 RATG Spezialfälle). Je Gerichtsgebühr: `ermaessigung` (`rueckziehung_vor_zustellung`, `rueckziehung_erste_tagsatzung`, `einstweilige_verfuegung`, `rueckziehung_vor_bewilligung`) und `bemessungsgrundlage` (falls vom Streitwert abweichend).

### Bibliotheks-API

```python
from gerichtskostennote import (
    pauschalgebuehr, Ermaessigung,                # GGG
    tarifsatz, einheitssatz, streitgenossenzuschlag,  # RATG
)

# --- GGG: Pauschalgebühr ---
pauschalgebuehr("1", 25_000)                         # Decimal('974')
pauschalgebuehr("1", 25_000, valorized=False)        # Decimal('792') — Gesetzeswert
pauschalgebuehr(
    "1", 25_000, ermaessigung=Ermaessigung.RUECKZIEHUNG_VOR_ZUSTELLUNG
)                                                    # Decimal('243.50')
pauschalgebuehr("4Ia", 100_000)                      # Decimal('450')

# --- RATG: Anwaltskosten für eine Klage, Streitwert 15 000 EUR, zwei Kläger ---
sw = 15_000
verdienst = tarifsatz("3a", sw)                      # Decimal('487.00')
es        = einheitssatz(sw, verdienst)              # Decimal('243.50') — 50 %
sg        = streitgenossenzuschlag(verdienst + es, anzahl_personen_einer_seite=2)
                                                     # Decimal('73.05') — 10 %
# Klagekosten exkl. USt/Auslagen: 803.55 EUR
```

GGG-Tarifpost-Keys: `"1"`, `"2"`, `"3a"`, `"3b"`, `"4Ia"`, `"4Ib"`, `"4IIa"`, `"4IIb"`, `"4IIIa"`, `"4IIIb"`.
RATG-Tarifpost-Keys: `"1"`, `"2"`, `"3a"` (TP 3 Teil A).

Anmerkung: Die Bibliothek liest die JSON-Tarifdaten relativ zum Repo-Root (`data/`). Editable-Install (`pip install -e .`) ist daher derzeit empfohlen.

## Roadmap

- [x] GGG TP 1–4 strukturiert erfassen
- [x] Python-Modul `gerichtskostennote` mit Tests gegen Worked Examples aus dem GGG
- [x] RATG TP 1, 2, 3 Teil A + § 23 Einheitssatz + § 15 Streitgenossenzuschlag
- [x] CLI `gkn` + Markdown-Renderer (Eingabe Streitwert/Leistungen → vollständige Kostennote)
- [ ] RATG TP 3 Teil B/C (Berufung/Revision), TP 3A (Exekutionsverfahren), TP 4–9
- [ ] § 23 Abs. 5–10 RATG (Verdoppelung/Verdreifachung des Einheitssatzes in Spezialfällen), § 23a (ERV)
- [ ] GGG TP 5–8 (Insolvenz, Außerstreit, Pflegschaft, Verlassenschaft)
- [ ] GGG TP 9–15 (Eintragungs- und Justizverwaltungsgebühren)
- [ ] PDF-Renderer (z. B. via Pandoc / WeasyPrint)

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
