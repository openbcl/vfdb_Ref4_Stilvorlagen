# vfdb_Ref4_Stilvorlagen

Stilvorlagen und Werkzeuge, mit denen die Arbeitsteams des Referats 4 der vfdb (Vereinigung zur Förderung des Deutschen Brandschutzes e. V.) Abbildungen für den **Leitfaden Ingenieurmethoden des Brandschutzes** in einheitlichem Stil erstellen: Diagramme, Schemata und Prinzipskizzen, wahlweise mit Excel, PowerPoint, Python oder LaTeX.

> **Status: Entwurf, Version 0.1.0.** Die Stilvorgaben sind aus den Abbildungen von Kapitel 4 abgeleitet und noch nicht von der Redaktion werkweit beschlossen. Rückmeldungen sind ausdrücklich erwünscht (siehe [Mitwirken](#mitwirken)).

## Grundsätze

1. **Nach Overleaf kommt nur ein fertiges PDF.** Jede Abbildung wird als `media/XX-name.pdf` (XX = Kapitelnummer) ins Gesamtwerk gelegt und ohne Skalierung eingebunden: `\includegraphics{media/XX-name.pdf}`.
2. **Eine Quelle für alle Stilwerte:** [`stil/stil.yaml`](stil/stil.yaml). Python-Paket, LaTeX-Paket und Office-Vorlagen werden daraus erzeugt.
3. **Feste Formate** (standard, zweifeldrig, breit) mit fester Achsenfläche.
4. **Zwei Genauigkeitsstufen:**
   - **A, exakt:** Python, Excel als Datenquelle, LaTeX. Schrift (TeX Gyre Heros), Formelsatz und Maße wie im Leitfaden.
   - **B, angenähert:** Excel und PowerPoint mit Vorlagen. Farben, Linienstärken, Größe und Achsenfläche (etwa ±0,2 mm) stimmen; Schrift Arial statt TeX Gyre Heros (gleiche Zeichenbreiten), Strichmuster ähnlich, Formelzeichen von Hand.

Die Vorgaben im Einzelnen: [Stilvorgaben](docs/Stilvorgaben.md).

## Welcher Weg passt?

| Ich möchte … | Weg | Stufe | Was muss installiert sein? |
|---|---|---|---|
| ein Diagramm direkt in Excel gestalten | Excel-Arbeitsmappe mit fertigem Diagramm, Export über PowerPoint → [Anleitung](docs/Office.md) | B | nur Office |
| ein Schema in PowerPoint zeichnen | PowerPoint-Vorlage je Format → [Anleitung](docs/Office.md) | B | nur Office |
| Daten in Excel pflegen, Abbildung exakt im Leitfaden-Stil | Excel-Vorlage + Befehl `vfdb-abbildung` → [Anleitung](docs/Excel.md) | A | Python, MiKTeX, vfdb-stil ([Installation](docs/Installation.md)) |
| ein Diagramm mit Python erstellen | Python-Paket `vfdb_stil` → [Anleitung](docs/Python.md) | A | Python, MiKTeX, vfdb-stil ([Installation](docs/Installation.md)) |
| ein Schema oder Diagramm in LaTeX setzen | TikZ/PGFPlots-Paket `vfdbstil.sty` → [Anleitung](docs/LaTeX.md) | A | nichts (Overleaf) oder LaTeX lokal |

Beispiele für Python, Excel (Stufe A) und LaTeX mit den erzeugten PDFs: [`beispiele/`](beispiele/); ein Office-Beispiel steckt in den Arbeitsmappen `office/vfdb_Diagramm_*.xlsx`.

## Aufbau

```
stil/        stil.yaml – alle Stilwerte (einzige Quelle)
docs/        Stilvorgaben, Installation und Anleitungen
python/      Python-Paket vfdb_stil (matplotlib, LuaLaTeX)
excel/       Excel-Vorlage „Daten + Diagrammangaben“, Startdatei für Windows
latex/       TikZ/PGFPlots-Paket vfdbstil.sty, Vorlagen, Bauskript
office/      Office-Design, Excel-Arbeitsmappen, Diagrammvorlage, PowerPoint-Vorlagen
beispiele/   Beispiele (python/, excel/, latex/) und die erzeugten PDFs (pdf/)
tests/       automatische Prüfungen (pytest)
```

Geplant: eine fertige Arbeitsumgebung im Browser (GitHub Codespaces) und eine automatisch gebaute Beispielgalerie.

## Mitwirken

Fehler und Vorschläge bitte als [Issue](https://github.com/openbcl/vfdb_Ref4_Stilvorlagen/issues) melden. Wie Stilwerte geändert und die Vorlagen neu erzeugt werden, steht in [CONTRIBUTING.md](CONTRIBUTING.md); Änderungen in [CHANGELOG.md](CHANGELOG.md).

## Lizenz

© 2026 vfdb Referat 4

| Bereich | Lizenz |
|---|---|
| Code und Textdateien zum Programm: `python/`, `stil/`, `latex/` (Paket, Werte, Vorlagen, Skripte), `excel/*.py`, `excel/*.bat`, `office/*.py`, `tests/`, `beispiele/python/`, `beispiele/latex/`, `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, Konfigurationsdateien | MIT, siehe [`LICENSE`](LICENSE) |
| Dokumentation, Office- und Excel-Vorlagen, Beispielabbildungen: `docs/`, `excel/*.xlsx`, `office/*` (außer `*.py`), `beispiele/excel/`, `beispiele/pdf/` | CC BY 4.0, siehe [`LICENSE-CC-BY-4.0.txt`](LICENSE-CC-BY-4.0.txt) |

**Abbildungen, die mit diesen Vorlagen und Werkzeugen erstellt werden, unterliegen keinen Pflichten aus diesem Repository** (keine Namensnennung, kein Lizenzhinweis). Wer die Vorlagen selbst weitergibt oder verändert veröffentlicht, nennt die Quelle, z. B. „Stilvorlagen: vfdb Referat 4, CC BY 4.0, https://github.com/openbcl/vfdb_Ref4_Stilvorlagen“.

**Schriften** werden nicht mitgeliefert. Benötigt werden TeX Gyre Heros (GUST Font License) und Fira Math (SIL Open Font License 1.1), beide in MiKTeX und TeX Live enthalten; im Office-Weg Arial (Windows-Systemschrift). Die Beispiel-PDFs enthalten eingebettete Teilmengen dieser Schriften.

Daten aus urheberrechtlich geschützten Quellen (z. B. Tabellenwerke von Handbüchern) werden nicht in dieses Repository aufgenommen. Die Beispiele verwenden nur Formeln aus Normen, gebräuchliche Kennwerte (α-Werte der t²-Brandentwicklung) und selbst berechnete Werte.
