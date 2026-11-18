# Mitwirken

## Fehler und Vorschläge

Bitte als [Issue](https://github.com/openbcl/vfdb_Ref4_Stilvorlagen/issues) melden – mit der Excel-, Python- oder LaTeX-Datei, die das Problem zeigt, und der vollständigen Fehlermeldung. Stilfragen (Farben, Maße, Regeln) entscheidet das Referat 4 bzw. die Redaktion des Leitfadens.

## Entwicklungsumgebung

```
git clone https://github.com/openbcl/vfdb_Ref4_Stilvorlagen
cd vfdb_Ref4_Stilvorlagen
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[test]"
.venv\Scripts\python -m pytest
.venv\Scripts\activate
```

Alle folgenden Befehle in dieser aktivierten Umgebung ausführen – sonst nehmen `python` und `vfdb-abbildung` womöglich eine andere Installation mit alten Stilwerten.

Die Tests mit Abbildungen brauchen LuaLaTeX und die Schriften TeX Gyre Heros und Fira Math; ohne LuaLaTeX werden sie übersprungen.

## Stilwerte ändern

`stil/stil.yaml` ist die einzige Quelle aller Stilwerte. Nach einer Änderung:

1. `python latex/erzeuge_werte.py` – LaTeX-Werte neu erzeugen
2. `python excel/erzeuge_vorlagen.py` – Excel-Vorlage und Excel-Beispiel neu erzeugen
3. Beispiele neu erzeugen:
   ```
   for %f in (beispiele\python\*.py) do python %f
   vfdb-abbildung beispiele\excel\t2_brandentwicklung.xlsx --ziel beispiele\pdf
   python latex/bauen.py "beispiele/latex/*.tex" --ziel beispiele/pdf
   ```
4. Unter Windows mit Office (geschlossen): `pip install -e ".[office]"`, dann `python office/erzeuge_office.py`
5. Zahlen in der Dokumentation nachziehen, die sich aus den Stilwerten ergeben: `README.md`, alle `docs/*.md`, `latex/vorlage_*.tex` und `beispiele/` nach dem alten Wert durchsuchen – ohne Groß-/Kleinschreibung (Hexfarben) und in allen Schreibweisen (10⁶, 1 000 000, 1e6). Typische Stellen: Tabellen in `docs/Stilvorgaben.md`, Folien- und Legendenmaße, Farben und Reihenzahl in `docs/Office.md`, Ränder, Linienbreiten, Schriftgrößen und Grenzen in `docs/LaTeX.md`, Grenzen und Reihenzahl in `docs/Excel.md` und `docs/Python.md`, der untere Rand 14 mm für Schemata mit Phasenbalken (bei Änderungen unter `schema`).
6. `python -m pytest`
7. Versionsnummer gleich erhöhen in `stil/stil.yaml`, `pyproject.toml`, `latex/vfdbstil.sty`, `README.md` und `docs/Stilvorgaben.md` (ein Test prüft das) und die Änderung in `CHANGELOG.md` eintragen.

## Lizenz von Beiträgen

Beiträge stehen unter der Lizenz des Bereichs, zu dem sie gehören – maßgeblich ist die Tabelle im Abschnitt „Lizenz“ der [README](README.md). Keine Daten aus urheberrechtlich geschützten Quellen aufnehmen.
