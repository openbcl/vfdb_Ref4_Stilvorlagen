"""Abbildungen in fester Groesse mit matplotlib (pgf-Backend, LuaLaTeX).

Schrift (TeX Gyre Heros), Formelsatz (Fira Math) und Einheiten (siunitx) werden von
LuaLaTeX gesetzt und entsprechen damit dem Leitfaden-Text. Voraussetzung: eine
LaTeX-Installation mit LuaLaTeX, fontspec, unicode-math, siunitx, mhchem und den Schriften
TeX Gyre Heros und Fira Math (z. B. MiKTeX oder TeX Live).

Beim Import wird matplotlib auf das pgf-Backend umgestellt und der Leitfaden-Stil gesetzt:
Nur so bestimmt LaTeX selbst die Textmasse fuer Legende und Ueberlappungspruefung. Eine
Bildschirmvorschau (plt.show) ist danach nicht moeglich - das gespeicherte PDF ansehen.
"""
from __future__ import annotations

import math
import re
import subprocess
import sys
from functools import lru_cache
from itertools import combinations
from pathlib import Path

import matplotlib

matplotlib.use("pgf")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.text import Text  # noqa: E402
from matplotlib.ticker import Formatter  # noqa: E402
from matplotlib.transforms import blended_transform_factory  # noqa: E402

from . import stil as S  # noqa: E402

MM = 1 / 25.4                 # mm -> inch

_L = S.LEGENDE
_A = S.ACHSE
_P = S.PFEILE
_Z = S.ZAHLEN
MAX_WARNUNGEN = 20


def _pfeil(art: str, **zusatz) -> dict:
    """matplotlib-Pfeilstil aus stil.yaml (Spitzenlaenge = 0,4 x mutation_scale)."""
    beidseitig = _P[art].get("beidseitig", False)
    d = dict(arrowstyle="<|-|>" if beidseitig else "-|>", lw=_P["linie_pt"],
             color=S.farbwert(_P["farbe"]),
             mutation_scale=_P[art]["spitze_laenge_pt"] / 0.4, shrinkA=0, shrinkB=0)
    d.update(zusatz)
    return d


PFEIL_ACHSE = _pfeil("achse")
PFEIL_HINWEIS = _pfeil("hinweis", shrinkA=_P["hinweis"]["abstand_text_pt"],
                       shrinkB=_P["hinweis"]["abstand_ziel_pt"])
PFEIL_MASS = _pfeil("mass")
_HL = S.LINIEN["hilfslinie"]
HILFSLINIE = dict(color=S.farbwert(_HL["farbe"]), ls=S.STRICHE[_HL["stil"]], lw=_HL["linie_pt"])
LINIE_DUENN = S.LINIEN["duenn_pt"]   # Nebenkurven in Schemata, z. B. ax.plot(..., lw=vs.LINIE_DUENN)


def praeambel() -> str:
    """LaTeX-Praeambel fuer das pgf-Backend: Schriften wie im Leitfaden; siunitx nach
    stil.yaml (bewusst ohne die Rundung des Leitfadens)."""
    return "\n".join([
        r"\usepackage{fontspec}",
        r"\usepackage{unicode-math}",
        rf"\setmainfont{{{S.SCHRIFT_TEXT}}}",
        rf"\setsansfont{{{S.SCHRIFT_TEXT}}}",
        rf"\setmathfont{{{S.SCHRIFT_FORMEL}}}",
        r"\usepackage[ngerman]{babel}",
        r"\usepackage{siunitx}",
        rf"\sisetup{{{_Z['siunitx']}}}",
        r"\usepackage[version=4]{mhchem}",
    ])


def rc_parameter() -> dict:
    t = _A["ticks"]
    n = len(S.FARBEN)
    return {
        "pgf.texsystem": "lualatex",
        "pgf.rcfonts": False,
        "pgf.preamble": praeambel(),
        "text.usetex": False,
        "font.family": "sans-serif",
        "font.size": S.PT_BESCHRIFTUNG,
        "axes.labelsize": S.PT_BESCHRIFTUNG,
        "axes.titlesize": S.PT_BESCHRIFTUNG,
        "xtick.labelsize": S.PT_TICKS,
        "ytick.labelsize": S.PT_TICKS,
        "legend.fontsize": S.PT_LEGENDE,
        "legend.frameon": _L["rahmen"],
        "legend.handlelength": _L["symbollaenge_em"],
        "legend.handletextpad": _L["textabstand_em"],
        "legend.labelspacing": 0.5,    # ergibt bei 8 pt den Zeilenabstand zeile_mm (Test)
        "legend.borderpad": 0.0,
        "legend.borderaxespad": 0.0,
        "legend.columnspacing": _L["spaltenabstand_em"],
        "axes.linewidth": _A["linie_pt"],
        "axes.edgecolor": S.farbwert(_A["farbe"]),
        "axes.labelcolor": S.TEXT,
        "text.color": S.TEXT,
        "xtick.color": S.farbwert(_A["farbe"]),
        "ytick.color": S.farbwert(_A["farbe"]),
        "axes.grid": _A["gitter"]["sichtbar"],
        "axes.axisbelow": _A["gitter"]["hinter_daten"],
        "axes.xmargin": _A["datenrand"],
        "axes.ymargin": _A["datenrand"],
        "grid.color": S.farbwert(_A["gitter"]["farbe"]),
        "grid.linewidth": _A["gitter"]["linie_pt"],
        "grid.linestyle": "-",
        "xtick.direction": "in" if t["richtung"] == "innen" else "out",
        "ytick.direction": "in" if t["richtung"] == "innen" else "out",
        "xtick.major.width": t["linie_pt"],
        "ytick.major.width": t["linie_pt"],
        "xtick.major.size": t["laenge_pt"],
        "ytick.major.size": t["laenge_pt"],
        "xtick.major.pad": t["abstand_pt"],
        "ytick.major.pad": t["abstand_pt"],
        "xtick.minor.visible": t["nebenticks"],
        "ytick.minor.visible": t["nebenticks"],
        "lines.linewidth": S.LINIEN["daten_pt"],
        "lines.scale_dashes": True,    # Strichmuster in Vielfachen der Linienstaerke (stil.yaml)
        "lines.markersize": S.LINIEN["marker_pt"],
        "lines.markeredgewidth": S.LINIEN["daten_pt"],   # Markerumriss wie PGFPlots (Linienstaerke)
        "axes.spines.top": _A["oben_rechts"],
        "axes.spines.right": _A["oben_rechts"],
        # alle 8 Farben mit ihren Linienstilen; die 9. Reihe beginnt wieder bei 1 - mehr
        # als 8 Reihen widersprechen den Stilvorgaben (vs.reihe() meldet einen Fehler)
        "axes.prop_cycle": matplotlib.cycler(color=S.FARBEN,
                                             linestyle=[S.linienstil(i) for i in range(n)]),
        "axes.formatter.use_locale": False,
        "savefig.bbox": None,          # feste Figurgroesse, kein Beschnitt
        "savefig.pad_inches": 0.0,
    }


