"""Rechnerische Pruefung der Kategorienpalette (Farbsehschwaeche, Unterscheidbarkeit).

Pruefungen (Schwellenwerte nach einer allgemeinen Referenz fuer Datenvisualisierung):
* Helligkeitsband: OKLCH-L zwischen 0,43 und 0,77 (auf hellem Grund)
* Mindest-Buntheit: OKLCH-C >= 0,10 (darunter wirkt eine Farbe grau)
* Farbsehschwaeche: Farbabstand Delta E (OKLab x 100) benachbarter Reihen bei simulierter
  Protanopie und Deuteranopie (Schweregrad 1,0); Ziel >= 8, Untergrenze 6 (nur mit zweitem
  Merkmal, hier: Linienstil); Tritanopie wird angegeben
* Normalsichtige: Delta E benachbarter Reihen >= 15
* Kontrast gegen Papierweiss >= 3:1, sonst Hinweis

Quellen:
* OKLab: B. Ottosson (2020), A perceptual color space for image processing,
  https://bottosson.github.io/posts/oklab/
* Simulation der Farbsehschwaeche: G. M. Machado, M. M. Oliveira, L. A. F. Fernandes (2009),
  A Physiologically-based Model for Simulation of Color Vision Deficiency, IEEE Transactions
  on Visualization and Computer Graphics 15(6), 1291-1298 (Matrizen fuer Schweregrad 1,0)
* Relative Leuchtdichte und Kontrastverhaeltnis: W3C, Web Content Accessibility Guidelines
  (WCAG) 2.1, Begriffsbestimmungen "relative luminance" und "contrast ratio"

Aufruf: vfdb-farbpruefung [--alle-paare] [#hex,#hex,...]   (ohne Farben: Palette aus stil.yaml)
"""
from __future__ import annotations

import argparse
import math
import re
import sys

BAND = (0.43, 0.77)
BUNTHEIT_MIN = 0.10
CVD_ZIEL, CVD_MIN = 8.0, 6.0
NORMAL_MIN = 15.0
KONTRAST_MIN = 3.0
PAPIER = "#ffffff"

MACHADO = {
    "Protanopie": ((0.152286, 1.052583, -0.204868),
                   (0.114503, 0.786281, 0.099216),
                   (-0.003882, -0.048116, 1.051998)),
    "Deuteranopie": ((0.367322, 0.860646, -0.227968),
                     (0.280085, 0.672501, 0.047413),
                     (-0.011820, 0.042940, 0.968881)),
    "Tritanopie": ((1.255528, -0.076749, -0.178779),
                   (-0.078411, 0.930809, 0.147602),
                   (0.004733, 0.691367, 0.303900)),
}


def _srgb(h: str) -> tuple[float, float, float]:
    h = h.strip().lstrip("#")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", h):
        raise ValueError(f"keine Farbe #rrggbb: {h!r}")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def linear_rgb(h: str) -> tuple[float, float, float]:
    return tuple(_linear(c) for c in _srgb(h))


def oklab(rgb_lin) -> tuple[float, float, float]:
    r, g, b = rgb_lin
    l_ = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m_ = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s_ = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
            1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
            0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_)


def _simuliert(h: str, art: str | None):
    rgb = linear_rgb(h)
    if art is None:
        return rgb
    m = MACHADO[art]
    return tuple(min(1.0, max(0.0, sum(m[i][k] * rgb[k] for k in range(3)))) for i in range(3))


def delta_e(h1: str, h2: str, art: str | None = None) -> float:
    """Farbabstand in OKLab x 100 (art=None: Normalsichtige)."""
    a, b = oklab(_simuliert(h1, art)), oklab(_simuliert(h2, art))
    return 100 * math.dist(a, b)


def oklch(h: str) -> tuple[float, float]:
    L, a, b = oklab(linear_rgb(h))
    return L, math.hypot(a, b)


