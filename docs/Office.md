# Abbildungen mit Excel und PowerPoint (Stufe B)

Für alle, die ohne zusätzliche Programme arbeiten wollen. Die Vorlagen liefern Farben, Linien, Schriftgrößen, Lage der Achsenfläche und Abbildungsgröße nach den [Stilvorgaben](Stilvorgaben.md).

**Unterschiede zu Stufe A (Python, LaTeX, Excel als Datenquelle):**

| | Stufe A | Stufe B (Office) |
|---|---|---|
| Schrift | TeX Gyre Heros, wie der Leitfaden | **Arial**: gleiche Zeichenbreiten, einzelne Buchstaben leicht anders geformt |
| Formelzeichen | automatisch kursiv, Formelsatz | von Hand kursiv bzw. tiefgestellt; Q̇ und Formeln nur eingeschränkt |
| Achsenfläche, Titel, erste Legendenzeile | exakt | etwa ±0,2 mm |
| Legende | Spalten und Zeilen automatisch | Excel ordnet die Einträge selbst an; Feldgröße von Hand |
| Teilstriche | 3 pt | 2,4 pt (in Excel nicht einstellbar) |
| Strichmuster | identisch | ähnlich (Office-Strichmuster) |

Warum Arial? Office kann TeX Gyre Heros nicht als Schrift in ein PDF einbetten. Es speichert den Text dann als Rasterbild, und das PDF wäre keine Vektorgrafik mehr. Arial ist auf jedem Windows-Rechner vorhanden und hat dieselben Zeichenbreiten.

Wer exakte Abbildungen aus Excel-Daten braucht, nutzt den [Excel-Weg der Stufe A](Excel.md). Das gilt auch für das Format **zweifeldrig** (zwei Größen übereinander statt einer zweiten y-Achse): Dafür gibt es in Stufe B keine Vorlage, und eine Sekundärachse in Excel widerspricht den Stilvorgaben.

## Dateien

Im Ordner [`office/`](../office/):

| Datei | Zweck |
|---|---|
| `vfdb_Diagramm_standard.xlsx`, `vfdb_Diagramm_breit.xlsx` | Arbeitsmappe mit fertig formatiertem Diagramm für 8 Reihen (Beispiel: nominelle Temperaturzeitkurven in Reihe 1 bis 3, Reihe 4 bis 8 leer) |
| `vfdb_Abbildung_standard.potx`, `vfdb_Abbildung_breit.potx` | PowerPoint-Vorlage: Folie so groß wie die Abbildung, Führungslinien an der Achsenfläche |
| `vfdb_Diagramm.crtx` | Excel-Diagrammvorlage (Punkt-XY mit Linien, 8 Reihen) |
| `vfdb_Leitfaden.thmx` | Office-Design mit den Leitfaden-Farben und Arial |

## Diagramm aus Excel

1. `vfdb_Diagramm_standard.xlsx` (bzw. `_breit`) kopieren und öffnen.
2. **Beispielwerte entfernen:** im Blatt „Daten“ die Zellen ab A2 markieren und **Entf** drücken (Inhalte löschen – **keine Zeilen oder Spalten löschen**, das Diagramm bezieht sich auf feste Zellen).
3. **Daten** eintragen: Spalte A die x-Werte, Spalte B bis I je eine Reihe (Reihe 1 bis 8, in dieser Reihenfolge erhalten sie Farbe und Linienstil), bis Zeile 10001. Zeile 1 enthält den Legendentext.
4. **Nicht benötigte Reihen löschen:** im Diagramm die Reihe anklicken und **Entf**. Leere Reihen sind nicht anklickbar; sie lassen sich über das Register *Format* (erscheint, wenn das Diagramm markiert ist) in der Auswahlliste links oben („Reihe 5“ usw.) auswählen. Bei nur einer Reihe auch die Legende löschen.
5. **Achsentitel ändern.** Formelzeichen kursiv: Zeichen markieren, **Strg+I**. Indizes: markieren, Rechtsklick → *Schriftart* → *Tiefgestellt*. Danach Titel mit der Maus wieder mittig an die Achsenfläche schieben; zu lange Titel werden beim Export abgeschnitten.
6. **Achsgrenzen und Teilstriche** unter *Achse formatieren* einstellen. Das Dezimalkomma an den Achsen kommt aus den Windows-Einstellungen; erscheint ein Punkt, unter *Datei* → *Optionen* → *Erweitert* „Trennzeichen vom Betriebssystem übernehmen“ abwählen und als Dezimaltrennzeichen `,` eintragen.
7. **Die Größe des Diagramms nicht ändern.** Das Diagrammobjekt ist rechts und unten absichtlich 15 mm größer als die Abbildung; dieser Rand wird beim Export abgeschnitten. Bei geänderter Größe verschiebt sich die Achsenfläche.
8. **Legende:** Das Legendenfeld ist für eine Zeile bemessen. Passen die Einträge nicht hinein, fehlen sie ohne Hinweis. Dann die Legende anklicken und am unteren Anfasser nach unten ziehen – **Höhe = Zahl der Zeilen × 4,25 mm** (8,5 mm für zwei, 12,75 mm für drei Zeilen). Excel verteilt die Zeilen gleichmäßig auf die Höhe; schon 0,3 mm Abweichung verändert den Zeilenabstand sichtbar. Bei langen Legendentexten setzt Excel die Einträge untereinander (eine Spalte), dann sind mehr Zeilen nötig.

### Als PDF speichern