def anwenden() -> None:
    """Setzt die matplotlib-Parameter des Leitfaden-Stils."""
    plt.rcParams.update(rc_parameter())


anwenden()


# --- Zahlen ----------------------------------------------------------------------
def _exponent_noetig(x: float) -> bool:
    return x != 0 and not (_Z["exponent_unter"] <= abs(x) < _Z["exponent_ab"])


def zahl(x: float, nachkomma: int | None = None, exponent: bool | None = None) -> str:
    """Zahl mit Dezimalkomma, ohne Tausendertrennung, mit echtem Minuszeichen.

    exponent: True = als $a\\cdot 10^{n}$, False = ausgeschrieben, None = nach Betrag
    (stil.yaml: zahlen.exponent_ab/_unter). nachkomma: feste Zahl von Nachkommastellen
    (bei Exponentenschreibweise fuer die Mantisse).
    """
    x = float(x)
    if not math.isfinite(x):
        raise ValueError(f"Zahl {x} kann nicht dargestellt werden")
    komma, minus = _Z["dezimalzeichen"], _Z["minuszeichen"]
    if x != 0:
        x = float(f"{x:.10g}")                     # erst auf 10 gueltige Stellen runden
    if exponent is None:
        exponent = _exponent_noetig(x)
    if exponent and x != 0:
        from decimal import Decimal
        hoch = math.floor(math.log10(abs(x)))
        dezimal = Decimal(repr(x)).scaleb(-hoch)   # dezimal: 1.235e-5 -> 1.235 (nicht 1.2349...)

        def mantisse(d):
            return (f"{float(d):.6f}".rstrip("0").rstrip(".") if nachkomma is None
                    else _kaufmaennisch(float(d), nachkomma))
        m = mantisse(dezimal)
        if m.lstrip("-") == "10" or m.lstrip("-").startswith("10" + "."):   # Rundung auf 10,0
            hoch += 1
            m = mantisse(dezimal.scaleb(-1))
        m = m.replace(".", "{" + komma + "}")
        return rf"${m}\cdot 10^{{{hoch}}}$"
    if nachkomma is None:
        s = f"{x:.10g}"
        if "e" in s:                               # ausgeschrieben, auch wenn .10g Exponent waehlt
            s = f"{x:.15f}".rstrip("0").rstrip(".")
    else:
        s = _kaufmaennisch(x, nachkomma)
    if s.startswith("-") and float(s) == 0:
        s = s[1:]
    return s.replace("-", minus).replace(".", komma)


def _kaufmaennisch(x: float, nachkomma: int) -> str:
    """Auf `nachkomma` Stellen runden, ab 5 aufrunden (wie die LaTeX-Seite)."""
    from decimal import ROUND_HALF_UP, Decimal
    return str(Decimal(repr(x)).quantize(Decimal(1).scaleb(-nachkomma), rounding=ROUND_HALF_UP))


class KommaFormatter(Formatter):
    """Tick-Beschriftung mit zahl(): Rundungsreste nahe 0 (z. B. 1e-16) werden zu 0, und die
    Exponentenschreibweise gilt einheitlich fuer alle Teilstriche einer Achse."""

    def __init__(self, nachkomma: int | None = None):
        self.nachkomma = nachkomma
        self._exponent: bool | None = None
        self._null = 0.0

    def set_locs(self, locs):
        super().set_locs(locs)
        if self.axis is not None:
            lo, hi = sorted(self.axis.get_view_interval())
            self._null = 1e-9 * (abs(hi - lo) or 1.0)
            sichtbar = [abs(v) for v in locs if lo - self._null <= v <= hi + self._null
                        and abs(v) > self._null]
        else:
            sichtbar = [abs(v) for v in locs if v != 0]
        self._exponent = any(_exponent_noetig(v) for v in sichtbar) if sichtbar else False

    def __call__(self, x, pos=None):
        null = self._null
        if self.axis is not None:
            lo, hi = self.axis.get_view_interval()
            null = max(null, 1e-9 * (abs(hi - lo) or 1.0))
        if abs(x) <= null:
            x = 0.0
        return zahl(x, self.nachkomma, self._exponent)


def komma_formatter(nachkomma: int | None = None) -> KommaFormatter:
    return KommaFormatter(nachkomma)


def deutsch(ax, x_nachkomma: int | None = None, y_nachkomma: int | None = None) -> None:
    """Tick-Beschriftung der Zahlenachsen mit Dezimalkomma; logarithmische Achsen behalten
    die Beschriftung 10^n (wie im LaTeX-Paket), Kategorien-, Datums- und eigene
    Beschriftungen (set_xticklabels) bleiben unveraendert. Nach dem Zeichnen der Daten und
    nach ax.set_xscale/set_yscale aufrufen. Auch fuer Farbskalen: vs.deutsch(cb.ax).
    Nachkommastellen eines Formats "%.2f" bzw. "{x:.2f}" werden uebernommen."""
    for achse, nk in ((ax.xaxis, x_nachkomma), (ax.yaxis, y_nachkomma)):
        if _zahlenachse(achse) or isinstance(achse.get_major_formatter(), KommaFormatter):
            if nk is None:
                nk = _nachkomma_aus_format(achse.get_major_formatter())
            achse.set_major_formatter(komma_formatter(nk))


