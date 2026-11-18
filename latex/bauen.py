"""Uebersetzt standalone-Abbildungen (.tex) mit LuaLaTeX zu PDF.

    python latex/bauen.py beispiele/latex/*.tex --ziel beispiele/pdf
    python latex/bauen.py "C:\\Abbildungen\\05-*.tex"          (Platzhalter auch unter Windows)

Jede Datei wird in einem temporaeren Ordner uebersetzt, zusammen mit vfdbstil.sty,
vfdbstil-werte.tex und dem Inhalt des Ordners der .tex-Datei (mit Unterordnern, z. B. Daten
als CSV oder eingebundene PDF-Bilder; bis zu 200 MB, ohne Hilfsdateien). Nur das PDF wird
in den Zielordner kopiert (ohne --ziel: neben die .tex-Datei). Fehler werden mit
Zeilennummer, Warnungen aus dem LaTeX-Protokoll (fehlende Zeichen, Schriften, Ueberlaeufe)
vollstaendig ausgegeben.
"""
from __future__ import annotations

import argparse
import glob
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

LATEX = Path(__file__).resolve().parent
STILDATEIEN = ("vfdbstil.sty", "vfdbstil-werte.tex")
WARNMUSTER = re.compile(r"(Missing character|Overfull|Underfull|LaTeX (Font )?Warning|"
                        r"(Package|Class) \w+ Warning)")
HOECHSTENS_BYTES = 200_000_000
IGNORIEREN = shutil.ignore_patterns(".git", ".venv", "__pycache__", "*.aux", "*.log", "*.fls",
                                    "*.fdb_latexmk", "*.synctex.gz")


class BauFehler(RuntimeError):
    """Fehler beim Uebersetzen (Meldung fuer Anwender)."""


def _ordnergroesse(ordner: Path) -> int:
    return sum(p.stat().st_size for p in ordner.rglob("*") if p.is_file())


TEX_ZEILENLAENGE = 79                     # TeX bricht Protokollzeilen nach 79 Bytes um
# Datei- und Seitenmarken im Protokoll; Folgezeilen wie "(Font) ..." oder "<argument> \foo"
# gehoeren dagegen zur Meldung
_RAUSCHEN = re.compile(r"^\s*(\((\.|[A-Za-z]:|/)|\)|\[\d|\]|\*|<(\.|[A-Za-z]:|/|use )"
                       r"|LaTeX2e|L3 programming|Document Class)")


def _umgebrochen(zeile: str, naechste: str = "") -> bool:
    """Hat TeX die Zeile umgebrochen? Vor einem Mehrbyte-Zeichen (Umlaut) bricht LuaTeX schon
    bis zu 3 Bytes frueher um."""
    n = len(zeile.encode("utf-8"))
    return n >= TEX_ZEILENLAENGE or (n >= TEX_ZEILENLAENGE - 3 and naechste[:1] > "\x7f")


def _meldungen(zeilen: list[str], muster) -> list[str]:
    """Meldungen samt Folgezeilen bis zur Leerzeile bzw. bis einschliesslich der Zeilenangabe
    l.<n>; von TeX umbrochene Zeilen werden ohne Leerzeichen wieder zusammengefuegt."""
    meldungen, i = [], 0
    while i < len(zeilen):
        if muster(zeilen[i]):
            text = zeilen[i].rstrip("\n")
            def folge(k):
                return zeilen[k] if k < len(zeilen) else ""
            umbruch = _umgebrochen(zeilen[i], folge(i + 1))
            j, teile = i + 1, 1
            while j < len(zeilen) and zeilen[j].strip() and teile < 8:
                z = zeilen[j]
                if not umbruch and _RAUSCHEN.match(z):
                    break
                text += z if umbruch else " " + z.strip()
                umbruch = _umgebrochen(z, folge(j + 1))
                teile += 1
                if z.startswith("l."):
                    break
                j += 1
            meldungen.append(re.sub(r"\s+", " ", text).strip())
            i = j
        i += 1
    return meldungen


def _formatbreiten() -> list[float]:
    """Breiten der Formate aus stil/stil.yaml (mm)."""
    try:
        import yaml
        with (LATEX.parent / "stil" / "stil.yaml").open(encoding="utf-8") as f:
            return sorted({v["breite_mm"] for v in yaml.safe_load(f)["formate"].values()})
    except Exception:  # noqa: BLE001 - Pruefung ist optional
        return []


def _breite_pruefen(zeilen: list[str]) -> list[str]:
    for z in zeilen:
        m = re.match(r"vfdbstil-Seitenbreite: ([\d.]+)pt", z)
        if m:
            breite = float(m.group(1)) * 25.4 / 72.27
            formate = _formatbreiten()
            if formate and all(abs(breite - b) > 0.1 for b in formate):
                return [f"Abbildung ist {breite:.1f} mm breit, kein Format des Leitfadens "
                        f"({', '.join(f'{b:g}' for b in formate)} mm) - fehlt \\vfdbRahmen "
                        "bzw. vfdbschema?"]
    return []


