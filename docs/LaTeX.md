# Schemata und Diagramme mit LaTeX (Stufe A)

Das Paket `vfdbstil` setzt die [Stilvorgaben](Stilvorgaben.md) für TikZ-Schemata und PGFPlots-Diagramme um. Größe, Schrift, Linien, Pfeile und Legende entsprechen den Python-Abbildungen. Gemessene Abweichung zur Python-Ausgabe derselben Abbildung (`beispiele/pdf/*_tikz.pdf` und `*_pgfplots.pdf` sowie Legenden mit 1 bis 3 Spalten): Abbildungsgröße, Achsen und Achsentitel ≤ 0,1 mm, Legende mit Linien (auch mit Markern) ≤ 0,3 mm, Pfeilspitzen ≤ 0,3 mm, Beschriftungen an Schema-Achsen und mehrzeilige Texte ≤ 0,6 mm.

Jede Abbildung ist ein eigenes kleines Dokument (`standalone`). Daraus entsteht ein PDF in fester Größe, das wie jede andere Abbildung nach `media/` kommt. Das Gesamtwerk braucht das Paket nicht.

## Benötigte Dateien

Aus dem Ordner [`latex/`](../latex/):

- `vfdbstil.sty` – das Paket
- `vfdbstil-werte.tex` – die Stilwerte, aus `stil/stil.yaml` erzeugt (nicht von Hand ändern)
- `vorlage_schema.tex` oder `vorlage_diagramm.tex` als Ausgangspunkt

Übersetzt wird mit **LuaLaTeX** (LaTeX-Stand ab Juni 2022, z. B. TeX Live 2022 oder neuer). Das Paket setzt `\pgfplotsset{compat=1.18}` und lädt `siunitx` und `mhchem` (Version 4; wer `mhchem` selbst lädt, gibt `[version=4]` an).

## In Overleaf

1. Ein eigenes Overleaf-Projekt für die Abbildungen des Kapitels anlegen, z. B. „Abbildungen Kap. 5“.
2. `vfdbstil.sty`, `vfdbstil-werte.tex` und die Vorlage hochladen – **in die oberste Ebene** des Projekts, nicht in einen Unterordner.
3. Menü → Compiler: **LuaLaTeX**.
4. Für jede Abbildung eine eigene `.tex`-Datei; welche übersetzt wird, legt Menü → *Main document* fest.
5. Das PDF herunterladen, in den Abbildungsnamen umbenennen (z. B. `05-rauchgastemperatur.pdf`) und im Leitfaden-Projekt nach `media/` hochladen; einbinden ohne Skalierung: `\includegraphics{media/05-rauchgastemperatur.pdf}`.

## Lokal

Die beiden Paketdateien neben die Abbildung legen und `lualatex abbildung.tex` ausführen. Mit dem Repository geht es auch so:

```
python latex/bauen.py meine_abbildung.tex --ziel media
python latex/bauen.py "abbildungen/*.tex" --ziel media
```

`bauen.py` übersetzt in einem temporären Ordner und nimmt dorthin die Paketdateien und den Inhalt des Ordners der `.tex`-Datei mit, einschließlich Unterordnern (z. B. CSV-Daten, eingebundene PDF-Bilder; bis 200 MB). Fehler werden mit Zeilennummer gemeldet, Warnungen aus dem LaTeX-Protokoll vollständig ausgegeben (z. B. fehlende Zeichen oder Schriften).

## Schemata (TikZ)

```latex
\documentclass[border=0pt]{standalone}
\usepackage[ngerman]{babel}
\usepackage[schriften]{vfdbstil}
\begin{document}
\begin{vfdbschema}[standard]{14}{3}      % Format, unterer und oberer Rand in mm
  \draw[vfdb kurve=1] (0,0) -- (40,40) -- (90,0);
  \vfdbPfeilachsen{Wärmefreisetzungsrate $\dot{Q}$}
  \vfdbPhase{0}{40}{Brandausbreitung}
\end{vfdbschema}
\end{document}
```

Koordinaten sind Millimeter, der Ursprung liegt im Schnittpunkt der Achsen. Die Achsenfläche ist `\vfdbB` × `\vfdbH` groß (Standard 103 × 64 mm). Inhalt außerhalb des festen Rahmens wird abgeschnitten – das PDF ansehen.