# Format, das nur aus einer Zahl besteht ("%.2f", "%d", "%.2e", "{x:,.0f}", "{x}") - ohne
# umgebenden Text und ohne Prozent-Typ
_NUR_ZAHL = re.compile(r"%[^%a-zA-Z]*[diouxXeEfFgG]|\{x(:[^{}%]*)?\}")


def _eigenes_format(achse) -> bool:
    """Lineare Achse mit eigenem Zahlenformat mit Text, Einheit oder Prozent ("{x:.0f} %")."""
    from matplotlib.ticker import FormatStrFormatter, StrMethodFormatter
    fmt = achse.get_major_formatter()
    return (achse.get_scale() in ("linear", "function")
            and isinstance(fmt, (FormatStrFormatter, StrMethodFormatter))
            and not _NUR_ZAHL.fullmatch(fmt.fmt or ""))


def _zahlenachse(achse) -> bool:
    """Lineare Zahlenachse (auch Farbskala) mit einer reinen Zahlenbeschriftung von matplotlib
    (ScalarFormatter, "%.1f", "{x:,.0f}") - nicht Kategorien, Datum oder eigene Texte; Formate
    mit Einheit oder Prozent ("{x:.0f} %", "{x:.0%}") gelten als eigene Beschriftung."""
    from matplotlib.ticker import FormatStrFormatter, ScalarFormatter, StrMethodFormatter
    if achse.get_scale() not in ("linear", "function"):
        return False
    fmt = achse.get_major_formatter()
    if isinstance(fmt, (FormatStrFormatter, StrMethodFormatter)):
        return bool(_NUR_ZAHL.fullmatch(fmt.fmt or ""))
    return isinstance(fmt, ScalarFormatter)


def _nachkomma_aus_format(fmt) -> int | None:
    if isinstance(fmt, KommaFormatter):          # zweiter Aufruf von deutsch(): beibehalten
        return fmt.nachkomma
    m = re.search(r"\.(\d+)[fF]", getattr(fmt, "fmt", "") or "")
    return int(m.group(1)) if m else None


def _zeichenfolge(ax, handle) -> int:
    """Position in der Zeichenreihenfolge (matplotlib fuehrt errorbar-Eintraege sonst nach
    allen Linien auf)."""
    kinder = ax.get_children()
    kandidaten = [handle] + list(getattr(handle, "get_children", lambda: [])())
    return min((kinder.index(k) for k in kandidaten if k in kinder), default=len(kinder))


def _hat_einheiten(achse) -> bool:
    """Kategorien- oder Datumsachse (matplotlib rechnet die Werte mit einem converter um)."""
    holen = getattr(achse, "get_converter", None)
    return (holen() if holen else getattr(achse, "converter", None)) is not None


# --- Figuren mit festen Raendern ---------------------------------------------------
def unten_legende(zeilen: int, extra_mm: float = 0.0, format: str = "standard") -> float:
    """Unterer Rand in mm fuer x-Ticks, x-Titel und eine Legende mit `zeilen` Zeilen."""
    if zeilen <= 0:
        return S.FORMATE[format]["rand_unten_mm"] + extra_mm
    return _L["abstand_mm"] + extra_mm + zeilen * _L["zeile_mm"] + _L["zuschlag_unten_mm"]


