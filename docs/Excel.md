# Abbildungen aus Excel-Daten (Stufe A, genau im Leitfaden-Stil)

Die Daten und alle Angaben zur Abbildung stehen in einer Excel-Datei. Ein Befehl liest sie und erzeugt das PDF – mit demselben Werkzeug wie der Python-Weg, also genau im Leitfaden-Stil. Programmieren ist nicht nötig.

Voraussetzung: einmalige [Installation](Installation.md) von Python, MiKTeX und vfdb-stil. Wer nichts installieren möchte, nutzt den [Office-Weg](Office.md) (Stufe B).

## Ablauf

1. **Vorlage anlegen.** In der Eingabeaufforderung im gewünschten Ordner (wie man sie dort öffnet, auch bei Netzwerkordnern: [Installation, Hinweise](Installation.md#hinweise)):
   ```
   vfdb-abbildung --vorlage 05-rauchgastemperatur.xlsx
   ```
   Die Angabe **Dateiname** (Name des PDF) ist dann schon `05-rauchgastemperatur`. Alternativ [`excel/Vorlage_Abbildung.xlsx`](../excel/Vorlage_Abbildung.xlsx) aus dem Repository kopieren (Dateiname dort `00-beispiel`, bitte ändern). Die Vorlage enthält ein kleines Beispiel, das sofort funktioniert, und ein Blatt „Anleitung“.
2. **Ausfüllen** (Einzelheiten unten): Blatt „Daten“, Blatt „Reihen“, Blatt „Diagramm“.
3. **In Excel speichern und schließen.** Beim Speichern berechnet Excel Formeln; nur diese Werte werden gelesen.
4. **PDF erzeugen:**
   ```
   vfdb-abbildung 05-rauchgastemperatur.xlsx
   ```
   Das dauert etwa 20 Sekunden. Das PDF entsteht im Ordner der Excel-Datei und heißt wie die Angabe **Dateiname** im Blatt „Diagramm“ (nicht wie die Excel-Datei). Mit `--ziel media` landet es im Unterordner `media` des aktuellen Ordners.
5. **Ausgabe prüfen:** Der Befehl nennt die Maße und warnt, wenn Texte sich überlappen, über den Rand ragen oder ein Achsentitel länger als seine Achse ist (bei zweifeldrig dann nur Formelzeichen und Einheit). Das PDF ansehen.
6. **In Overleaf** nach `media/` hochladen und ohne Skalierung einbinden: `\includegraphics{media/05-rauchgastemperatur.pdf}`.

Ohne Eingabeaufforderung: [`excel/Abbildung_erzeugen.bat`](../excel/Abbildung_erzeugen.bat) neben die Excel-Dateien kopieren und eine Excel-Datei mit der Maus darauf ziehen.

Ein ausgefülltes Beispiel mit zwei Feldern: [`beispiele/excel/t2_brandentwicklung.xlsx`](../beispiele/excel/t2_brandentwicklung.xlsx). Es ergibt dieselbe Abbildung wie das Python-Beispiel `t2_brandentwicklung.py`.

## Blatt „Daten“

- Zeile 1: Spaltenüberschriften (jede nur einmal), darunter **nur Zahlen** – jedenfalls in den Spalten, die gezeichnet werden (x-Spalte und die Spalten im Blatt „Reihen“). Weitere Spalten, z. B. Bemerkungen oder Zeitstempel, werden nicht gelesen.
- Dezimalkomma wie in Excel üblich; Text wie „1.200“ wird als mehrdeutig abgelehnt.
- Leere Zellen erzeugen eine Lücke in der Kurve – auch Formeln mit leerem Ergebnis, z. B. `=WENN(A2="";"";…)`, und `#NV` (`=NV()`).
- Spaltenüberschriften dürfen Zeilenumbrüche (Alt+Enter) enthalten; im Blatt „Reihen“ und bei der Angabe x-Spalte dafür ein Leerzeichen schreiben.
- Formeln sind erlaubt (die Datei muss danach in Excel gespeichert worden sein).
- Datum und Uhrzeit werden nicht unterstützt – bitte als Zahl angeben (z. B. Minuten).

## Blatt „Reihen“

Eine Zeile je Kurve.

| Spalte | Bedeutung |
|---|---|
| Spalte | Spaltenüberschrift im Blatt „Daten“ |
| Legendentext | Text in der Legende. Gleicher Text = gleiche Farbe (z. B. dieselbe Größe in beiden Feldern). Leer = Kurve ohne Legendeneintrag. |
| Feld | 1 oder 2 (2 nur bei Format zweifeldrig); leer = 1 |
| Darstellung | Linie, Punkte oder Linie und Punkte; leer = Linie |
| Farbe Nr. | 1 bis 8 nach den Stilvorgaben; leer = nächste freie Farbe in fester Reihenfolge. Eine Farbe nur einmal vergeben. |

Höchstens 8 verschiedene Reihen; bei mehr Reihen zusammenfassen oder auf zwei Abbildungen verteilen.

## Blatt „Diagramm“

| Angabe | Bedeutung |
|---|---|
| Dateiname | Name des PDF ohne Endung, Kapitelnummer voran, z. B. `05-rauchgastemperatur` (Pflicht). Nicht erlaubt: `< > : " / \ \| ? *` |
| Format | standard, zweifeldrig oder breit (Auswahlliste) |
| x-Spalte | Spaltenüberschrift der x-Werte im Blatt „Daten“ (Pflicht) |
| x-Achsentitel, y-Achsentitel | Achsentitel (siehe unten); bei zweifeldrig zusätzlich „y-Achsentitel Feld 2“ |
| x min / x max / x Schritt | Achsgrenzen und Abstand der Teilstriche; leer = automatisch (Datenbereich ohne Rand). min muss kleiner als max sein; höchstens 50 Teilstriche. |
| y min / y max / y Schritt | ebenso, für Feld 2 mit dem Zusatz „Feld 2“ |
| Nachkommastellen x / y | feste Zahl von Nachkommastellen an den Teilstrichen; leer = automatisch |
| Legende | ja oder nein (auch 0 bzw. FALSCH). Die Legende erscheint nur bei mindestens zwei verschiedenen Legendentexten (Stilregel: bei nur einer Reihe keine Legende). |

## Achsentitel und Legendentexte

Sie werden mit LaTeX gesetzt, genau wie im Leitfaden:

| Eingabe in Excel | Ergebnis |
|---|---|
| `Zeit $t$ in \si{\minute}` | Zeit *t* in min |
| `Wärmefreisetzungsrate $\dot{Q}$ in \si{\kilo\watt}` | Wärmefreisetzungsrate *Q̇* in kW |
| `$Y_\mathrm{CO}$ in Vol.-%` | *Y*<sub>CO</sub> in Vol.-% (Index aufrecht) |
| `$Y_{CO}$` | *Y*<sub>*CO*</sub> (Index kursiv – nur für Formelzeichen als Index) |
| `Gastemperatur $T$ in °C` | Gastemperatur *T* in °C |
| `\ce{CO2}-Konzentration` | CO₂-Konzentration |
| `Wärmestromdichte $\dot{q}''$ in \si{\kilo\watt\per\square\metre}` (oder `kW/m²`) | Wärmestromdichte *q̇''* in kW/m² |

- Formelzeichen stehen zwischen `$ … $` – immer paarweise. Auch geschweifte Klammern `{ }` müssen paarweise stehen; beides wird vorab geprüft.
- Beschreibende Indizes (max, CO, eff) aufrecht mit `\mathrm{…}`.
- Die Zeichen `% & # _` dürfen direkt geschrieben werden.
- Die Zeichen `~ \ { }` haben in LaTeX eine Bedeutung; außerhalb von `$ … $` nur bewusst verwenden. Hochzahlen: `m²` direkt, `m$^2$` oder `\si{\square\metre}` – ein `^` außerhalb von `$ … $` (`m^2`) meldet der Befehl.
- **Keine Sonderzeichen aus Word kopieren** (Q̇, ṁ, CO₂): Sie fehlen in der Schrift oder verlieren den Punkt. Der Befehl warnt dann („Zeichen … fehlt in der Schrift“). Stattdessen `$\dot{Q}$`, `$\dot{m}$`, `\ce{CO2}` schreiben.
- Formelbefehle wie `\alpha`, `\dot{Q}` oder `\mathrm{max}` außerhalb von `$ … $` meldet der Befehl als Fehler mit Zelle und Korrekturvorschlag (z. B. „bitte `$\dot{Q}$` schreiben“). Einheiten in `\si{…}` (auch `\si{\milli\bar}`) sind richtig so. Indizes gehören mit in die Formel: `$\dot{Q}_\mathrm{max}$`, nicht `$\dot{Q}$_max`.

Sehr große oder sehr kleine Zahlen an den Achsen (ab 1 000 000 bzw. unter 0,0001) erscheinen als *a*·10ⁿ – dann einheitlich für alle Teilstriche dieser Achse. Besser ist meist eine passende Einheit (MW statt W).

Mehrere Dateien auf einmal: `vfdb-abbildung *.xlsx`.

## Fehlermeldungen

Fehler werden mit Blatt und Zeile bzw. Zelle gemeldet, z. B.:

```
FEHLER in 05-rauchgastemperatur.xlsx: Spalte 'Q mittel' fehlt im Blatt Daten (vorhanden: t in min, Q langsam)
FEHLER in 05-rauchgastemperatur.xlsx: Blatt Diagramm, y-Achsentitel (B6): LaTeX kann den Text nicht setzen (Extra }, or forgotten $.). Bitte $ … $ paarweise setzen und \si{…}, \dot{…} usw. prüfen.
FEHLER in 05-rauchgastemperatur.xlsx: Datei kann nicht geschrieben werden - ist das PDF (oder die Excel-Datei) noch in einem Programm geöffnet?
```

Bei mehreren Dateien (`vfdb-abbildung a.xlsx b.xlsx`) macht der Befehl nach einem Fehler mit der nächsten Datei weiter.
