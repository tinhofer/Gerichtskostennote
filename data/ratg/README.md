# RATG Tarifdaten

Strukturierte Tarifdaten zum österreichischen **Rechtsanwaltstarifgesetz (RATG)**, Anlage 1, Stand 14.04.2026. Quelle ist das RIS-Konsolidat (PDF im Repo-Root).

## Was hier ist

Erste Tranche, beschränkt auf die für eine typische Zivilprozess-Kostennote wesentlichen Tarifposten und die zwei Aufschlags-Regeln (§ 23 Einheitssatz, § 15 Streitgenossenzuschlag):

| Datei | Norm | Inhalt |
|---|---|---|
| `tp1.json` | RATG Anl. 1 TP 1 | Schriftsätze einfacher Art |
| `tp2.json` | RATG Anl. 1 TP 2 | Kurze Schriftsätze und Tagsatzungen |
| `tp3a.json` | RATG Anl. 1 TP 3 Teil A | Klagen, Klagebeantwortungen, Tagsatzungen 1. Instanz |
| `tp3b.json` | RATG Anl. 1 TP 3 Teil B | Berufungen, Rekurse, Beschwerden (2. Instanz) |
| `tp3c.json` | RATG Anl. 1 TP 3 Teil C | Revisionen, Revisionsrekurse, OGH-Schriftsätze (3. Instanz) |
| `einheitssatz.json` | § 23 RATG | Pauschalanteil für Nebenleistungen (60 % bzw. 50 %) |
| `streitgenossenzuschlag.json` | § 15 RATG | Zuschlag bei mehreren Personen (10 % + 5 % je weitere, max. 50 %) |
| `index.json` | — | Metadaten + gemeinsame Bracket-Stützstellen + offene Punkte |

## Tarifaufbau

Alle drei Tarifposten teilen sich dieselbe Bracket-Struktur in der Bemessungsgrundlage:

- Zwölf fixe Stufen von `bis 40` bis `über 7 270 bis 10 170` EUR (TP-spezifische Beträge).
- **Inkremental** (10 170 → 34 820 EUR): für jede angefangene weitere `1 450 EUR` ein Schritt um den TP-spezifischen `step_amount` mehr.
- **Zusatzschritt** (34 820 → 36 340 EUR): genau ein weiterer Schritt (`step_amount`).
- **Promille-Stufe 1** (36 340 → 363 360 EUR): vom Mehrbetrag über 36 340 EUR der TP-spezifische Tausendsatz (`promille_36340_to_363360_vT`).
- **Promille-Stufe 2** (über 363 360 EUR): vom Mehrbetrag über 363 360 EUR der niedrigere TP-spezifische Tausendsatz.
- **Cap**: die Entlohnung übersteigt nie den TP-spezifischen Höchstbetrag.

## Beträge

Wie bei den GGG-Daten: jede Stelle führt `betrag_gesetz` (RATG-Wortlaut) und `betrag_ab_2023_05_01` (Valorisierung **BGBl. II Nr. 131/2023**, in Kraft seit 1.5.2023). Für eine Kostennote 2026 gilt `betrag_ab_2023_05_01`.

## Noch offen

- TP 3A (Exekutionsverfahren)
- TP 4 (Strafverfahren), TP 5 (Reisekosten), TP 6 (Schreibgebühren)
- TP 7 (außergerichtliche Leistungen), TP 8 (Stundensätze), TP 9 (Verfahrenshilfe)
- § 23 Abs. 5–10 RATG (Verdoppelung/Verdreifachung/Vervierfachung des Einheitssatzes in Spezialfällen)
- § 23a RATG (ERV-Erhöhung)

Siehe `index.json#open_items`.
