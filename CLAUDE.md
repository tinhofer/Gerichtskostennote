# CLAUDE.md — Orientierung für Claude-Sessions in diesem Repository

Dieses Dokument fasst zusammen, was beim Arbeiten an *Gerichtskostennote* zu wissen ist. Wenn du als Claude (oder anderer Agent) in dieses Repo kommst: lies das hier **vor** jeder substanziellen Änderung.

## Projekt

Werkzeuge und strukturierte Daten zur Berechnung einer österreichischen **Gerichtskostennote**:
- **Gerichtsgebühren** nach GGG (Gerichtsgebührengesetz)
- **Anwaltskosten** nach RATG (Rechtsanwaltstarifgesetz) inkl. § 15 Streitgenossenzuschlag, § 23 Einheitssatz, § 23a ERV-Erhöhung
- **Auslagen** (Barauslagen ohne USt — Reisekosten, Porto etc.)
- **Renderer** für Markdown und PDF (A4)

User: Praktizierender Rechtsanwalt in Wien (Dr. Andreas Tinhofer, Am Heumarkt 7). Setzt das Tool für echte Kostennoten ein. Stabilität und juristische Korrektheit zählen.

## Repo-Layout

```
data/
  ggg/      tp1..tp4_*.json + index.json + README.md
  ratg/     tp1, tp2, tp3a, tp3b, tp3c, einheitssatz, streitgenossenzuschlag, erv (+ index, README)
src/gerichtskostennote/
  ggg.py            Pauschalgebühren-Rechner
  ratg.py           Tarifsatz, Einheitssatz, Streitgenossenzuschlag, ERV, Tagsatzungsdauer
  renderer.py       compute() + render_markdown()
  pdf.py            render_pdf() (optional, braucht reportlab)
  cli.py            argparse-CLI, dispatch nach .pdf-Suffix oder -f
  __main__.py       python -m gerichtskostennote
tests/              pytest-Suite (siehe unten)
examples/           klage_15000.json, berufung_50000.json
20260414 *.pdf      RIS-Konsolidate GGG + RATG (Stand 14.04.2026)
pyproject.toml      setuptools, src/-Layout, Python ≥ 3.10
.github/workflows/  ci.yml — Python-Matrix 3.10/3.11/3.12
```

## Quick reference — Befehle

```bash
pip install -e ".[test]"          # Bibliothek + pytest + reportlab + pypdf
python -m pytest -q               # gesamte Suite (aktuell 158 Tests)
python -m gerichtskostennote examples/klage_15000.json           # Markdown
python -m gerichtskostennote examples/klage_15000.json -o x.pdf   # PDF
gkn input.json                                                    # Konsolen-Skript
```

## Eingabe-JSON-Schema (Renderer)

Pflichtfeld: `streitwert` (Zahl, EUR).

Top-level optional:
- `title`, `header` (dict mit `aktenzeichen`, `gericht`, `klaeger`/`beklagter` als Listen, `stand`)
- `umsatzsteuer_prozent` (Default 20)
- `default_personen_einer_seite` (Default 1 → kein Streitgenossenzuschlag)
- `default_fahrtkosten` (Zahl, EUR) — Standardbetrag für `fahrtkosten: true` Shortcut
- `anwaltsleistungen`: Liste
- `barauslagen`: Liste (Auslagen ohne USt)
- `gerichtsgebuehren`: Liste