| Befehl / Stil | Zweck |
|---|---|
| `vfdbschema[format]{unten}{oben}` | Umgebung mit fester Abbildungsgröße |
| `\vfdbPfeilachsen[x-Text]{y-Text}` | Achsen als Pfeile; x-Text Standard „Zeit *t*“ |
| `\vfdbXmarke{x}{Text}`, `\vfdbYmarke{y}{Text}` | Beschriftung an den Achsen (8 pt) |
| `\vfdbPhase{x0}{x1}{Text}` | Maßpfeil einer Phase unter der Zeitachse |
| `vfdb kurve=i` | Kurve in Farbe *i* (1,4 pt) |
| `vfdb reihe=i` | Kurve in Farbe *i* mit dem Linienstil der Reihe *i* (1 bis 8) |
| `vfdb duenn=i` | dünne Kurve (1,0 pt) |
| `vfdb hilfslinie` | graue, gestrichelte Hilfslinie |
| `vfdb flaeche`, `vfdb flaeche farbig=i` | graue bzw. farbige, durchscheinende Fläche |
| `vfdb hinweis`, `vfdb mass`, `vfdb achse` | Hinweispfeil, Maßpfeil, Achsenpfeil |
| `vfdb klein` | Schrift 8 pt |
| `\vfdbZahl{-1.5}` | Zahl im Leitfaden-Format: −1,5 (auf 10 gültige Stellen; ab 10⁶ bzw. unter 10⁻⁴ als *a*·10ⁿ) |
| `vfdbFarbe1` … `vfdbFarbe8`, `vfdbGrau`, `vfdbGrauFlaeche` | Farben |

Hinweispfeile waagerecht oder senkrecht führen, z. B. `\draw[vfdb hinweis] (text.west) -- (32, 20);`.

## Diagramme (PGFPlots)

```latex
\begin{tikzpicture}
  \vfdbRahmen[standard]{\vfdbRandEintraege{2}}{3}    % feste Größe, Platz für 2 Legendeneinträge
  \begin{axis}[vfdb=standard, xmin=0, xmax=10, ymin=0, ymax=100,
      xlabel={Zeit $t$ in \si{\minute}}, ylabel={Temperatur $T$ in \si{\degreeCelsius}},
      vfdb legende=2]                                % 2 Einträge -> Spalten nach Stilregel
    \addplot table[x=t, y=A, col sep=semicolon] {daten.csv};
    \addlegendentry{Messung A}
    \addplot table[x=t, y=B, col sep=semicolon] {daten.csv};
    \addlegendentry{Messung B}
  \end{axis}
\end{tikzpicture}
```