1. Diagramm markieren (Rand anklicken), **Strg+C**.
2. `vfdb_Abbildung_standard.potx` doppelklicken. PowerPoint öffnet eine neue Präsentation mit einer leeren Folie in Abbildungsgröße.
3. **Folienhöhe anpassen, falls nötig – vor dem Einfügen:** *Entwurf* → *Foliengröße* → *Benutzerdefinierte Foliengröße*, nur die Höhe ändern (eine Rückfrage zum Skalieren ist bei der noch leeren Folie ohne Bedeutung). Die Vorlage ist für eine Legendenzeile bemessen (Standard 8,37 cm, breit 10,26 cm). Je weiterer Legendenzeile 0,425 cm höher; ohne Legende 0,675 cm niedriger (Standard 7,70 cm, breit 9,58 cm). Wird die Folie nach dem Einfügen geändert, verrutscht das Diagramm und muss erneut auf Position 0/0 gesetzt werden.
4. **Strg+V**, dann Rechtsklick auf das Diagramm → *Größe und Position* → *Position*: horizontal **0 cm**, vertikal **0 cm** (jeweils von der oberen linken Ecke).
5. Die Achsenfläche liegt jetzt auf etwa 0,2 mm genau. Bei unveränderter Folienhöhe zeigen das die Führungslinien (*Ansicht* → *Führungslinien*). Wurde die Folienhöhe geändert, verschiebt PowerPoint die waagerechten Führungslinien mit – dann gilt allein Position 0/0, das Diagramm nicht an diese Linien schieben.
6. **Persönliche Angaben entfernen:** *Datei* → *Informationen* → *Auf Probleme überprüfen* → *Dokument prüfen* → „Dokumenteigenschaften und persönliche Informationen“ entfernen. Sonst steht der eigene Name als Autor im PDF.
7. *Datei* → *Exportieren* → *PDF/XPS-Dokument erstellen*. Teile des Diagramms außerhalb der Folie werden dabei abgeschnitten.
8. Das PDF in Overleaf nach `media/` hochladen und ohne Skalierung einbinden: `\includegraphics{media/05-name.pdf}`.

### Diagrammvorlage für eigene Diagramme

`vfdb_Diagramm.crtx` nach `%APPDATA%\Microsoft\Templates\Charts` kopieren. Danach steht sie unter *Diagrammtyp ändern* → *Vorlagen* zur Verfügung und überträgt Farben, Linien und Schrift für bis zu 8 Reihen; die Achsgrenzen bleiben automatisch. Sie gilt nur für das **Format standard**: Die Lage der Achsenfläche stimmt nur, wenn das Diagramm vorher auf **13,9 × 9,88 cm** gesetzt wird (Register *Format* → *Größe*); die Achsentitel müssen neu geschrieben werden. Der Weg über die fertige Arbeitsmappe ist einfacher.

## Schema in PowerPoint

1. `vfdb_Abbildung_standard.potx` (bzw. `_breit`) doppelklicken.
2. Die Führungslinien zeigen die Achsenfläche (*Ansicht* → *Führungslinien*).
3. Neue Linien und Formen sind bereits 0,6 pt schwarz (Formen ohne Füllung), Text Arial 9 pt. Darüber hinaus:

| Element | Wert |
|---|---|
| Kurven | 1,4 pt, Farben in der Reihenfolge der Stilvorgaben: `#2A78D6`, `#EB6834`, `#1BAF7A`, `#EDA100`, `#E87BA4`, `#008300` (Akzentfarben 1–6 des Designs), `#6250D6`, `#E34948` (als Hexwert eingeben) |
| Hilfslinien | 0,8 pt, gestrichelt, Grau `#52514E` |
| Achsen, Hinweis- und Maßpfeile | 0,6 pt, gefüllte Dreiecksspitze, Schwarz `#0B0B0B` |
| Flächen | Hellgrau `#ECEBE7` |
| Beschriftungen | Arial 9 pt, auch Achsentitel; Marken an den Achsen (z. B. *t*₁), Legende und Tabellen 8 pt |

4. Persönliche Angaben entfernen (siehe oben) und *Datei* → *Exportieren* → *PDF/XPS-Dokument erstellen*.

## Office-Design für eigene Dateien

`vfdb_Leitfaden.thmx` nach `%APPDATA%\Microsoft\Templates\Document Themes` kopieren. Danach steht das Design in Excel und PowerPoint unter *Seitenlayout* bzw. *Entwurf* → *Designs* zur Auswahl, und die Leitfaden-Farben erscheinen in jeder Farbauswahl als Design-Farben. (Ein Doppelklick auf die Datei öffnet nur eine neue PowerPoint-Präsentation.)

## Hinweis für Pflegende

Die Office-Dateien werden mit `python office/erzeuge_office.py` aus `stil/stil.yaml` erzeugt: Windows mit Microsoft Office, LuaLaTeX und `pip install -e ".[office]"` (pywin32 und PyMuPDF; PyMuPDF steht unter AGPL-3.0 und wird nur lokal zum Messen genutzt). Excel und PowerPoint müssen dabei geschlossen sein.

Das Skript fügt das Diagramm wie ein Anwender in die PowerPoint-Vorlage ein, exportiert ein PDF, misst Achsenfläche, Achsentitel und erste Legendenzeile (Bezug: Python-Abbildung gleichen Formats) und korrigiert die Excel-Werte, bis die Abweichung bei etwa 0,2 mm liegt (Excel rastet Größen in Schritten von 1 pt = 0,35 mm ein). Es erzeugt alles zuerst in einem temporären Ordner, entfernt persönliche Angaben (Autor, Firma, Speicherpfad) und kopiert die Dateien erst dann nach `office/`. Mit `--test` bleiben Test-PDFs in `office/test/`, mit `--ausfuehrlich` werden die Abweichungen je Schritt ausgegeben. Geprüft wurde mit Microsoft 365 (Version 16) bei 96 dpi Bildschirmauflösung.
