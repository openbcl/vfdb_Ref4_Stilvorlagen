"""Beispiel zweifeldrig: t^2-Brandentwicklung - Waermefreisetzungsrate und freigesetzte Energie.

Qdot = alpha t^2, Q = alpha t^3 / 3 mit den gebraeuchlichen Standardwerten fuer alpha
(1055 kW, also etwa 1 MW, nach 600 / 300 / 150 / 75 s): langsam 0,002931, mittel 0,01172,
schnell 0,04689, sehr schnell 0,1876 kW/s^2.
Zweifeldrig: Die y-Achsentitel nennen nur Symbol und Einheit (fuer den Groessennamen reicht
die Feldhoehe nicht), die Groessen nennt die Bildunterschrift.
"""
from pathlib import Path

import numpy as np

import vfdb_stil as vs

ALPHA = [("langsam", 0.002931), ("mittel", 0.01172), ("schnell", 0.04689),
         ("sehr schnell", 0.1876)]
t = np.linspace(0, 600, 601)            # s

fig, (ax1, ax2) = vs.figur("zweifeldrig", legende=len(ALPHA), sharex=True)
for i, (name, a) in enumerate(ALPHA):
    ax1.plot(t / 60, a * t ** 2 / 1000, label=name, **vs.reihe(i))      # MW
    ax2.plot(t / 60, a * t ** 3 / 3 / 1000, **vs.reihe(i))              # MJ
ax1.set_ylim(0, 5)
ax1.set_yticks(range(0, 6))
ax1.set_ylabel(r"$\dot{Q}$ in \si{\mega\watt}")
ax2.set_ylim(0, 1000)
ax2.set_yticks(range(0, 1001, 250))
ax2.set_ylabel(r"$Q$ in \si{\mega\joule}")
ax2.set_xlim(0, 10)
ax2.set_xticks(range(0, 11))
ax2.set_xlabel(r"Zeit $t$ in \si{\minute}")
ax1.tick_params(labelbottom=False)
for ax in (ax1, ax2):
    vs.deutsch(ax)
vs.legende_unten(ax2, *ax1.get_legend_handles_labels())
vs.speichern(fig, Path(__file__).resolve().parents[1] / "pdf" / "t2_brandentwicklung.pdf")