- `vfdb=standard` bzw. `vfdb=breit` setzt Achsenfläche, Achsen, Gitter, Schriften (Direktbeschriftungen 9 pt), Zahlenformat (Dezimalkomma, keine Skalierung mit „·10ⁿ“ unter der Achse) und die Reihenfolge von Farben und Linienstilen. Kurven werden an der Achsenfläche abgeschnitten.
- **Abbildungsgröße:** Die Abbildung hat eine feste Größe; was außerhalb liegt (eine Legendenzeile zu viel, eine überstehende Tick-Beschriftung), wird **ohne Warnung abgeschnitten** – das PDF ansehen.
- **Unterer Rand** für `\vfdbRahmen`: ohne Legende 10; mit Legende `\vfdbRandEintraege{<Zahl der Einträge>}` (passend zu `vfdb legende`) oder `\vfdbRandLegende{<Zahl der Zeilen>}`.
- **Legende:** zeilenweise gefüllt. `vfdb legende=<Zahl der Einträge>` wählt die Spalten nach der Stilregel (bis 3 in einer Zeile, 4 in 2 Spalten, sonst 3). Ist die Legende zu breit, `legend columns` von Hand verringern und den Rand anpassen.
- **Nachkommastellen:** Tick-Zahlen werden auf 7 gültige Stellen gerundet; feste Nachkommastellen (ab 5 aufgerundet) mit `vfdb nachkomma x=2`, `vfdb nachkomma y=2` oder `vfdb nachkomma=2` (beide Achsen) in den Achsenoptionen.
- **Große und kleine Zahlen:** Die ganze Achse wird als *a*·10ⁿ beschriftet, wenn ein Teilstrich ab 10⁶ liegt oder einer (außer 0) unter 10⁻⁴ – wie bei Python. Grundlage sind die Teilstriche aus `xtick distance` (auch als Ausdruck, z. B. `5*60`) oder, ohne diese Angabe, die von PGFPlots selbst gewählten. Mit einer Liste `xtick={…}` kann die Wahl abweichen.
- **Kontrolle der Größe:** `bauen.py` warnt, wenn die Abbildung keine Formatbreite hat (z. B. weil `\vfdbRahmen` fehlt).
- **Marker:** `\addplot+[mark=o] …` (leer) bzw. `\addplot+[only marks, mark=*] …` (gefüllt in der Farbe der Reihe); Größe nach Stilvorgaben, auch in der Legende. Eigene `mark options` ersetzen die Voreinstellung – dann `solid` mit angeben, z. B. `mark options={solid, scale=1.2}` oder `mark options={solid, fill=white}`, sonst übernimmt der Markerumriss das Strichmuster der Reihe. Eine eigene Farbe (`\addplot+[vfdbGrau, mark=*]`) gilt für Linie und Marker.
- **Fehlerbalken** (`error bars/.cd, y dir=both, …`): durchgezogen in Farbe und Linienstärke der Reihe, ohne Endstriche – wie in Python.
- **Bestimmte Farbe statt der Reihenfolge:** `\addplot+[vfdb reihe=3] …` (Farbe, Linienstil und Markerfüllung der Reihe 3). Die übrigen `\addplot` behalten die Farbe ihrer Position – dann allen Reihen `vfdb reihe=…` geben, jede Nummer nur einmal.
- **Logarithmische Achsen:** `ymode=log`; Beschriftung als 10ⁿ.
- **Mehr als 8 Reihen** sind nicht vorgesehen; die 9. Reihe erhielte wieder Farbe 1.
- **Sonderzeichen in Texten:** `_ & # %` als `\_ \& \# \%` schreiben (z. B. FDS-Namen `TC\_01`). Ein Fehler in einem Legendentext („Missing $ inserted“) wird an der Zeile von `\end{axis}` gemeldet.
- **Keine Sonderzeichen aus Word kopieren** (Q̇, ṁ, CO₂): Sie fehlen in der Schrift oder verlieren den Punkt. Stattdessen `$\dot{Q}$`, `$\dot{m}$`, `\ce{CO2}`. `bauen.py` warnt bei fehlenden Zeichen und bei Punkten aus Word.
- **Daten aus Excel:** als CSV speichern, **mit Dezimalpunkt** (deutsches Excel schreibt Dezimalkommas – dann meldet LaTeX einen Fehler „Could not parse input“). Für Excel-Daten ist meist der [Excel-Weg](Excel.md) einfacher.
- Format **zweifeldrig** ist in PGFPlots noch nicht vorbereitet; dafür den Python- oder Excel-Weg nutzen.
- **Nicht vorbereitet sind außerdem** Balkendiagramme (`ybar`, `xbar`) und Flächen mit Legendeneintrag; in der Legende stehen reine Punkte (`only marks`) enger als in Python. Dafür den Python-Weg nutzen.
- **Fläche unter einer Kurve** (ohne Legendeneintrag): `\addplot[vfdb flaeche farbig=1, forget plot] coordinates {…} \closedcycle;` – `forget plot`, damit die Fläche keine Farbe der Reihenfolge und keinen Legendenplatz verbraucht. **Fläche zwischen zwei Kurven** mit `\usepgfplotslibrary{fillbetween}`, den Kurven `\addplot+[name path=a] …` bzw. `\addplot+[name path=b] …` (mit `+`, sonst fehlen Farbe und Linienstil der Reihe) und `\addplot[vfdb flaeche farbig=1, forget plot] fill between[of=a and b];` – dann `\vfdbRahmen` erst nach `\end{axis}` setzen, mit `\pgfresetboundingbox` davor (vor der Achse bricht PGFPlots mit „Dimension too large“ ab).

## Fehlermeldungen

Tippfehler werden mit verständlicher Meldung abgefangen, z. B. `Package vfdbstil Error: Unbekanntes Format 'Standard' (erlaubt: standard, zweifeldrig, breit)` oder `Reihe '9' gibt es nicht (1 bis 8)`. Die Option `schriften` verlangt LuaLaTeX (oder XeLaTeX).