Pro `anwaltsleistung`:
- Pflicht: `tp` (RATG-Key — `"1"`, `"2"`, `"3a"`, `"3b"`, `"3c"`)
- Optional: `datum`, `beschreibung`
- Optional: `personen_einer_seite`, `weitere_personen_andere_seite` (überschreibt Default)
- Optional: `einheitssatz_multiplier` (z. B. `2` für § 23 Abs. 5 RATG — auswärts, doppelter ES)
- Optional: `dauer_stunden` (für TP 3A/B/C Abschnitt II Tagsatzungen — 1 = einfacher Wert; 2 = 1,5×; 3 = 2×; 4 = 2,5×; jede angefangene weitere Stunde halbe Entlohnung)
- Optional: `erv` — `"einleitend"` (§ 23a Anm. 1, 5,00), `"weiterer"` / `true` (Anm. 2, 2,60), `"grundbuch_firmenbuch"` (Anm. 3, 9,50)
- Optional: `fahrtkosten` — `true` (= Default), Zahl (eigener Betrag) oder `false`/fehlend (keine Fahrtkosten). Erzeugt automatisch eine Barauslagen-Position.

Pro `barauslage`:
- Pflicht: `betrag`
- Optional: `datum`, `beschreibung`

Pro `gerichtsgebuehr`:
- Pflicht: `tp` (GGG-Key — `"1"`, `"2"`, `"3a"`, `"3b"`, `"4Ia"`, `"4Ib"`, `"4IIa"`, `"4IIb"`, `"4IIIa"`, `"4IIIb"`)
- Optional: `beschreibung`, `ermaessigung` (`rueckziehung_vor_zustellung` etc.), `bemessungsgrundlage` (überschreibt Top-Level-Streitwert)

Auto-generierte Fahrtkosten-Barauslagen kommen *vor* expliziten `barauslagen`-Einträgen, in Leistung-Reihenfolge.

## Konventionen

- **Decimal überall.** Geldbeträge nie als `float`. `quantize` mit `ROUND_HALF_UP` auf Cent (`Decimal("0.01")`).
- **§ 6 Abs. 2 GGG**: Hundertsatz-/Tausendsatzgebühren werden auf den nächsthöheren Euro **aufgerundet** (`ROUND_CEILING`). Implementiert in `ggg._ceil_euro`.
- **Bracket-Semantik**: `ueber` exklusiv (`>`), `bis` inklusiv (`≤`). Beide GGG und RATG nutzen das.
- **Doppelte Werte in den JSON-Daten**:
  - GGG: `betrag_gesetz` + `betrag_ab_2025_04_01` (BGBl. II Nr. 51/2025, nur noch Historie) + `betrag_ab_2026_08_01` (BGBl. II Nr. 227/2026, aktuell).
  - GGG-Sondergebühren, die nur zeitweise gelten, tragen `gilt_ab` / `gilt_bis` (siehe `data/ggg/README.md`).
  - RATG: `betrag_gesetz` + `betrag_ab_2023_05_01` (Valorisierung BGBl. II Nr. 131/2023).
  - Default: `valorized=True` (= aktuelle Beträge).
- **Tarifstand**: RIS-Konsolidate vom 14.04.2026 (PDF im Repo-Root); GGG nachgeführt um BGBl. II Nr. 227/2026 (ab 1.8.2026) und BGBl. I Nr. 62/2026 Art. 14 (ab 1.10.2026). RATG: keine Änderung der Tarifbeträge seit BGBl. II Nr. 131/2023 (Stand 26.10.2026).
- **Neue Valorisierung einspielen**: neues Feld `*_ab_JJJJ_MM_TT` neben den alten Werten anlegen, in `ggg.py` bzw. `ratg.py` die gelesenen Feldnamen umstellen, Tests anpassen. Alte Werte als Historie behalten.
- **§ 23 Abs. 5 RATG** Spezialfälle (Verdoppelung etc.) werden über `einheitssatz_multiplier` exponiert — Daten dafür hardgecodet nicht, User setzt's pro Leistung.

## Was implementiert ist (Stand 26.10.2026)

**GGG**: TP 1–4 vollständig (Pauschalgebühren Zivilprozess 1./2./3. Instanz; Exekutionsverfahren mit den Multiplikatoren Z II/III).

