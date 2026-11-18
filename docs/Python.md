# Abbildungen mit Python (Stufe A)

Das Paket `vfdb_stil` setzt die [Stilvorgaben](Stilvorgaben.md) für matplotlib um. Schrift und Formelsatz kommen von LuaLaTeX und entsprechen damit dem Leitfaden.

Voraussetzung: [Installation](Installation.md) von Python, MiKTeX (oder TeX Live) und vfdb-stil.

## Beispiel

```python
import numpy as np
import vfdb_stil as vs

t = np.linspace(0, 120, 600)
fig, ax = vs.figur("standard", legende=2)
ax.plot(t, 20 + 345 * np.log10(8 * t + 1), label="ETK", **vs.reihe(0))
ax.plot(t, 20 + 660 * (1 - 0.687 * np.exp(-0.32 * t) - 0.313 * np.exp(-3.8 * t)),
        label="Außenbrandkurve", **vs.reihe(1))
ax.set_xlim(0, 120)
ax.set_ylim(0, 1200)
ax.set_xlabel(r"Zeit $t$ in \si{\minute}")
ax.set_ylabel(r"Gastemperatur $T$ in \si{\degreeCelsius}")
vs.deutsch(ax)
vs.legende_unten(ax)
vs.speichern(fig, "media/04-temperaturzeitkurven.pdf")
```

`speichern` gibt die Maße der Abbildung aus und warnt, wenn Texte sich überlappen oder über den Rand ragen. Weitere Beispiele: [`beispiele/python/`](../beispiele/python/) (auch zweifeldrig und ein Schema), die erzeugten PDFs unter [`beispiele/pdf/`](../beispiele/pdf/).

**Wichtig:** `import vfdb_stil` stellt matplotlib auf das pgf-Backend (LuaLaTeX) um und setzt den Leitfaden-Stil. Eine Bildschirmvorschau mit `plt.show()` ist danach nicht möglich – das gespeicherte PDF ansehen. In Jupyter das Paket daher in einem eigenen Notebook für die Abbildungen verwenden.

## Die wichtigsten Funktionen

| Funktion | Zweck |
|---|---|
| `figur(format, legende=n)` | Abbildung im Format `"standard"`, `"zweifeldrig"` oder `"breit"`. `legende` = Zahl der Legendeneinträge; der untere Rand wird danach bemessen. Ränder in mm mit `unten=`, `oben=` (z. B. Schema mit Phasenbalken: `unten=14`). Weitere Argumente gehen an `plt.subplots` (z. B. `sharex=True`, `ncols=2`; nebeneinanderliegende Felder bekommen dann den linken Rand als Abstand). |
| `reihe(i)` | Farbe und Linienstil der Reihe *i* (ab 0) in fester Reihenfolge: `ax.plot(..., **vs.reihe(i))`. Nur Punkte: `ax.plot(x, y, marker="o", ls="none", color=vs.farbe(i))` (Punkte auf dem Achsenrand werden ganz gezeichnet) |
| `farbe(i)`, `linienstil(i)`, `farbwert("grau")` | einzeln |
| `deutsch(ax, x_nachkomma, y_nachkomma)` | Tick-Beschriftung mit Dezimalkomma und echtem Minus; Rundungsreste (z. B. 1e-16) werden zu 0; liegt ein Teilstrich ab 10⁶ bzw. unter 10⁻⁴, erscheint die ganze Achse als *a*·10ⁿ. **Nach dem Zeichnen der Daten** aufrufen; für eine Farbskala `vs.deutsch(cb.ax)` mit `cb = fig.colorbar(…)` (die Farbskala verkleinert die Achsenfläche – die Maße in der Ausgabe von `speichern` prüfen; für Karten Format `"breit"`). Reine Zahlenformate (`"%.2f"`, `"{x:,.0f}"`) werden umgestellt; eigene Formate mit Einheit oder Prozent (`"{x:.0f} %"`) bleiben unverändert – Komma dort selbst setzen, z. B. mit `vs.zahl`; zeigen sie auf einer linearen Achse einen Dezimalpunkt, warnt `speichern` |
| `legende_unten(ax)` | Legende unter der Abbildung, zeilenweise, mit den Einträgen aller Felder derselben Spalte (gleicher Text nur einmal; nebeneinanderliegende Felder: je Feld aufrufen); legt bei zu langen Einträgen Spalten zusammen und passt den unteren Rand an. Am **untersten** Feld aufrufen, bei zweifeldrig also `fig, (ax1, ax2) = vs.figur("zweifeldrig", legende=2, sharex=True)` … `vs.legende_unten(ax2)`. |
| `pfeilachsen(ax, x_max, y_max, ylabel)` | Achsen als Pfeile für Schemata |
| `hinweis(ax, text, xy, xytext)` | Beschriftung mit Hinweispfeil (waagerecht oder senkrecht führen) |
| `phasenbalken(ax, x0, x1, text)` | Maßpfeil für eine Phase unter der Zeitachse; braucht `figur(..., unten=14)` (bei zweizeiligem Text mehr – `speichern` nennt dann den nötigen Rand) |
| `speichern(fig, pfad)` | Vektor-PDF in fester Größe, mit Maßangaben und Prüfung (Überlappungen, Rand, Zeichen, die in der Schrift fehlen, Dezimalpunkt statt `deutsch`, reservierter Legendenplatz ohne Legende) |
| `HILFSLINIE`, `LINIE_DUENN`, `GRAU_FLAECHE`, `TEXT`, `FARBEN` … | Stilkonstanten, z. B. `ax.plot(..., **vs.HILFSLINIE)` |

