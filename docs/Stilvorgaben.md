# Stilvorgaben für Abbildungen im Leitfaden Ingenieurmethoden

**Status:** Entwurf 0.1.0. Die Vorgaben sind aus den Abbildungen von Kapitel 4 abgeleitet und noch nicht von der Redaktion werkweit beschlossen.
**Maschinenlesbare Fassung:** [`stil/stil.yaml`](../stil/stil.yaml). Bei Abweichungen gilt die YAML-Datei.

## Das Wichtigste in Kürze

1. **Vektor-PDF in fester Größe.** Jede Abbildung wird als `media/XX-name.pdf` abgelegt (XX = Kapitelnummer) und **ohne Skalierung** eingebunden: `\includegraphics{media/XX-name.pdf}`.
2. **Schrift wie im Text:** TeX Gyre Heros, Formelzeichen in Fira Math. Beschriftungen 9 pt, Ticks und Legende 8 pt.
3. **Drei Formate** mit fester Achsenfläche (siehe unten). Die Höhe der Abbildung ergibt sich aus dem Inhalt.
4. **Feste Farbreihenfolge** und zusätzlich unterschiedliche Linienstile, damit die Abbildung auch in Graustufen und bei Farbsehschwäche lesbar bleibt.
5. **Dezimalkomma**, keine Tausenderpunkte, echtes Minuszeichen.
6. **Keine zwei y-Achsen.** Stattdessen zwei Felder übereinander.

## Formate

Alle Maße in mm. Die Achsenfläche ist der Bereich innerhalb der Achsen.

| Format | Breite der Abbildung | Achsenfläche (B × H) | Rand links / rechts | Einsatz |
|---|---|---|---|---|
| Standard | 124 (0,8 × Textbreite) | 103 × 64 | 17 / 4 | Einzeldiagramm, Regelfall |
| zweifeldrig | 124 | 2 × (103 × 40), Abstand 4 | 17 / 4 | zwei Größen über derselben x-Achse |
| breit | 155 (Textbreite) | 134 × 82,8 | 17 / 4 | viele Reihen, Karten, Schemata mit Tabelle |

Die Seitenverhältnisse 103 : 64 und 134 : 82,8 entsprechen etwa dem Goldenen Schnitt (1 : 0,618). Durch die gleichen Ränder liegen die Achsen aller Standardabbildungen auf der Seite genau untereinander.

Höhe der Abbildung = oberer Rand (3) + Achsenfläche + unterer Rand. Der untere Rand beträgt 10 mm ohne Legende; mit Legende 11,5 mm (Abstand Achse – Legende) + 4,25 mm je Legendenzeile + 1 mm, also 16,75 mm bei einer, 21 mm bei zwei Zeilen.

## Schrift und Text

| Element | Schrift | Größe |
|---|---|---|
| Achsentitel, Beschriftungen in der Abbildung | TeX Gyre Heros | 9 pt |
| Tick-Beschriftung, Legende, Tabellen in der Abbildung | TeX Gyre Heros | 8 pt |
| Formelzeichen | Fira Math | wie umgebender Text |

In Excel und PowerPoint wird statt TeX Gyre Heros **Arial** verwendet (gleiche Zeichenbreiten). Office kann TeX Gyre Heros nicht als Vektorschrift in ein PDF einbetten (siehe [Office-Anleitung](Office.md)).

- **Achsentitel:** „Größe *Symbol* in Einheit“, z. B. „Gastemperatur *T* in °C“, „Wärmefreisetzungsrate *Q̇* in MW“. Reicht der Platz nicht (Format zweifeldrig), genügen Symbol und Einheit; die Größe nennt dann die Bildunterschrift.
- **Zahlen** an den Achsen ab 1 000 000 bzw. unter 0,0001 als *a*·10ⁿ; besser eine passende Einheit wählen (MW statt W).
- **Textfarbe** `#0b0b0b` (nahezu Schwarz), wie Achsen und Pfeile.
- **Kein Gesamttitel** in der Abbildung. Er steht in der Bildunterschrift. Feldtitel nur zur Unterscheidung mehrerer Felder.
- **Direktbeschriftungen** liegen innerhalb der Achsenfläche. Texte überlappen sich nicht und ragen nicht über den Rand.
- Mehrzeilige Beschriftungen mit Zeilenabstand 1,1.

## Achsen und Linien