def _kombinierende_zeichen(tex: Path) -> list[str]:
    """Kombinierende Zeichen (z. B. Q mit Punkt aus Word, U+0307) setzt LaTeX ohne Meldung
    falsch oder gar nicht."""
    import unicodedata
    try:
        zeilen = tex.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return []
    return [f"{tex.name}:{nr}: Zeichen U+{ord(c):04X} (kombinierend, z. B. aus Word kopiert) "
            f"erscheint nicht richtig - Formelzeichen als $\\dot{{Q}}$, $\\dot{{m}}$ schreiben"
            for nr, z in enumerate(zeilen, start=1) if not z.lstrip().startswith("%")
            for c in dict.fromkeys(unicodedata.normalize("NFC", z))   # zerlegtes ä ist richtig
            if unicodedata.combining(c)]


def bauen(tex: Path, ziel: Path | None = None) -> tuple[Path, list[str]]:
    """Uebersetzt `tex`; gibt (PDF-Pfad, Warnungen) zurueck."""
    tex = Path(tex).resolve()
    if not tex.is_file():
        raise BauFehler(f"{tex}: Datei nicht gefunden")
    if shutil.which("lualatex") is None:
        raise BauFehler("lualatex nicht gefunden - LaTeX-Installation (MiKTeX/TeX Live) prüfen, "
                        "siehe docs/Installation.md")
    ziel = (ziel or tex.parent).resolve()
    with tempfile.TemporaryDirectory(prefix="vfdbstil_") as tmp:
        arbeit = Path(tmp) / "abbildung"
        if _ordnergroesse(tex.parent) <= HOECHSTENS_BYTES:
            ausgabe = tex.with_suffix(".pdf").name
            shutil.copytree(tex.parent, arbeit, ignore=lambda d, n: set(IGNORIEREN(d, n)) |
                            ({ausgabe} if Path(d) == tex.parent else set()))
        else:                                 # sehr grosser Ordner: nur die .tex-Datei
            arbeit.mkdir()
            shutil.copy(tex, arbeit / tex.name)
            print(f"  HINWEIS {tex.parent} ist größer als 200 MB - nur {tex.name} wird "
                  "übersetzt (Daten in einen kleineren Ordner legen)", file=sys.stderr)
        for d in STILDATEIEN:
            shutil.copy(LATEX / d, arbeit / d)
        lauf = subprocess.run(["lualatex", "-interaction=nonstopmode", "-halt-on-error",
                               "-file-line-error", tex.name], cwd=arbeit, capture_output=True,
                              text=True, encoding="utf-8", errors="replace")
        pdf = arbeit / tex.with_suffix(".pdf").name
        log = arbeit / tex.with_suffix(".log").name
        zeilen = log.read_text(encoding="utf-8", errors="replace").splitlines() if log.exists() else []
        if lauf.returncode != 0 or not pdf.exists():
            fehler = _meldungen(zeilen, lambda z: z.startswith("!")   # auch Namen mit Leerzeichen
                                or re.match(r"^(?:[A-Za-z]:)?[^:]+\.[A-Za-z]+:\d+: ", z))  # .tex, .sty
            fehler = fehler or zeilen[-20:] or [lauf.stdout[-2000:]]
            raise BauFehler(f"{tex.name}: LuaLaTeX-Fehler\n  " + "\n  ".join(fehler[:6]))
        warnungen = list(dict.fromkeys(_meldungen(zeilen, lambda z: bool(WARNMUSTER.search(z)))))
        warnungen += _breite_pruefen(zeilen)
        warnungen += _kombinierende_zeichen(tex)
        ziel.mkdir(parents=True, exist_ok=True)
        try:
            return Path(shutil.copy(pdf, ziel / pdf.name)), warnungen
        except PermissionError:
            raise BauFehler(f"{ziel / pdf.name} kann nicht geschrieben werden - ist das PDF noch "
                            "geöffnet?") from None


def main(argv: list[str] | None = None) -> int:
    for strom in (sys.stdout, sys.stderr):
        if hasattr(strom, "reconfigure"):
            strom.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("dateien", nargs="+", help=".tex-Dateien (Platzhalter * erlaubt)")
    p.add_argument("--ziel", type=Path, help="Ordner für die PDF-Dateien")
    a = p.parse_args(argv)
    dateien: list[Path] = []
    fehler = 0
    for muster in a.dateien:
        if Path(muster).exists() or not any(c in muster for c in "*?["):
            treffer = [muster]                # auch Namen mit [ ] (sonst Platzhalter)
        else:
            treffer = sorted(glob.glob(muster))
        if not treffer:
            print(f"FEHLER: keine Datei passt zu {muster}", file=sys.stderr)
            fehler += 1
        dateien += [Path(t) for t in treffer]
    for d in dateien:
        try:
            pdf, warnungen = bauen(d, a.ziel)
            print(pdf)
            for w in warnungen:
                print(f"  WARNUNG {w}")
        except BauFehler as e:
            print(f"FEHLER: {e}", file=sys.stderr)
            fehler += 1
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