Texte werden mit LaTeX gesetzt: Formelzeichen zwischen `$ … $` (auch `\alpha`, `\dot{Q}`, `Y_\mathrm{CO}`, mit Index: `$\dot{Q}_\mathrm{max}$`), Einheiten mit `\si{…}`, Stoffe mit `\ce{…}`; `&`, `#` und `_` außerhalb von Formeln als `\&`, `\#`, `\_` schreiben. **Texte mit `\` immer als `r"…"` schreiben** – sonst macht Python aus `"$\theta$"` einen Tabulator und „heta“. Hochzahlen als `m$^2$`, `m²` oder `\si{\square\metre}`. Steht ein Formelbefehl oder `^` außerhalb von `$ … $`, ein Index direkt hinter `$ … $` oder fehlt das `r`, brechen `speichern` und `legende_unten` mit einer Meldung samt Korrekturvorschlag ab (z. B. „bitte `$\dot{Q}$` schreiben“). Achsentitel, die länger als ihre Achse sind (häufig bei zweifeldrig), meldet `speichern` als Warnung – dann genügen Formelzeichen und Einheit. Sonderzeichen wie Q̇, ṁ oder CO₂ nicht aus Word kopieren (sie fehlen in der Schrift oder verlieren den Punkt); `speichern` warnt dann.

`deutsch()` gilt für lineare Achsen; logarithmische Achsen (nach `ax.set_yscale("log")`) behalten die Beschriftung 10ⁿ.

## Regeln, die das Paket nicht erzwingen kann

- Farben nur über `reihe(i)` bzw. `farbe(i)` vergeben, nie eigene Farben; höchstens 8 Reihen.
- Keine zweite y-Achse (`twinx`); stattdessen Format `"zweifeldrig"`.
- Hinweispfeile waagerecht oder senkrecht.
- Kein Gesamttitel in der Abbildung; bei nur einer Reihe keine Legende.
- Achsgrenzen setzen (`ax.set_xlim`, `ax.set_ylim`); ohne Angabe reicht die Achse genau bis zu den Daten.
- `vs.deutsch(ax)` nach dem Zeichnen für jedes Feld mit Zahlenachsen aufrufen (Dezimalkomma; Kategorien-, Datums- und eigene Beschriftungen bleiben unverändert). Zeigen die Teilstriche ohne `deutsch` einen Dezimalpunkt oder „1e6“ oder wurde `deutsch` vor dem Zeichnen von Kategorien bzw. Datumswerten aufgerufen, warnt `speichern`.
- Legende: Einträge in der Reihenfolge des Zeichnens; eine andere Reihenfolge mit `vs.legende_unten(ax, handles, labels)`.

## Farbpalette prüfen

```
vfdb-farbpruefung
```

prüft die Palette aus `stil.yaml` rechnerisch auf Unterscheidbarkeit benachbarter Reihen, auch bei Farbsehschwäche; `--alle-paare` vergleicht jede Farbe mit jeder (für Streudiagramme). Mit eigenen Farben: `vfdb-farbpruefung "#2a78d6,#eb6834,#1baf7a"`.