| Element | Wert |
|---|---|
| Achsenlinien | 0,6 pt, nur links und unten |
| Ticks | innen, 3 pt lang, 0,6 pt, keine Nebenticks |
| Gitter | hellgrau `#d9d8d4`, 0,4 pt, hinter den Daten |
| Datenlinien | 1,4 pt; Nebenkurven in Schemata 1,0 pt |
| Hilfslinien | grau `#52514e`, gestrichelt, 0,8 pt |
| Marker | 4 pt Durchmesser |
| Achsgrenzen | ohne Angabe genau der Datenbereich (kein zusätzlicher Rand) |

## Farben

Die Reihen erhalten die Farben **immer in dieser Reihenfolge**. Reihe 1 ist immer blau, auch wenn eine andere Reihe weggelassen wird.

| Nr. | Farbe | Hex | Linienstil |
|---|---|---|---|
| 1 | blau | `#2a78d6` | durchgezogen |
| 2 | orange | `#eb6834` | gestrichelt |
| 3 | türkis | `#1baf7a` | gepunktet |
| 4 | gelb | `#eda100` | Strichpunkt |
| 5 | rosa | `#e87ba4` | Strich-Punkt-Punkt |
| 6 | grün | `#008300` | fein gepunktet |
| 7 | violett | `#6250d6` | lang gestrichelt |
| 8 | rot | `#e34948` | durchgezogen (vorläufig) |

Neutrale Farben: Text `#0b0b0b`, Grau `#52514e`, Gitter `#d9d8d4`, Flächen `#ecebe7`.

Bei mehr als acht Reihen werden Reihen zusammengefasst oder auf mehrere Felder verteilt. Weitere Farben werden nicht erfunden.

> Die Palette stammt aus einer allgemeinen Referenzpalette für Datenvisualisierung. Benachbarte Reihen sind – auch bei Rot-Grün-Schwäche – rechnerisch gut unterscheidbar (`vfdb-farbpruefung`). Bei der seltenen Blau-Gelb-Schwäche (vom Werkzeug nur angegeben, nicht bewertet) sind benachbart 4/5 (gelb/rosa) deutlich und 6/7 knapp schwach, nicht benachbart 2/8 deutlich sowie 1/6 und 2/5 knapp. Nicht benachbarte Paare sind teils schwach: deutlich Reihe 2/8 (orange/rot, für alle) sowie 2/6 (orange/grün) und 1/7 (blau/violett) bei Rot-Grün-Schwäche, 1/7 auch für Normalsichtige knapp; knapp außerdem 2/4, 2/5 und 5/8 für Normalsichtige und 3/5, 3/8 und 6/8 bei Rot-Grün-Schwäche (`vfdb-farbpruefung --alle-paare` nennt das ungünstigste Paar). Bei Linien unterscheidet hier der Linienstil. Reine Punktdarstellungen haben dieses zweite Merkmal nicht: dann möglichst wenige Reihen oder Reihen direkt beschriften. Drei Farben (türkis, gelb, rosa) haben auf weißem Papier weniger als 3 : 1 Kontrast; Linienstil und Linienstärke gleichen das aus. Falls es vfdb-Hausfarben gibt, entscheidet die Redaktion über den Austausch.

## Legende

- Unter der Abbildung, zentriert, ohne Rahmen.
- Bis 3 Einträge in einer Zeile, 4 Einträge in 2 Spalten, ab 5 Einträgen in 3 Spalten. Passen die Einträge nicht in die Breite, weniger Spalten.
- Einträge zeilenweise in Lesereihenfolge: von links nach rechts, dann die nächste Zeile.
- Bei nur einer Reihe keine Legende. Der Achsentitel oder die Bildunterschrift benennt sie.

## Schemata

- Achsen als Pfeile, ohne Gitter und Tick-Striche. „Zeit *t*“ rechtsbündig unter der Pfeilspitze.
- Einheitliche Pfeile: 0,6 pt, gefüllte Spitze (so breit wie lang). Achsenpfeil 3,6 pt Spitzenlänge, Hinweispfeil 2,8 pt, Maßpfeil 2,4 pt (beidseitig).
- Hinweispfeile **waagerecht oder senkrecht**, nicht „fast senkrecht“.
- Phasen als Maßpfeil 8 mm unter der Zeitachse, Text darunter.
- Flächen unter Kurven in Grau `#ecebe7` oder in der Reihenfarbe mit 18 % Deckkraft.

## Beispiele

Beispiele für Python, Excel (Stufe A) und LaTeX liegen unter [`beispiele/`](../beispiele/), ein Office-Beispiel in [`office/`](../office/). Die Abbildungen von Kapitel 4 des Leitfadens sind nach diesen Vorgaben entstanden; sie füllen mehrspaltige Legenden noch spaltenweise statt zeilenweise.
