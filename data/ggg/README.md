# GGG Tarifdaten

Strukturierte Tarifdaten zum österreichischen **Gerichtsgebührengesetz (GGG)**, Stand 14.04.2026. Quelle ist das RIS-Konsolidat (PDF im Repo-Root).

## Was hier ist

Erste Tranche, beschränkt auf die Streitwert-basierten Pauschalgebühren im Zivilprozess und im Exekutionsverfahren:

| Datei | Bereich | Bemessungsgrundlage |
|---|---|---|
| `tp1_zivilprozess_erste_instanz.json` | Zivilprozess 1. Instanz | Streitwert |
| `tp2_zivilprozess_zweite_instanz.json` | Berufung/Rekurs 2. Instanz | Berufungsinteresse |
| `tp3_zivilprozess_dritte_instanz.json` | Revision/Revisionsrekurs 3. Instanz, § 615 ZPO | Revisionsinteresse |
| `tp4_exekutionsverfahren.json` | Exekutionsverfahren, alle Instanzen | Wert des Anspruchs |
| `index.json` | Übergeordnete Metadaten + Schema-Hinweise | — |

## Beträge

Jede Stufe enthält zwei Felder:

- `betrag_gesetz` — Wert wie er im GGG-Tarif selbst steht.
- `betrag_ab_2025_04_01` — Wert nach Valorisierung gemäß **BGBl. II Nr. 51/2025** (in Kraft seit 1.4.2025). Das ist der derzeit zu zahlende Betrag.

Für eine Gerichtskostennote 2026 ist `betrag_ab_2025_04_01` heranzuziehen.

## Bracket-Semantik

Das GGG verwendet `über X bis Y`:

- `ueber` = exklusiv (Streitwert **>** `ueber`)
- `bis` = inklusiv (Streitwert **≤** `bis`)

Für Streitwerte oberhalb der höchsten Stufe greifen Promille- bzw. Prozentregeln (TP 1: 1,2 % + Sockel, TP 2: 1,8 % + Sockel, TP 3 lit. a: 2,4 % + Sockel, TP 4: 2,7 ‰ vom übersteigenden Teil).

## Noch offen

TP 5–15 (Insolvenz, Außerstreit, Eintragungsgebühren, Privatanklage, Justizverwaltung). Siehe `index.json#open_items`.