def kontrast(h1: str, h2: str) -> float:
    def lum(h):
        r, g, b = linear_rgb(h)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    hi, lo = sorted((lum(h1), lum(h2)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def pruefen(farben: list[str], alle_paare: bool = False) -> tuple[list[tuple[str, str, str]], bool]:
    """Liste (Pruefung, Ergebnis BESTANDEN/HINWEIS/NICHT BESTANDEN, Detail) und Gesamtergebnis."""
    n = len(farben)
    paare = ([(i, j) for i in range(n) for j in range(i + 1, n)] if alle_paare
             else [(i, i + 1) for i in range(n - 1)])
    bericht, ok = [], True

    aus = [(f, round(oklch(f)[0], 3)) for f in farben if not BAND[0] <= oklch(f)[0] <= BAND[1]]
    ok &= not aus
    bericht.append(("Helligkeitsband", "BESTANDEN" if not aus else "NICHT BESTANDEN",
                    f"alle {n} in L {BAND[0]}-{BAND[1]}" if not aus else f"ausserhalb: {aus}"))

    grau = [(f, round(oklch(f)[1], 3)) for f in farben if oklch(f)[1] < BUNTHEIT_MIN]
    ok &= not grau
    bericht.append(("Mindest-Buntheit", "BESTANDEN" if not grau else "NICHT BESTANDEN",
                    f"alle {n} >= {BUNTHEIT_MIN}" if not grau else f"zu grau: {grau}"))

    if not paare:
        bericht.append(("Paarvergleiche", "HINWEIS", "weniger als zwei Farben - entfällt"))
        return bericht, ok
    schlecht = min(((delta_e(farben[i], farben[j], art), art, i, j)
                    for art in ("Protanopie", "Deuteranopie") for i, j in paare))
    tri = min(delta_e(farben[i], farben[j], "Tritanopie") for i, j in paare)
    d, art, i, j = schlecht
    zustand = "BESTANDEN" if d >= CVD_ZIEL else ("HINWEIS" if d >= CVD_MIN else "NICHT BESTANDEN")
    ok &= d >= CVD_MIN
    bericht.append(("Farbsehschwaeche", zustand,
                    f"ungünstigstes Paar Reihe {i + 1}/{j + 1} ({farben[i]}/{farben[j]}): "
                    f"Delta E {d:.1f} ({art}); Tritanopie min. {tri:.1f}"))

    dn, i, j = min((delta_e(farben[i], farben[j]), i, j) for i, j in paare)
    ok &= dn >= NORMAL_MIN
    bericht.append(("Normalsichtige", "BESTANDEN" if dn >= NORMAL_MIN else "NICHT BESTANDEN",
                    f"ungünstigstes Paar Reihe {i + 1}/{j + 1}: Delta E {dn:.1f} (Grenze {NORMAL_MIN:.0f})"))

    gering = [(f, round(kontrast(f, PAPIER), 2)) for f in farben if kontrast(f, PAPIER) < KONTRAST_MIN]
    bericht.append(("Kontrast zu Papierweiss", "BESTANDEN" if not gering else "HINWEIS",
                    f"alle {n} >= {KONTRAST_MIN}:1" if not gering else
                    f"unter {KONTRAST_MIN}:1 (Linien kräftig genug zeichnen, Direktbeschriftung): {gering}"))
    return bericht, ok


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Kategorienpalette rechnerisch prüfen")
    p.add_argument("farben", nargs="?", help="#hex,#hex,... (ohne Angabe: Palette aus stil.yaml)")
    p.add_argument("--alle-paare", action="store_true",
                   help="alle Paare statt nur benachbarter Reihen prüfen (Streudiagramme, Karten)")
    a = p.parse_args(argv)
    if a.farben:
        farben = [f.strip() for f in re.split(r"[,;\s]+", a.farben) if f.strip()]
    else:
        from .stil import FARBEN
        farben = FARBEN
    try:
        bericht, ok = pruefen(farben, a.alle_paare)
    except ValueError as e:
        print(f"FEHLER: {e} - Farben als #rrggbb angeben, z. B. #2a78d6,#eb6834", file=sys.stderr)
        return 2
    print(f"Palette mit {len(farben)} Farben, {'alle Paare' if a.alle_paare else 'benachbarte Reihen'}:")
    for name, zustand, detail in bericht:
        print(f"  [{zustand:15s}] {name:24s} {detail}")
    print("  -> " + ("alle Prüfungen bestanden" if ok else "nicht bestanden"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