**RATG**: TP 1, 2, 3 Teil A/B/C; § 23 Einheitssatz; § 15 Streitgenossenzuschlag (10 % + 5 % je weitere, max. 50 %); § 23a ERV-Erhöhung (alle 3 Anmerkungen); Tagsatzungsdauer-Faktor für Abschnitt II.

**Renderer**: Markdown + PDF (ReportLab), CLI mit Format-Auto-Detection. Header-Block, Anwaltskosten-Tabelle (8 Spalten inkl. ERV), Barauslagen-Sektion, Gerichtsgebühren-Sektion, Gesamtsumme.

## Was bewusst nicht implementiert ist

- **RATG TP 3A** (Exekutionsverfahren — andere Struktur als TP 3 A/B/C, eigene Schemen für Forderungsbetreibung etc.)
- **RATG TP 4–9** (Strafverfahren, Reisekosten i.S.d. TP 5, Schreibgebühren TP 6, außergerichtliche Leistungen TP 7, Stundensätze TP 8, Verfahrenshilfe TP 9)
- **§ 23 Abs. 6–10 RATG** Spezialregeln (bedingter Zahlungsbefehl, dreifacher/vierfacher Einheitssatz im Berufungsverfahren ohne Beweisaufnahme etc.). Multiplier-Hook existiert, Daten dafür nicht.
- **GGG TP 5–8** (Insolvenz, Pflegschaft, Verlassenschaft, Außerstreit)
- **GGG TP 9–15** (Eintragungs- und Justizverwaltungsgebühren)
- **Anm.-14-Caps für TP 3 Abschnitt II** (weitere-Stunden-Cap) — relevant erst bei extremen Streitwerten
- **Vollwertige Paketauslieferung**: Datenfiles unter `data/` werden per `parents[2]` aus dem src-Layout gelesen. Editable-Install ist die getestete Konfiguration.

## Wichtige Auslegungsfragen (für die Codeebene relevant)

- **§ 23a Satz 3 RATG**: Der ERV-Erhöhungsbetrag wird nicht in die Bemessung von Einheitssatz und Streitgenossenzuschlag einbezogen — aber in den Netto-Betrag und damit in die USt-Basis. Im Code: `streitgenossenzuschlag(verdienst + es, ...)` (ohne ERV); USt wird auf `anwalt_netto` berechnet, der ERV enthält.
- **§ 23 Abs. 5 RATG (auswärtige Leistung + doppelter ES)** verlangt strikt, dass keine Reisekosten geltend gemacht werden. Tool erzwingt das nicht — Userverantwortung. Der User weiß das.
- **Klage gegen Klagebeantwortung**: Beide TP 3A; nur Klage ist `erv: "einleitend"`, alle anderen `erv: "weiterer"` (oder `true`).

## Workflow / PR

- `main` ist Default-Branch und enthält den aktuellen Stand. Neue Arbeit immer auf einem eigenen Branch von `main` beginnen: `git fetch origin && git checkout main && git pull && git checkout -b claude/<thema>`.
- Pro Thema ein PR gegen `main`; der User merged selbst. Nicht direkt auf `main` pushen.
- PR-Beschreibung bei weiteren Commits mit `mcp__github__update_pull_request` aktuell halten.
- Ein offener PR wird in der Session beobachtet: CI-Ergebnisse, Reviews und der Merge kommen als Benachrichtigungen herein.
- Bisherige PRs (beide gemerged): #1 GGG/RATG-Rechner, Renderer, CLI; #2 GGG-Valorisierung 1.8.2026 und Budgetbegleitgesetz 2027-2028.
- Alte Remote-Branches `claude/initial-repo-setup-067NM`, `claude/plan-next-priorities-hRvRZ` und `claude/ggg-novellen-aug-okt-2026` sind erledigt; löschen nur auf ausdrückliche Anweisung des Users.

## Rechtsquellen online prüfen

