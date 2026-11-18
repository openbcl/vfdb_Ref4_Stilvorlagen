"""vfdb_stil - einheitlicher Grafikstil fuer den vfdb-Leitfaden Ingenieurmethoden.

Beispiel:

    import numpy as np
    import vfdb_stil as vs

    t = np.linspace(0, 120, 600)
    fig, ax = vs.figur("standard", legende=2)
    ax.plot(t, 20 + 345 * np.log10(8 * t + 1), label="ETK", **vs.reihe(0))
    ax.plot(t, 20 + 660 * (1 - 0.687 * np.exp(-0.32 * t) - 0.313 * np.exp(-3.8 * t)),
            label="Außenbrandkurve", **vs.reihe(1))
    ax.set_xlabel(r"Zeit $t$ in \\si{\\minute}")
    ax.set_ylabel(r"Gastemperatur $T$ in \\si{\\degreeCelsius}")
    vs.deutsch(ax)
    vs.legende_unten(ax)
    vs.speichern(fig, "media/04-temperaturzeitkurven.pdf")

Der Import stellt matplotlib auf das pgf-Backend (LuaLaTeX) um; eine Bildschirmvorschau
mit plt.show() ist danach nicht moeglich - das gespeicherte PDF ansehen.
"""
from .abbildung import (HILFSLINIE, LINIE_DUENN, MM, PFEIL_ACHSE, PFEIL_HINWEIS, PFEIL_MASS,
                        KommaFormatter, achse_mm, anwenden, deutsch, fehlende_zeichen, figur,
                        hinweis, komma_formatter,
                        legende_unten, legende_zeilen, nachweis, pfeilachsen, phasenbalken,
                        praeambel, pruefen, speichern, unten_legende, unter_achse, xdata_ymm, zahl)
from .stil import (FARBEN, FARBNAMEN, FLAECHE_DECKKRAFT, FORMATE, GRAU, GRAU_FLAECHE, GRAU_HELL,
                   LINIENSTILE, STIL, TEXT, TEXTBREITE_MM, farbe, farbwert, legende_spalten,
                   linienstil, reihe)

__version__ = STIL["version"]

__all__ = [
    "FARBEN", "FARBNAMEN", "FLAECHE_DECKKRAFT", "FORMATE", "GRAU", "GRAU_FLAECHE", "GRAU_HELL",
    "HILFSLINIE", "LINIE_DUENN", "LINIENSTILE", "MM", "fehlende_zeichen", "PFEIL_ACHSE", "PFEIL_HINWEIS", "PFEIL_MASS", "STIL", "TEXT",
    "TEXTBREITE_MM", "KommaFormatter", "achse_mm", "anwenden", "deutsch", "farbe", "farbwert",
    "figur", "hinweis", "komma_formatter", "legende_spalten", "legende_unten", "legende_zeilen",
    "linienstil", "nachweis", "pfeilachsen", "phasenbalken", "praeambel", "pruefen", "reihe",
    "speichern", "unten_legende", "unter_achse", "xdata_ymm", "zahl",
]
