# GGG Tarifdaten

Strukturierte Tarifdaten zum österreichischen **Gerichtsgebührengesetz (GGG)**. Quelle ist das RIS-Konsolidat vom 14.04.2026 (PDF im Repo-Root), nachgeführt um:

- **BGBl. II Nr. 227/2026** — Valorisierungsverordnung nach § 31a GGG, in Kraft **1.8.2026**
- **BGBl. I Nr. 62/2026** (Budgetbegleitgesetz 2027-2028, Art. 14) — Neufassung von TP 1 Anm. 9 und TP 2/3 Anm. 6, in Kraft **1.10.2026**

## Was hier ist

Die Streitwert-basierten Pauschalgebühren im Zivilprozess und im Exekutionsverfahren:

| Datei | Bereich | Bemessungsgrundlage |
|---|---|---|
| `tp1_zivilprozess_erste_instanz.json` | Zivilprozess 1. Instanz | Streitwert |
| `tp2_zivilprozess_zweite_instanz.json` | Berufung/Rekurs 2. Instanz | Berufungsinteresse |
| `tp3_zivilprozess_dritte_instanz.json` | Revision/Revisionsrekurs 3. Instanz, § 615 ZPO | Revisionsinteresse |
| `tp4_exekutionsverfahren.json` | Exekutionsverfahren, alle Instanzen | Wert des Anspruchs |
| `index.json` | Übergeordnete Metadaten + Schema-Hinweise | — |

## Beträge

Jeder Betrag kann bis zu drei Stände führen:

- `betrag_gesetz` — Wert wie er im GGG-Tarif selbst steht.
- `betrag_ab_2025_04_01` — Valorisierung **BGBl. II Nr. 51/2025** (1.4.2025 – 31.7.2026). Nur noch Historie.
- `betrag_ab_2026_08_01` — Valorisierung **BGBl. II Nr. 227/2026** (ab 1.8.2026). **Aktueller Wert**, den der Rechner mit `valorized=True` verwendet.

Analog `sockel_*` (Sockelbetrag der offenen Spitzenstufe) und `mindestbetrag_*` (TP 3 lit. b). Die Prozent- und Promillesätze (1,2 % / 1,8 % / 2,4 % / 2,7 ‰ / 5 %) sind Gesetzesrecht und werden nicht valorisiert.

## Sondergebühren mit Gültigkeitszeitraum

In `spezialgebuehren` stehen Beträge, die das Budgetbegleitgesetz 2027-2028 neu regelt. Sie tragen `gilt_ab` / `gilt_bis`:

| Eintrag | TP 1 | TP 2 | TP 3 | Zeitraum |
|---|---:|---:|---:|---|
| `jn_49_2_2a_2b` (Ehestreitigkeiten nach § 49 Abs. 2 Z 2a/2b JN) | 433 | 475 | 709 | bis 30.9.2026 |
| `jn_49_2_2a_2d` (Streitigkeiten nach § 49 Abs. 2 Z 2a–2d JN) | 410 | 449 | 671 | ab 1.10.2026 |
| `ev_382b_382d_eo*` (EV nach §§ 382b–382d EO) | 205 | 224 | 335 | ab 1.10.2026; vorher gebührenfrei |

**Offene Auslegungsfrage:** Für `jn_49_2_2a_2d` nennt der Gesetzestext 410 / 449 / 671 EUR, also weniger als die Beträge, auf die die Verordnung die alten Anmerkungen einen Tag später angehoben hat. Die Daten folgen dem Gesetzeswortlaut; gegen die konsolidierte RIS-Fassung prüfen.

Die halbe Pauschalgebühr für gewöhnliche einstweilige Verfügungen (TP 1 Anm. 2, TP 2/3 Anm. 1a) bleibt unverändert; sie gilt nicht für EV nach §§ 382b–382d EO.

Diese Sondergebühren werden vom Rechner derzeit nicht verwendet — sie sind nur als Daten erfasst.

## Bracket-Semantik

Das GGG verwendet `über X bis Y`:

- `ueber` = exklusiv (Streitwert **>** `ueber`)
- `bis` = inklusiv (Streitwert **≤** `bis`)

Für Streitwerte oberhalb der höchsten Stufe greifen Promille- bzw. Prozentregeln (TP 1: 1,2 % + Sockel, TP 2: 1,8 % + Sockel, TP 3 lit. a: 2,4 % + Sockel, TP 4: 2,7 ‰ vom übersteigenden Teil).

## Fälligkeit (nicht im Rechner abgebildet)

Seit 1.10.2026 (§ 2 Z 1 lit. c und d GGG idF BGBl. I Nr. 62/2026):

- Wird nach mündlicher Urteilsverkündung eine Berufung angemeldet, entsteht ein Viertel der TP-2-Pauschalgebühr schon mit der Anmeldung. Es ist nur zu entrichten, wenn die Berufung dann nicht erhoben wird, und wird mit Ablauf der vierwöchigen Berufungsfrist fällig. Bemessungsgrundlage ist der Teil des Streitwerts, mit dem die anmeldende Partei unterlegen ist (§ 18 Abs. 2 Z 5).
- Bei EV nach §§ 382b–382d EO entsteht die Gebühr erst mit Rechtskraft der Entscheidung der jeweiligen Instanz.

## Noch offen

TP 5–15 (Insolvenz, Außerstreit, Eintragungsgebühren, Privatanklage, Justizverwaltung). Siehe `index.json#open_items`.