- `www.ris.bka.gv.at` ist in der Cloud-Umgebung freigeschaltet, liefert automatisierten Abfragen aber nur eine Bot-Schutzseite (Myra Cloud, HTTP 503) — auch für direkte PDF-Links. Nicht umgehen.
- Für automatisierte Abfragen die RIS-Open-Data-API verwenden: Suche über `data.bka.gv.at/ris/api/v2.6/Bundesrecht?Applikation=BrKons&Gesetzesnummer=10002667&Fassung.FassungVom=JJJJ-MM-TT`, Volltexte über die zurückgelieferten URLs auf `ogd.ris.bka.gv.at` (beide Hosts sind freigeschaltet). Der GGG-Tarif hängt in RIS am Dokument „Art. 1 § 32“.
- RIS übernimmt Valorisierungsverordnungen mit Verzögerung in die Fußnoten (Stand 26.10.2026: BGBl. II Nr. 227/2026 fehlte noch). Für Beträge immer das BGBl. selbst als Primärquelle nehmen.
- Ohne Zugriff: den User bitten, BGBl.-PDFs hochzuladen, und mit `pdftotext -layout` auswerten.
- Nach einem Container-Neustart fehlen ggf. Pakete: `python3 -m pip install -e ".[test]"` (mit `python3 -m pip`, nicht `pip`, sonst landet das Paket im falschen Interpreter).

## Tests laufen lassen

```bash
python -m pytest -q              # quick
python -m pytest -v              # verbose
python -m pytest tests/test_ratg.py::test_tagsatzung_two_hours_one_and_a_half
```

Aktuell **158 Tests** in 4 Dateien:
- `tests/test_ggg.py` (45) — GGG TP 1–4, Datenintegrität der Valorisierung und der BBG-Sondergebühren
- `tests/test_ratg.py` (49) — RATG TP 1/2/3A/3B/3C, § 23, § 15, ERV, Tagsatzungsdauer
- `tests/test_renderer.py` (44) — compute(), Markdown, CLI, ERV, Barauslagen, Fahrtkosten, dauer_stunden
- `tests/test_pdf.py` (10) — ReportLab-Renderer, CLI-Dispatch, pypdf-Textextraktion

## Wenn ich neue Tarifdaten ergänze

1. JSON in `data/<gesetz>/` mit Stand-Datum und Valorisierungsverweis.
2. Module-Load-Logik in `ratg.py`/`ggg.py` erweitern.
3. Worked-Example-Test in `tests/test_<gesetz>.py` mit Werten aus dem PDF.
4. `data/<gesetz>/README.md` und `data/<gesetz>/index.json#open_items` updaten.
5. `CHANGELOG.md` Eintrag im Unreleased-Block.
6. Tests laufen lassen, dann commit + push.

## Wenn der User mich um eine Kostennote-Berechnung bittet

1. JSON in `/tmp/` schreiben, **nicht** ins Repo.
2. `python3 -m gerichtskostennote /tmp/<name>.json` ausführen, das Markdown im Chat zeigen.
3. Bei Unklarheiten (z. B. wie viele Personen, ob ERV einleitend oder weiterer Schriftsatz) **explizit nachfragen oder die Annahme nennen**.
4. Bei Funktions-Lücken (z. B. Stundenanzahl bei Tagsatzung) erst Feature einbauen, Tests grün stellen, dann anwenden.
5. Manuelle Vorrechnungen mit der Tool-Ausgabe gegenprüfen.

## Was du nicht tun sollst

- **Keine** Tarifwerte aus dem Gedächtnis annehmen — immer aus `data/` lesen oder das User-Provided RIS-PDF konsultieren.
- **Keine** Updates am Default-Branch ohne explizite Anweisung.
- **Keine** Force-Pushes, keine `--amend` auf gepushten Commits.
- **Keine** Branches löschen, ohne dass der User es explizit anweist (der Bootstrap-Branch z. B. wartet auf User-Action).
- **Keine** float-Arithmetik für Geld.