def legende_zeilen(eintraege: int) -> int:
    """Anzahl Legendenzeilen nach der Spaltenregel aus stil.yaml."""
    if eintraege <= 0:
        return 0
    return -(-eintraege // S.legende_spalten(eintraege))


def figur(format: str = "standard", *, legende: int = 0, unten: float | None = None,
          oben: float | None = None, links: float | None = None, rechts: float | None = None,
          breite: float | None = None, achse_h: float | None = None, nrows: int | None = None,
          ncols: int = 1, abstand: float | None = None, wabstand: float | None = None, **kw):
    """Figur im Format "standard", "zweifeldrig" oder "breit" mit Raendern in mm.

    legende: Anzahl der Legendeneintraege unter der Grafik (0 = keine Legende); der untere
             Rand wird danach bemessen (legende_unten passt ihn bei Bedarf an).
    abstand: senkrechter Feldabstand; wabstand: waagerechter Feldabstand bei ncols > 1
             (Standard: linker Rand, Platz fuer y-Beschriftung und y-Achsentitel).
    Die Hoehe ergibt sich aus oberem Rand + Feldern + unterem Rand.
    Weitere Schluesselwoerter gehen an plt.subplots (z. B. sharex=True).
    """
    if format not in S.FORMATE:
        raise ValueError(f"unbekanntes Format {format!r} (erlaubt: {', '.join(S.FORMATE)})")
    f = S.FORMATE[format]
    breite = f["breite_mm"] if breite is None else breite
    links = f["rand_links_mm"] if links is None else links
    rechts = f["rand_rechts_mm"] if rechts is None else rechts
    oben = f["rand_oben_mm"] if oben is None else oben
    explizit = unten is not None
    if unten is None:
        unten = unten_legende(legende_zeilen(legende), format=format)
    if nrows is None:
        nrows = 2 if format == "zweifeldrig" else 1
    achse_h = f["achse_h_mm"] if achse_h is None else achse_h
    if abstand is None:
        abstand = f.get("feldabstand_mm", S.FORMATE["zweifeldrig"]["feldabstand_mm"])
    wabstand = f["rand_links_mm"] if wabstand is None else wabstand
    hoehe = oben + nrows * achse_h + (nrows - 1) * abstand + unten
    fig, ax = plt.subplots(nrows, ncols, figsize=(breite * MM, hoehe * MM), **kw)
    fig._vfdb_legendenplatz = legende > 0 and not explizit   # pruefen: Legende vergessen?
    feld_b = (breite - links - rechts - (ncols - 1) * wabstand) / ncols
    fig.subplots_adjust(left=links / breite, right=1 - rechts / breite,
                        bottom=unten / hoehe, top=1 - oben / hoehe,
                        hspace=abstand / achse_h, wspace=wabstand / feld_b)
    return fig, ax


def achse_mm(ax):
    """(x0, y0, Breite, Hoehe) der Achsenflaeche in mm (Ursprung unten links)."""
    fig = ax.figure
    fb, fh = fig.get_figwidth() / MM, fig.get_figheight() / MM
    p = ax.get_position()
    return p.x0 * fb, p.y0 * fh, p.width * fb, p.height * fh


def unter_achse(ax, mm: float) -> float:
    """y-Koordinate (Achsenbruchteil) `mm` Millimeter unterhalb der Achsenunterkante."""
    return -mm / achse_mm(ax)[3]


def xdata_ymm(ax):
    """Transformation: x in Datenkoordinaten, y in Achsenbruchteilen."""
    return blended_transform_factory(ax.transData, ax.transAxes)


def _unten_anpassen(fig, ax_unten, unten_mm: float) -> None:
    """Setzt den unteren Rand unter `ax_unten` auf `unten_mm`; alle Achsenflaechen behalten
    ihre Groesse in mm, die Figurhoehe aendert sich entsprechend."""
    delta = unten_mm - achse_mm(ax_unten)[1]
    if abs(delta) < 0.01:
        return
    fb, fh = fig.get_figwidth() / MM, fig.get_figheight() / MM
    lagen = [(ax, achse_mm(ax)) for ax in fig.axes]
    fig.set_size_inches(fb * MM, (fh + delta) * MM)
    for ax, (x0, y0, b, h) in lagen:
        ax.set_position([x0 / fb, (y0 + delta) / (fh + delta), b / fb, h / (fh + delta)])


def _zeilenweise(eintraege, ncol: int) -> list:
    """Ordnet Eintraege so um, dass matplotlib (fuellt spaltenweise) sie zeilenweise
    in Lesereihenfolge zeigt - wie PGFPlots."""
    eintraege = list(eintraege)
    n = len(eintraege)
    if n == 0:
        return []
    zeilen = -(-n // ncol)
    voll = n - (zeilen - 1) * ncol          # Spalten mit voller Laenge
    return [eintraege[z * ncol + s] for s in range(ncol)
            for z in range(zeilen if s < voll else zeilen - 1)]


def legende_unten(ax, handles=None, labels=None, ncol: int | None = None,
                  abstand_mm: float | None = None, rand_anpassen: bool = True, **kw):
    """Legende zentriert unter der Achse `ax` (unterstes Feld), ohne Rahmen,
    zeilenweise, Spalten nach Stilregel.

    Passt die Legende nicht in die Abbildung (zentriert unter der Achsenflaeche), werden
    Spalten zusammengelegt. Mit rand_anpassen=True wird der untere Rand auf die
    tatsaechliche Legendenhoehe gesetzt (Achsenflaechen bleiben unveraendert, die
    Figurhoehe passt sich an). Ohne handles: Eintraege aller Felder derselben Spalte
    (gleicher Text nur einmal). Ohne Eintraege: keine Legende (Rueckgabe None).
    """
    fig = ax.figure
    _canvas(fig)
    x0, y0, b, _h = achse_mm(ax)
    if any(achse_mm(a)[1] < y0 - 0.01 for a in fig.axes):
        raise ValueError("legende_unten() am untersten Feld aufrufen (Legende unter der Abbildung)")
    if handles is None:                      # zweifeldrig: auch die Eintraege des oberen Felds
        gesehen: dict[str, object] = {}
        for a in fig.axes:
            if abs(achse_mm(a)[0] - x0) > 0.01:      # Feld daneben (ncols=2): eigene Legende
                continue
            for h, l in sorted(zip(*a.get_legend_handles_labels()),
                               key=lambda hl: _zeichenfolge(a, hl[0])):
                gesehen.setdefault(l, h)
        handles, labels = list(gesehen.values()), list(gesehen)
    elif labels is None:
        labels = [h.get_label() for h in handles]
    handles, labels = list(handles), list(labels)
    _formelbefehle_vorpruefen(_alle_texte(fig) + [str(l) for l in labels])
    n = len(handles)
    if n == 0:
        return None
    if ncol is None:
        ncol = S.legende_spalten(n)
    abstand_mm = _L["abstand_mm"] if abstand_mm is None else abstand_mm
    renderer = fig.canvas.get_renderer()
    fb_mm = fig.get_figwidth() / MM
    mitte = x0 + b / 2
    max_b = 2 * min(mitte - 1.0, fb_mm - mitte - 1.0) * MM * fig.dpi   # 1 mm Luft je Seite
    while True:
        leg = ax.legend(_zeilenweise(handles, ncol), _zeilenweise(labels, ncol),
                        loc="upper center", ncol=ncol,
                        bbox_to_anchor=(0.5, unter_achse(ax, abstand_mm)), **kw)
        if ncol == 1 or leg.get_window_extent(renderer).width <= max_b:
            break
        ncol -= 1
    if rand_anpassen:
        zeilen = -(-n // ncol)
        hoehe_mm = leg.get_window_extent(renderer).height / fig.dpi / MM
        noetig = max(zeilen * _L["zeile_mm"], hoehe_mm)
        _unten_anpassen(fig, ax, abstand_mm + noetig + _L["zuschlag_unten_mm"])
        leg.set_bbox_to_anchor((0.5, unter_achse(ax, abstand_mm)), transform=ax.transAxes)
    return leg


# --- Schemata ----------------------------------------------------------------------
def pfeilachsen(ax, x_max: float, y_max: float, ylabel: str | None = None,
                xlabel: str = r"Zeit $t$") -> None:
    """Achsen als Pfeile ueber die volle Achsenflaeche, ohne Gitter und Tick-Striche.

    Die Beschriftung der Zeitachse steht rechtsbuendig unter der Pfeilspitze.
    """
    for s in ax.spines.values():
        s.set_visible(False)
    ax.grid(False)
    ax.tick_params(length=0, pad=_A["ticks"]["abstand_pt"])
    ax.set_xlim(0, x_max)
    ax.set_ylim(0, y_max)
    for ziel in ((1, 0), (0, 1)):
        ax.annotate("", xy=ziel, xytext=(0, 0), xycoords="axes fraction",
                    arrowprops=PFEIL_ACHSE, annotation_clip=False)
    if xlabel:
        ax.annotate(xlabel, xy=(1, 0), xycoords="axes fraction",
                    xytext=(0, -_A["ticks"]["abstand_pt"]), textcoords="offset points",
                    ha="right", va="top", annotation_clip=False)
    if ylabel:
        ax.set_ylabel(ylabel)


def hinweis(ax, text: str, xy, xytext, **kw):
    """Beschriftung mit einheitlichem Hinweispfeil (waagerecht oder senkrecht fuehren)."""
    pfeil = dict(PFEIL_HINWEIS)
    pfeil.update(kw.pop("arrowprops", {}))
    kw.setdefault("linespacing", S.ZEILENABSTAND)
    kw.setdefault("annotation_clip", False)    # auch Ziele unter der Zeitachse (Phasenbalken)
    return ax.annotate(text, xy=xy, xytext=xytext, arrowprops=pfeil, **kw)


def phasenbalken(ax, x0: float, x1: float, text: str, y_mm: float | None = None,
                 grenzen: bool = True, **kw) -> None:
    """Massspfeil fuer eine Phase `y_mm` unter der Zeitachse mit Text darunter."""
    sc = S.SCHEMA
    y_mm = sc["phasenbalken_mm"] if y_mm is None else y_mm
    tr = xdata_ymm(ax)
    y = unter_achse(ax, y_mm)
    if grenzen:
        for xg in (x0, x1):
            ax.plot([xg, xg], [unter_achse(ax, y_mm - sc["phasengrenze_oben_mm"]),
                               unter_achse(ax, y_mm + sc["phasengrenze_unten_mm"])],
                    color=S.farbwert(_P["farbe"]), lw=_P["linie_pt"], ls="-",
                    transform=tr, clip_on=False)
    ax.annotate("", xy=(x0, y), xytext=(x1, y), xycoords=tr, arrowprops=PFEIL_MASS,
                annotation_clip=False)
    ax.text((x0 + x1) / 2, unter_achse(ax, y_mm + sc["phasentext_mm"]), text, transform=tr,
            ha="center", va="top", linespacing=S.ZEILENABSTAND, **kw)


# --- Speichern mit Pruefung ----------------------------------------------------------
def _titel_ausrichten(fig) -> None:
    """Achsentitel aller Felder in einheitlichem Abstand zur Achse."""
    for ax in fig.axes:
        if getattr(ax, "vfdb_frei", False):
            continue
        _x0, _y0, b, h = achse_mm(ax)
        if ax.get_ylabel():
            ax.yaxis.set_label_coords(-_A["titel_abstand_y_mm"] / b, 0.5)
        if ax.get_xlabel():
            ax.xaxis.set_label_coords(0.5, -_A["titel_abstand_x_mm"] / h)


@lru_cache(maxsize=4)
def _zeichenvorrat(datei: str) -> frozenset | None:
    """Unicode-Zeichen einer Schriftdatei der LaTeX-Installation (None, wenn nicht gefunden)."""
    try:
        pfad = subprocess.run(["kpsewhich", datei], capture_output=True, text=True,
                              timeout=30).stdout.strip()
        if not pfad:
            return None
        from fontTools.ttLib import TTFont
        return frozenset(TTFont(pfad).getBestCmap())
    except Exception:  # noqa: BLE001 - Pruefung ist optional
        return None


def fehlende_zeichen(text: str) -> list[str]:
    """Nicht-ASCII-Zeichen, die in der Textschrift (ausserhalb $...$) bzw. Formelschrift
    (innerhalb $...$) fehlen und deshalb im PDF verschwinden wuerden, sowie kombinierende
    Zeichen (z. B. der Punkt in einem aus Word kopierten Q mit Punkt, U+0307), die
    unzuverlaessig gesetzt werden."""
    import unicodedata
    vorrat_text = _zeichenvorrat(S.STIL["schrift"]["text_datei"])
    vorrat_formel = _zeichenvorrat(S.STIL["schrift"]["formel_datei"])
    fehlend = []
    text = unicodedata.normalize("NFC", text)   # zerlegtes ä (a + U+0308) setzt LaTeX richtig
    for i, teil in enumerate(text.split("$")):
        vorrat = vorrat_formel if i % 2 else vorrat_text
        for c in teil:
            if ord(c) <= 127 or c in fehlend:
                continue
            if unicodedata.combining(c) or (vorrat is not None and ord(c) not in vorrat):
                fehlend.append(c)
    return fehlend


_GRUPPE = r"\{(?:[^{}]|\{[^{}]*\})*\}"          # {...}, eine Verschachtelung
_FORMELBEFEHLE = re.compile(
    r"(?:[A-Za-z]_)?"                            # Index-Traeger davor: Y_\mathrm{CO}
    r"\\(?:alpha|beta|gamma|delta|epsilon|varepsilon|zeta|eta|theta|vartheta|iota|kappa|lambda|"
    r"mu|nu|xi|pi|rho|sigma|tau|upsilon|phi|varphi|chi|psi|omega|Gamma|Delta|Theta|Lambda|Xi|"
    r"Pi|Sigma|Phi|Psi|Omega|dot|ddot|bar|hat|vec|tilde|cdot|times|leq|geq|neq|approx|infty|"
    r"partial|sqrt|frac|mathrm)(?![A-Za-z])"
    r"(?:\[[^\]]*\])?"                            # Option: \sqrt[3]{x}
    rf"(?:(?:{_GRUPPE}){{1,2}}"                   # Argumente: \dot{Q}, \frac{1}{2}
    r"|\s*[A-Za-z0-9](?![A-Za-z0-9])"             # einzelnes Zeichen: \dot Q, \Delta p
    r"|\s*\\[A-Za-z]+)?"                          # Befehl: \bar\alpha
    rf"(?:[_^](?:{_GRUPPE}|\\mathrm\{{[^{{}}]*\}}|[A-Za-z0-9]))*")   # Indizes: \dot{Q}_\mathrm{max}
# Argumente von Einheiten- und Stoffbefehlen (\si{\milli\bar}, \qtyrange{0}{10}{\bar}) und
# Formeln in \(...\) bzw. \ensuremath{...} sind richtig
_EINHEITEN = re.compile(
    r"\\(?:(?:num|qty|SI)(?:list|range|product)?|si|unit|ang|ce|pu|tablenum|complexnum|complexqty)"
    rf"(?![A-Za-z])\s*(?:\[[^\]]*\]\s*)?(?:{_GRUPPE}\s*)+"
    rf"|\\\(.*?\\\)|\\ensuremath\s*{_GRUPPE}")


def formelbefehle_ausserhalb(text: str) -> list[str]:
    """Formelbefehle ausserhalb von $...$, jeweils mit Argument und Indizes, z. B.
    ['\\dot{Q}_\\mathrm{max}', 'Y_\\mathrm{CO}'] - LaTeX laesst sie dort weg oder bricht ab.
    Argumente von \\si, \\SI, \\qty..., \\ce usw. zaehlen nicht."""
    teile = re.split(r"(?<!\\)\$", _EINHEITEN.sub(" ", text))
    return [m.group(0) for i, t in enumerate(teile) if i % 2 == 0
            for m in _FORMELBEFEHLE.finditer(t)]


def _steuerzeichen(text: str, erlaubt: str = "") -> list[str]:
    """Steuerzeichen, die LaTeX nicht setzen kann. Ein Zeilenumbruch \\n ist nur ausserhalb von
    $...$ und ausserhalb von Einheiten-/Stoffargumenten erlaubt (dort entsteht er aus
    "\\si{\\newton}" ohne r)."""
    gefunden = [c for c in text if ord(c) < 32 and c != "\n" and c not in erlaubt]
    if any("\n" in m.group(0).rstrip() for m in _EINHEITEN.finditer(text)):
        gefunden.append("\n")
    if re.search(r"\n(?=um(?:list|range|product)?\s*[{\[])", text):   # "\num{800}" ohne r
        gefunden.append("\n")
    gefunden += ["\n" for i, t in enumerate(re.split(r"(?<!\\)\$", text)) if i % 2 and "\n" in t]
    return gefunden


def formel_fehler(text: str, excel: bool = False) -> str | None:
    """Meldung, wenn ein Text so nicht gesetzt werden kann (Formelbefehl ausserhalb von $...$,
    Index direkt hinter $...$, Steuerzeichen), sonst None. excel=True: Meldungen fuer
    Excel-Zellen (Tabulatoren werden dort als Leerzeichen gesetzt)."""
    steuer = _steuerzeichen(text, erlaubt="\t" if excel else "")
    if steuer and excel:
        return ("Zeilenumbruch (Alt+Enter) innerhalb von $ … $ - bitte entfernen" if steuer[0] == "\n"
                else f"Text enthält ein Steuerzeichen (U+{ord(steuer[0]):04X}) - bitte entfernen")
    if steuer and "\r\n" in text:
        return "Zeilenumbruch als \\r\\n - bitte nur \\n verwenden"
    if steuer:      # Python-Zeichenkette ohne r"...": aus "$\theta$" wird Tabulator + "heta"
        return (f"Text enthält ein Steuerzeichen ({steuer[0]!r}) - r vor dem Anführungszeichen "
                "vergessen? Texte mit \\ immer als r\"…\" schreiben, z. B. r\"$\\theta$\"")
    teile = re.split(r"(?<!\\)\$", _EINHEITEN.sub(" ", text))
    if any(i % 2 == 0 and i > 0 and t.startswith(("_", "^")) for i, t in enumerate(teile)):
        return ("Index oder Exponent direkt hinter $ … $ gehört in die Formel, z. B. "
                "$\\dot{Q}_\\mathrm{max}$ statt $\\dot{Q}$_\\mathrm{max}")
    befehle = formelbefehle_ausserhalb(text)
    if befehle:
        return f"{befehle[0]} steht außerhalb von $ … $ - bitte ${befehle[0]}$ schreiben"
    if any(i % 2 == 0 and re.search(r"(?<!\\)\^", t) for i, t in enumerate(teile)):
        return ("Hochzahl ^ außerhalb von $ … $ erscheint wörtlich (m^2) - z. B. m$^2$, m² oder "
                "\\si{\\square\\metre} schreiben")
    return None


def _formelbefehle_vorpruefen(texte) -> None:
    """Bricht mit verstaendlicher Meldung ab, bevor LaTeX an Formelbefehlen ausserhalb von
    $...$ scheitert (sonst lange Fehlerausgabe "Missing $ inserted")."""
    for text in texte:
        meldung = formel_fehler(str(text))
        if meldung:
            raise ValueError(f"{meldung} (Text: {text})")


def _alle_texte(fig) -> list[str]:
    return [t.get_text() for t in fig.findobj(Text) if t.get_visible() and t.get_text()]


def pruefen(fig, toleranz_pt: float = 0.3) -> list[str]:
    """Texte, die ueber den Figurrand ragen, sich ueberlappen oder Zeichen enthalten, die in
    der Schrift fehlen (Liste von Warnungen)."""
    _canvas(fig)
    fig.draw_without_rendering()
    r = fig.canvas.get_renderer()
    fb = fig.bbox
    tol = toleranz_pt * fig.dpi / 72
    # Tick-Beschriftungen ausserhalb der Achsgrenzen werden nicht gezeichnet -> ignorieren
    alle_ticks, gezeichnet = set(), set()

    def sichtbar(ax, achse):                  # ausgeblendete Achsen (axis("off")) zaehlen nicht
        return ax.axison and achse.get_visible()
    for ax in fig.axes:
        for achse in (ax.xaxis, ax.yaxis):
            for tick in achse.get_major_ticks() + achse.get_minor_ticks():
                alle_ticks.update((tick.label1, tick.label2))
            if sichtbar(ax, achse):
                for tick in achse._update_ticks():   # nur Ticks innerhalb der Achsgrenzen
                    gezeichnet.update((tick.label1, tick.label2))
    warnungen = []
    # Zahlenachsen ohne deutsch(): Dezimalpunkt oder "1e6" unter der Achse (nur Zahlen-
    # beschriftungen von matplotlib - Kategorien, Datum, eigene Beschriftungen bleiben aussen vor)
    for ax in fig.axes:
        for achse in (ax.xaxis, ax.yaxis):
            if not sichtbar(ax, achse):
                continue
            if isinstance(achse.get_major_formatter(), KommaFormatter) and _hat_einheiten(achse):
                warnungen.append("vs.deutsch(ax) wurde vor dem Zeichnen der Kategorien bzw. "
                                 "Datumswerte aufgerufen - die Achse zeigt Zahlen; deutsch() "
                                 "erst nach dem Zeichnen aufrufen")
                continue
            texte_achse = [t.get_text() for tick in achse._update_ticks()
                           for t in (tick.label1, tick.label2) if t.get_visible()]
            if _eigenes_format(achse):           # deutsch() laesst es stehen: Komma selbst setzen
                fremd = next((s for s in texte_achse
                              if re.search(r"\d\.\d|\d,\d{3}(?!\d)|\d[eE][+-]?\d", s)), None)
                if fremd:
                    warnungen.append(f"eigenes Achsenformat mit Dezimalpunkt bzw. Tausender- oder "
                                     f"e-Schreibweise ('{fremd}') - Komma selbst setzen, z. B. "
                                     "FuncFormatter mit vs.zahl")
                continue
            if not _zahlenachse(achse):
                continue
            versatz = achse.get_offset_text().get_text()
            punkt = next((s for s in texte_achse if re.search(r"\d\.\d", s)), None)
            if punkt or versatz:
                warnungen.append(f"Zahlen ohne Dezimalkomma-Format ('{punkt or versatz}') - "
                                 "vs.deutsch(ax) aufrufen (Farbskala: vs.deutsch(cb.ax))")
    if getattr(fig, "_vfdb_legendenplatz", False) and not fig.legends \
            and not any(a.get_legend() for a in fig.axes):
        warnungen.append("Platz für eine Legende reserviert (figur(..., legende=n)), aber keine "
                         "Legende - den Reihen label=... geben und vs.legende_unten(ax) aufrufen "
                         "oder figur(..., legende=0)")
    texte = []
    for t in fig.findobj(Text):
        if not t.get_visible() or not t.get_text().strip():
            continue
        if t in alle_ticks and t not in gezeichnet:
            continue
        for c in fehlende_zeichen(t.get_text()):
            warnungen.append(f"Zeichen '{c}' (U+{ord(c):04X}) fehlt in der Schrift und erscheint "
                             f"nicht richtig: {_kurz(t, 30)} - Formelzeichen als "
                             "$\\dot{Q}$, $\\dot{m}$, Stoffe als \\ce{CO2} schreiben")
        meldung = formel_fehler(t.get_text())
        if meldung:
            warnungen.append(f"{meldung}: {_kurz(t, 30)}")
        try:
            bb = Text.get_window_extent(t, r)
        except Exception:  # noqa: BLE001 - z. B. Text ohne Renderer
            continue
        if bb.width == 0:
            continue
        texte.append((t, bb))
        if bb.x0 < fb.x0 - tol or bb.x1 > fb.x1 + tol or bb.y0 < fb.y0 - tol or bb.y1 > fb.y1 + tol:
            warnungen.append(f"Rand: {_kurz(t, 40)} "
                             f"x {bb.x0 / fig.dpi / MM:.1f}..{bb.x1 / fig.dpi / MM:.1f} mm, "
                             f"y {bb.y0 / fig.dpi / MM:.1f}..{bb.y1 / fig.dpi / MM:.1f} mm"
                             + (_unten_hinweis(fig, (fb.y0 - bb.y0) / fig.dpi / MM)
                                if bb.y0 < fb.y0 - tol else ""))
    for (t1, b1), (t2, b2) in combinations(texte, 2):
        if b1.overlaps(b2):
            ix = min(b1.x1, b2.x1) - max(b1.x0, b2.x0)
            iy = min(b1.y1, b2.y1) - max(b1.y0, b2.y0)
            if ix > 0.5 and iy > 0.5:
                warnungen.append(f"Ueberlappung: {_kurz(t1, 30)} / {_kurz(t2, 30)}")
    # Achsentitel laenger als die Achse (zweifeldrig: Titel der Felder stossen aneinander)
    for ax in fig.axes:
        if not ax.axison:
            continue
        ab = ax.get_window_extent(r)
        for titel, laenge, soll in ((ax.yaxis.label, "height", ab.height),
                                    (ax.xaxis.label, "width", ab.width)):
            if titel.get_visible() and titel.get_text().strip():
                ist = getattr(Text.get_window_extent(titel, r), laenge)
                if ist > soll + tol:
                    warnungen.append(
                        f"Achsentitel laenger als die Achse ({ist / fig.dpi / MM:.1f} mm > "
                        f"{soll / fig.dpi / MM:.1f} mm): {_kurz(titel, 40)} - kuerzen, z. B. nur "
                        "Formelzeichen und Einheit")
    return warnungen


def _unten_hinweis(fig, ueberstand_mm: float) -> str:
    """Abhilfe fuer Texte unter der Abbildung: noetiger unterer Rand (aufgerundet)."""
    unten = min(achse_mm(a)[1] for a in fig.axes) if fig.axes else 0.0
    noetig = math.ceil(unten + ueberstand_mm + 0.5)
    return (f" - unteren Rand auf {noetig} mm vergrößern (Python: figur(..., unten={noetig})); "
            "im Excel-Weg den x-Achsentitel einzeilig schreiben")


def _marker_ganz_zeigen(fig) -> list:
    """Marker auf dem Achsenrand ganz zeichnen wie PGFPlots (matplotlib schneidet sie an der
    Achsenflaeche ab): Marker als eigene, nicht abgeschnittene Linie, nur Punkte innerhalb
    der Achsgrenzen. Gibt [(Linie, Marker, Ersatz)] zurueck - speichern stellt danach den
    alten Zustand wieder her (Legende, geaenderte Achsgrenzen beim naechsten Speichern)."""
    import numpy as np
    from matplotlib.lines import Line2D
    geaendert = []
    for ax in fig.axes:
        (x0, x1), (y0, y1) = sorted(ax.get_xlim()), sorted(ax.get_ylim())
        tx, ty = (x1 - x0) * 1e-9, (y1 - y0) * 1e-9
        for ln in list(ax.get_lines()):
            m = ln.get_marker()
            if not ln.get_visible() or not ln.get_clip_on() or m in (None, "", " ", "None", "none"):
                continue
            if ln.get_transform() != ax.transData:
                continue
            xy = np.array(ln.get_xydata(), dtype=float)   # umgerechnet (auch Datum, Kategorien)
            x, y = xy[:, 0], xy[:, 1]
            aussen = ~((x >= x0 - tx) & (x <= x1 + tx) & (y >= y0 - ty) & (y <= y1 + ty))
            xy[aussen] = np.nan                            # Indizes bleiben fuer markevery gueltig
            punkte = Line2D(xy[:, 0], xy[:, 1], linestyle="none", marker=m,
                            markevery=ln.get_markevery(),
                            markersize=ln.get_markersize(), markerfacecolor=ln.get_markerfacecolor(),
                            markeredgecolor=ln.get_markeredgecolor(),
                            markeredgewidth=ln.get_markeredgewidth(), fillstyle=ln.get_fillstyle(),
                            alpha=ln.get_alpha(), label="_nolegend_", clip_on=False,
                            zorder=max(ln.get_zorder(), 2.6),   # ueber der Achslinie wie PGFPlots
                            transform=ax.transData)
            ax.add_artist(punkte)
            ln.set_marker("None")
            geaendert.append((ln, m, punkte))
    return geaendert


def _marker_zuruecksetzen(geaendert) -> None:
    for ln, m, punkte in geaendert:
        ln.set_marker(m)
        punkte.remove()


def _canvas(fig) -> None:
    """Nach speichern (plt.close) hat die Figur keine Zeichenflaeche mehr - neu verbinden,
    damit sie ein zweites Mal gespeichert werden kann (z. B. Notebook-Zelle erneut)."""
    if not hasattr(fig.canvas, "get_renderer"):
        from matplotlib.backends.backend_pgf import FigureCanvasPgf
        FigureCanvasPgf(fig)


def _kurz(t, n: int) -> str:
    """Text fuer Meldungen, wie eingegeben (ohne doppelte Backslashes)."""
    s = t.get_text()
    return "'" + (s if len(s) <= n else s[:n] + "…") + "'"


def nachweis(fig) -> list[str]:
    """Masse der Figur und aller Achsenflaechen in mm."""
    fb, fh = fig.get_figwidth() / MM, fig.get_figheight() / MM
    zeilen = [f"Figur {fb:.1f} x {fh:.1f} mm"]
    for i, ax in enumerate(fig.axes):
        x0, y0, b, h = achse_mm(ax)
        zeilen.append(f"Feld {i + 1}: {b:.1f} x {h:.1f} mm, links {x0:.1f} mm, "
                      f"rechts {fb - x0 - b:.1f} mm, unten {y0:.1f} mm, oben {fh - y0 - h:.1f} mm")
    return zeilen


def _drucken(text: str) -> None:
    """Ausgabe, die auch bei umgeleiteter Ausgabe unter Windows nicht abbricht."""
    kodierung = getattr(sys.stdout, "encoding", None) or "utf-8"
    print(text.encode(kodierung, errors="replace").decode(kodierung, errors="replace"))


_BILDENDUNGEN = {".png", ".jpg", ".jpeg", ".svg", ".eps", ".ps", ".pgf", ".tif", ".tiff"}


def speichern(fig, ziel: str | Path, *, ausgabe: bool = True) -> Path:
    """Speichert die Figur als Vektor-PDF in fester Groesse und prueft die Beschriftung.

    ziel: Dateipfad; ohne Endung wird ".pdf" angehaengt, eine Bild-Endung (.png usw.)
    wird durch ".pdf" ersetzt. Ordner werden angelegt.
    Gibt den Pfad zurueck; Masse und Warnungen werden ausgegeben (ausgabe=True).
    """
    pfad = Path(ziel)
    if pfad.suffix.lower() in _BILDENDUNGEN:
        pfad = pfad.with_suffix(".pdf")
    elif pfad.suffix.lower() != ".pdf":
        pfad = pfad.with_name(pfad.name + ".pdf")
    _canvas(fig)
    _formelbefehle_vorpruefen(_alle_texte(fig))
    _titel_ausrichten(fig)
    geaendert = _marker_ganz_zeigen(fig)
    try:
        zeilen = nachweis(fig)
        warnungen = pruefen(fig)
        pfad.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(pfad, backend="pgf")
    finally:                                  # Figur unveraendert lassen (erneutes Speichern)
        _marker_zuruecksetzen(geaendert)
    plt.close(fig)
    if ausgabe:
        _drucken(f"{pfad}")
        for z in zeilen:
            _drucken(f"  {z}")
        for w in warnungen[:MAX_WARNUNGEN]:
            _drucken(f"  WARNUNG {w}")
        if len(warnungen) > MAX_WARNUNGEN:
            _drucken(f"  ... und {len(warnungen) - MAX_WARNUNGEN} weitere Warnungen")
    return pfad
