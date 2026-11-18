"""Erzeugt die Excel-Vorlage und das Excel-Beispiel aus dem Paket (Angaben an einer Stelle).

    python excel/erzeuge_vorlagen.py
"""
from pathlib import Path

import numpy as np

from vfdb_stil.excel import vorlage_schreiben

REPO = Path(__file__).resolve().parents[1]

print(vorlage_schreiben(REPO / "excel" / "Vorlage_Abbildung.xlsx"))

# Beispiel zweifeldrig: t^2-Brandentwicklung (gleiche Abbildung wie
# beispiele/python/t2_brandentwicklung.py, hier aus Excel erzeugt)
ALPHA = [("langsam", 0.002931), ("mittel", 0.01172), ("schnell", 0.04689),
         ("sehr schnell", 0.1876)]
t = np.arange(0, 601, 5.0)
daten = {"t in min": list(t / 60)}
reihen = []
for name, a in ALPHA:
    q = a * t ** 2 / 1000
    e = a * t ** 3 / 3 / 1000
    # Werte oberhalb der Achsgrenze weglassen (leere Zelle = Luecke)
    daten[f"Q {name}"] = [round(v, 5) if v <= 5.2 else None for v in q]
    daten[f"E {name}"] = [round(v, 3) if v <= 1040 else None for v in e]
for name, _a in ALPHA:
    reihen.append([f"Q {name}", name, 1, "Linie", None])
for name, _a in ALPHA:
    reihen.append([f"E {name}", name, 2, "Linie", None])

beispiel = {
    "angaben": {
        "Dateiname": "t2_brandentwicklung_excel",
        "Format": "zweifeldrig",
        "x-Spalte": "t in min",
        "x-Achsentitel": r"Zeit $t$ in \si{\minute}",
        "y-Achsentitel": r"$\dot{Q}$ in \si{\mega\watt}",
        "y-Achsentitel Feld 2": r"$Q$ in \si{\mega\joule}",
        "x min": 0, "x max": 10, "x Schritt": 1,
        "y min": 0, "y max": 5, "y Schritt": 1,
        "y min Feld 2": 0, "y max Feld 2": 1000, "y Schritt Feld 2": 250,
    },
    "reihen": reihen,
    "daten": daten,
}
print(vorlage_schreiben(REPO / "beispiele" / "excel" / "t2_brandentwicklung.xlsx", beispiel))
