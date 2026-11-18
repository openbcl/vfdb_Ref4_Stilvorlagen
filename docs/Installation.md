# Installation (Windows)

Diese Anleitung gilt für den **Python-Weg** und den **Excel-Weg der Stufe A** (Befehl `vfdb-abbildung`). Für den Office-Weg (Stufe B) und für LaTeX in Overleaf ist nichts zu installieren.

Benötigt werden drei Dinge:

1. **Python** (ab 3.11)
2. **LaTeX mit LuaLaTeX** und den Schriften TeX Gyre Heros und Fira Math, z. B. MiKTeX
3. das Paket **vfdb-stil** aus diesem Repository

Zeitbedarf: etwa 20 Minuten, davon das meiste Download.

## 1. Python

1. Auf [python.org/downloads/windows](https://www.python.org/downloads/windows/) bei einer aktuellen Version das klassische Installationsprogramm **„Windows installer (64-bit)“** laden und starten.
2. Im ersten Fenster **„Add python.exe to PATH“** ankreuzen, dann „Install Now“. (Wer stattdessen den neueren „Python install manager“ nutzt: Wird `vfdb-abbildung` später nicht gefunden, hilft `python -m vfdb_stil.excel`, siehe unten.)
3. Prüfen: Eingabeaufforderung öffnen (Windows-Taste, `cmd` tippen, Enter) und eingeben:
   ```
   python --version
   ```
   Es erscheint z. B. `Python 3.12.…`.

## 2. MiKTeX (LaTeX)

1. Installationsprogramm von [miktex.org/download](https://miktex.org/download) laden und starten; Installation „nur für mich“ genügt.
2. **MiKTeX Console** öffnen → *Settings* (Einstellungen) → bei der Frage, ob fehlende Pakete installiert werden sollen, **„Always“** (immer) wählen. Sonst kann der erste Lauf mit einer unsichtbaren Rückfrage hängen bleiben.
3. Die benötigten Pakete (u. a. `tex-gyre`, `firamath`, `siunitx`, `pgfplots`) lädt MiKTeX beim ersten Lauf selbst nach. Der erste Lauf dauert deshalb länger.
4. **Danach eine neue Eingabeaufforderung öffnen** – eine schon offene kennt MiKTeX noch nicht.

Wer schon **TeX Live** nutzt, braucht MiKTeX nicht; TeX Live enthält alles Nötige.

Findet LuaLaTeX eine Schrift nicht, hilft meist das Aktualisieren der Schriftdatenbank:
```
luaotfload-tool --update
```

## 3. Paket vfdb-stil

In der Eingabeaufforderung:

```
python -m pip install https://github.com/openbcl/vfdb_Ref4_Stilvorlagen/archive/refs/heads/main.zip
```

Wer Git installiert hat, kann stattdessen schreiben:
`python -m pip install "vfdb-stil @ git+https://github.com/openbcl/vfdb_Ref4_Stilvorlagen"`

Aus einem heruntergeladenen und entpackten Ordner des Repositorys: im Ordner `python -m pip install .`

## 4. Ausprobieren

```
cd %USERPROFILE%\Documents
vfdb-abbildung --vorlage test.xlsx
vfdb-abbildung test.xlsx
```

Der erste Befehl legt eine Excel-Vorlage mit einem kleinen Beispiel an, der zweite erzeugt daraus `test.pdf` im selben Ordner (Dauer etwa 20 Sekunden, beim allerersten Mal länger).

## Hinweise

- **Eingabeaufforderung im richtigen Ordner:** Im Explorer den Ordner öffnen, in die Adresszeile `cmd` tippen und Enter drücken. Bei Ordnern auf einem Netzwerkpfad (`\\server\…`) geht das nicht – die Eingabeaufforderung meldet „UNC-Pfade werden nicht unterstützt“ und startet in `C:\Windows`. Dann die `.bat`-Datei (nächster Punkt) benutzen oder die Freigabe als Netzlaufwerk mit Buchstaben verbinden.
- **Ohne Eingabeaufforderung:** [`excel/Abbildung_erzeugen.bat`](../excel/Abbildung_erzeugen.bat) in den Ordner der Excel-Dateien kopieren und eine Excel-Datei mit der Maus darauf ziehen.
- **„Befehl nicht gefunden“:** Statt `vfdb-abbildung` geht immer `python -m vfdb_stil.excel`, z. B. `python -m vfdb_stil.excel test.xlsx`.
- **Aktualisieren:** `python -m pip install --force-reinstall https://github.com/openbcl/vfdb_Ref4_Stilvorlagen/archive/refs/heads/main.zip` (mit `--force-reinstall` auch dann, wenn sich die Versionsnummer nicht geändert hat).
