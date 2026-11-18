"""Stilwerte aus stil/stil.yaml (einzige Quelle) als Python-Konstanten."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


def stil_pfad() -> Path:
    """Pfad der stil.yaml: im installierten Paket oder im Repository (Entwicklung)."""
    hier = Path(__file__).resolve().parent
    for pfad in (hier / "stil.yaml", hier.parent.parent / "stil" / "stil.yaml"):
        if pfad.is_file():
            return pfad
    raise FileNotFoundError("stil.yaml nicht gefunden (weder im Paket noch unter stil/)")


@lru_cache(maxsize=1)
def laden() -> dict[str, Any]:
    with stil_pfad().open(encoding="utf-8") as f:
        return yaml.safe_load(f)


STIL = laden()

TEXTBREITE_MM: float = STIL["seite"]["textbreite_mm"]
FORMATE: dict[str, dict[str, float]] = STIL["formate"]

SCHRIFT_TEXT: str = STIL["schrift"]["text"]
SCHRIFT_FORMEL: str = STIL["schrift"]["formel"]
PT_BESCHRIFTUNG: float = STIL["schrift"]["groesse_pt"]["beschriftung"]
PT_TICKS: float = STIL["schrift"]["groesse_pt"]["ticks"]
PT_LEGENDE: float = STIL["schrift"]["groesse_pt"]["legende"]
ZEILENABSTAND: float = STIL["schrift"]["zeilenabstand"]
ZAHLEN = STIL["zahlen"]

_F = STIL["farben"]
FARBEN: list[str] = list(_F["kategorien"])
FARBNAMEN: list[str] = list(_F["kategorien_namen"])
TEXT: str = _F["text"]
GRAU: str = _F["grau"]
GRAU_HELL: str = _F["grau_hell"]
GRAU_FLAECHE: str = _F["grau_flaeche"]
FLAECHE_DECKKRAFT: float = _F["flaeche_deckkraft"]

STRICHE = {"durchgezogen": "-", "gestrichelt": "--", "gepunktet": ":", "strichpunkt": "-."}


def farbwert(name: str) -> str:
    """Farbname aus stil.yaml (z. B. "text", "grau_hell") oder #rrggbb -> #rrggbb."""
    if name.startswith("#"):
        return name
    if name not in _F or not isinstance(_F[name], str):
        raise KeyError(f"unbekannte Farbe {name!r} in stil.yaml")
    return _F[name]


def _linienstil(eintrag: dict) -> Any:
    if "muster" in eintrag:
        return (0, tuple(float(x) for x in eintrag["muster"]))
    return STRICHE[eintrag["name"]]


LINIENSTILE: list[Any] = [_linienstil(e) for e in STIL["linienstile"]]

ACHSE = STIL["achsen"]
LINIEN = STIL["linien"]
LEGENDE = STIL["legende"]
PFEILE = STIL["pfeile"]
SCHEMA = STIL["schema"]


def farbe(i: int) -> str:
    """Farbe der Reihe i (0-basiert) in fester Reihenfolge."""
    if not 0 <= i < len(FARBEN):
        raise IndexError(f"Reihe {i + 1}: nur {len(FARBEN)} Farben festgelegt - Reihen "
                         "zusammenfassen oder auf mehrere Felder verteilen")
    return FARBEN[i]


def linienstil(i: int) -> Any:
    """Linienstil der Reihe i (0-basiert); Reihen ohne festgelegten Stil: durchgezogen."""
    return LINIENSTILE[i] if 0 <= i < len(LINIENSTILE) else "-"


def reihe(i: int) -> dict[str, Any]:
    """Plot-Argumente (Farbe und Linienstil) der Reihe i, z. B. ax.plot(x, y, **reihe(0))."""
    return {"color": farbe(i), "linestyle": linienstil(i)}


def legende_spalten(eintraege: int) -> int:
    """Spaltenzahl der Legende nach stil.yaml (legende.spalten)."""
    if eintraege <= 0:
        return 0
    regel = {int(k): int(v) for k, v in LEGENDE["spalten"].items()}
    return regel.get(eintraege, regel[max(regel)])
