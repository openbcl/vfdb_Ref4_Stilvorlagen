"""Beispiel Schema: schematisierter Brandverlauf mit Brandphasen (Prinzipskizze ohne Zahlen).

Pfeilachsen, Flaechen, Hilfslinien, Hinweispfeile und Phasenbalken nach den Stilvorgaben.
Allgemeines Prinzip (t^2-Anstieg, Vollbrandphase, linearer Abfall), vgl. das vereinfachte
Naturbrandmodell in DIN EN 1991-1-2/NA, Anhang AA.
"""
from pathlib import Path

import numpy as np

import vfdb_stil as vs

X_MAX, Y_MAX = 10.6, 9.0
Q_V = 6.0
T1, T2, T3 = 2.7, 6.4, 9.0

t_a = np.linspace(0, T1, 200)
q_a = Q_V * (t_a / T1) ** 2

fig, ax = vs.figur("standard", unten=14.0)
vs.pfeilachsen(ax, X_MAX, Y_MAX, ylabel=r"Wärmefreisetzungsrate $\dot{Q}$")

ax.fill_between(t_a, 0, q_a, color=vs.GRAU_FLAECHE, lw=0)
ax.fill_between([T1, T2, T3], 0, [Q_V, Q_V, 0], color=vs.GRAU_FLAECHE, lw=0)
for x in (T1, T2):
    ax.plot([x, x], [0, Q_V], **vs.HILFSLINIE)
ax.plot(np.r_[t_a, T2, T3], np.r_[q_a, Q_V, 0], color=vs.farbe(0), zorder=3)

# Hinweise: Pfeile waagerecht bzw. senkrecht
x_g = 2.0
q_g = Q_V * (x_g / T1) ** 2
vs.hinweis(ax, r"$\dot{Q}=\alpha\cdot t^{2}$", xy=(x_g + 0.1, q_g), xytext=(3.3, q_g),
           ha="left", va="center")
vs.hinweis(ax, "70 % der Brandlast\nverbrannt", xy=(T2, Q_V + 0.15), xytext=(T2, 8.0),
           ha="center", va="bottom")

vs.phasenbalken(ax, 0, T1, "Brandausbreitung")
vs.phasenbalken(ax, T1, T2, "Vollbrandphase")
vs.phasenbalken(ax, T2, T3, "Abklingphase")

ax.set_xticks([T1, T2, T3])
ax.set_xticklabels([r"$t_{1}$", r"$t_{2}$", r"$t_{3}$"])
ax.set_yticks([Q_V])
ax.set_yticklabels([r"$\dot{Q}_\mathrm{max}$"])
vs.speichern(fig, Path(__file__).resolve().parents[1] / "pdf" / "schema_brandphasen.pdf")
