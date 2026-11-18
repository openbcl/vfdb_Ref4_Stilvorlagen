"""Beispiel Standardformat: nominelle Temperaturzeitkurven (Liniendiagramm mit Legende).

Kurven nach DIN EN 1991-1-2, Abschnitt 3.2 (t in min, T0 = 20 degC):
    ETK:              T - T0 = 345 lg(8 t + 1)
    Aussenbrandkurve: T - T0 = 660 (1 - 0,687 e^(-0,32 t) - 0,313 e^(-3,8 t))
    Hydrokarbonkurve: T - T0 = 1080 (1 - 0,325 e^(-0,167 t) - 0,675 e^(-2,5 t))
"""
from pathlib import Path

import numpy as np

import vfdb_stil as vs

T0 = 20.0
t = np.linspace(0, 120, 600)
kurven = [
    ("Einheits-Temperaturzeitkurve (ETK)", T0 + 345 * np.log10(8 * t + 1)),
    ("Hydrokarbonkurve", T0 + 1080 * (1 - 0.325 * np.exp(-0.167 * t) - 0.675 * np.exp(-2.5 * t))),
    ("Außenbrandkurve", T0 + 660 * (1 - 0.687 * np.exp(-0.32 * t) - 0.313 * np.exp(-3.8 * t))),
]

fig, ax = vs.figur("standard", legende=len(kurven))
for i, (name, T) in enumerate(kurven):
    ax.plot(t, T, label=name, **vs.reihe(i))
ax.set_xlim(0, 120)
ax.set_ylim(0, 1200)
ax.set_xticks(range(0, 121, 15))
ax.set_yticks(range(0, 1201, 200))
ax.set_xlabel(r"Zeit $t$ in \si{\minute}")
ax.set_ylabel(r"Gastemperatur $T$ in \si{\degreeCelsius}")
vs.deutsch(ax)
vs.legende_unten(ax)
vs.speichern(fig, Path(__file__).resolve().parents[1] / "pdf" / "nominelle_temperaturzeitkurven.pdf")
