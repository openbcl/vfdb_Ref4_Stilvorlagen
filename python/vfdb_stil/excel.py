"""Abbildungen aus einer Excel-Arbeitsmappe erzeugen (Weg "Excel als Datenquelle").

Die Arbeitsmappe enthaelt die Blaetter:
* "Diagramm": Angaben zur Abbildung (Dateiname, Format, Achsentitel, Achsgrenzen ...)
* "Reihen":   welche Spalten als Reihen gezeichnet werden (Legendentext, Feld, Darstellung)
* "Daten":    die Werte; Zeile 1 enthaelt die Spaltenueberschriften
* "Anleitung": Kurzanleitung (wird nicht ausgewertet)

Aufruf:
    vfdb-abbildung meine_abbildung.xlsx              -> PDF neben der Excel-Datei
    vfdb-abbildung meine_abbildung.xlsx --ziel media -> PDF in den Ordner media
    vfdb-abbildung --vorlage meine_abbildung.xlsx    -> neue Vorlage (mit Beispiel) anlegen
    python -m vfdb_stil.excel ...                    -> dasselbe, falls der Befehl fehlt

Formelzeichen und Einheiten in Achsen- und Legendentexten werden wie im Leitfaden mit
LaTeX gesetzt: Formelzeichen zwischen $ ... $, Einheiten mit \\si{...}, z. B.
"Wärmefreisetzungsrate $\\dot{Q}$ in \\si{\\kilo\\watt}". Die Zeichen % & # _ duerfen
direkt geschrieben werden (z. B. "Vol.-%"); ~ ^ \\ { } haben in LaTeX eine Bedeutung.
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import math
import re
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

from . import abbildung as F
from . import stil as S

BLATT_DIAGRAMM, BLATT_REIHEN, BLATT_DATEN, BLATT_ANLEITUNG = "Diagramm", "Reihen", "Daten", "Anleitung"
FORMATE = tuple(S.FORMATE)


def _formatbeschreibung() -> str:
    teile = []
    for name, f in S.FORMATE.items():
        felder = "2 Felder je " if name == "zweifeldrig" else ""
        teile.append(f"{name} ({felder}{f['achse_b_mm']:g} x {f['achse_h_mm']:g} mm)".replace(".", ","))
    return "Achsenfläche: " + " | ".join(teile)


# (Angabe, Standardwert, Erlaeuterung) - Reihenfolge wie in der Vorlage
ANGABEN = [
    ("Dateiname", None, "Name der PDF-Datei ohne Endung, Kapitelnummer voran, z. B. "
                        "05-rauchgastemperatur. Pflichtangabe."),
    ("Format", "standard", _formatbeschreibung()),
    ("x-Spalte", None, "Spaltenüberschrift im Blatt Daten mit den x-Werten. Pflichtangabe."),
    ("x-Achsentitel", None, r"z. B. Zeit $t$ in \si{\minute}"),
    ("y-Achsentitel", None, r"Feld 1 (oben), z. B. Wärmefreisetzungsrate $\dot{Q}$ in \si{\kilo\watt} "
     r"(bei zweifeldrig nur $\dot{Q}$ in \si{\kilo\watt})"),
    ("y-Achsentitel Feld 2", None, "nur bei Format zweifeldrig (unteres Feld); bei zweifeldrig "
     f"beide y-Achsentitel kurz halten (höchstens {S.FORMATE['zweifeldrig']['achse_h_mm']:g} mm), "
     "z. B. nur $\\dot{Q}$ in \\si{\\kilo\\watt}"),
    ("x min", None, "leer = automatisch (Datenbereich)"),
    ("x max", None, "leer = automatisch; muss größer als x min sein"),
    ("x Schritt", None, f"Abstand der Teilstriche, leer = automatisch; höchstens "
                        f"{S.ACHSE['ticks']['hoechstens']} Teilstriche"),
    ("y min", None, "Feld 1; leer = automatisch"),
    ("y max", None, "Feld 1; leer = automatisch"),
    ("y Schritt", None, "Feld 1; leer = automatisch"),
    ("y min Feld 2", None, "nur zweifeldrig"),
    ("y max Feld 2", None, "nur zweifeldrig"),
    ("y Schritt Feld 2", None, "nur zweifeldrig"),
    ("Nachkommastellen x", None, "Nachkommastellen der Teilstrich-Beschriftung, leer = automatisch"),
    ("Nachkommastellen y", None, "Feld 1"),
    ("Nachkommastellen y Feld 2", None, "nur zweifeldrig"),
    ("Legende", "ja", "ja | nein. Die Legende zeigt die Legendentexte (Blatt Reihen); "
                      "mit weniger als zwei Legendentexten entfällt sie."),
]
REIHEN_SPALTEN = [
    ("Spalte", "Spaltenüberschrift im Blatt Daten"),
    ("Legendentext", "Text in der Legende; gleicher Text = gleiche Farbe (z. B. in beiden Feldern); "
                     "leer = Reihe ohne Legendeneintrag"),
    ("Feld", "1 oder 2 (2 nur bei Format zweifeldrig); leer = 1"),
    ("Darstellung", "Linie | Punkte | Linie und Punkte; leer = Linie"),
    ("Farbe Nr.", f"1 bis {len(S.FARBEN)} nach Stilvorgaben; leer = nächste freie Farbe"),
]
DARSTELLUNGEN = ("linie", "punkte", "linie und punkte")
ANLEITUNG = [
    "So entsteht die Abbildung",
    "1. Blatt Daten: Zeile 1 Spaltenüberschriften, darunter nur Zahlen (Dezimalkomma wie in Excel üblich).",
    "2. Blatt Reihen: je Kurve eine Zeile (Spalte aus Blatt Daten, Legendentext, Feld, Darstellung).",
    "3. Blatt Diagramm: Dateiname, Format, x-Spalte und Achsentitel eintragen.",
    "4. Datei in Excel speichern (Formeln werden dabei berechnet) und schließen.",
    "5. Eingabeaufforderung im Ordner der Datei öffnen (Explorer: in die Adresszeile cmd tippen, Enter). "
    "Bei Ordnern auf einem Netzwerkpfad (\\\\server\\…) geht das nicht: dann die Excel-Datei mit der Maus "
    "auf Abbildung_erzeugen.bat ziehen (siehe docs/Installation.md).",
    "6. Befehl: vfdb-abbildung NAME-DIESER-EXCEL-DATEI.xlsx   (Dauer ca. 20 s; das PDF entsteht im "
    "selben Ordner und heißt wie die Angabe Dateiname)",
    "",
    "Achsentitel und Legendentexte",
    "Formelzeichen zwischen $ … $, z. B. Gastemperatur $T$ in °C oder $\\dot{Q}$ für Q mit Punkt.",
    "Einheiten wahlweise direkt (°C, kW) oder mit \\si{\\kilo\\watt}; beschreibende Indizes aufrecht: "
    "$Y_\\mathrm{CO}$, $\\dot{Q}_\\mathrm{max}$; Stoffe: \\ce{CO2}.",
    "Sonderzeichen wie Q̇, ṁ, CO₂ nicht aus Word kopieren (sie fehlen in der Schrift), sondern wie oben schreiben.",
    "Die Zeichen % & # _ dürfen direkt geschrieben werden. Vorsicht mit ~ ^ \\ { } außerhalb von $ … $.",
    "",
    "Anleitung mit allen Angaben: docs/Excel.md im Repository vfdb_Ref4_Stilvorlagen.",
]


class ExcelFehler(ValueError):
    """Fehler in den Angaben der Arbeitsmappe (Meldung fuer Anwender)."""


@dataclass
class Reihe:
    spalte: str
    legende: str | None
    feld: int
    darstellung: str
    farbe_nr: int | None
    zeile: int


# --- Text ---------------------------------------------------------------------------
def latex_text(s: str | None) -> str:
    """Maskiert & # _ ausserhalb von $ ... $ und ausserhalb von {...} (Befehlsargumente wie
    \\ce{CO_2} bleiben unveraendert); % und ^ maskiert das pgf-Backend selbst. Tabulatoren
    (beim Einfuegen aus Word/PDF mitkopiert) werden zu Leerzeichen."""
    if not s:
        return ""
    s = str(s).replace("\t", " ")
    aus, mathe, tiefe, i = [], False, 0, 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):          # Befehl oder bereits maskiertes Zeichen
            aus.append(s[i:i + 2])
            i += 2
            continue
        if c == "$":
            mathe = not mathe
        elif c == "{":
            tiefe += 1
        elif c == "}":
            tiefe = max(0, tiefe - 1)
        elif c in "&#_" and not mathe and tiefe == 0:
            aus.append("\\" + c)
            i += 1
            continue
        aus.append(c)
        i += 1
    return "".join(aus)


def text_pruefen(s, ort: str) -> None:
    """Grobe Vorpruefung eines Achsen-/Legendentexts: $ paarweise, { } ausgeglichen."""
    if not s:
        return
    ohne = re.sub(r"\\.", "", str(s))                 # \$ \{ \} usw. zaehlen nicht
    if ohne.count("$") % 2:
        raise ExcelFehler(f"{ort}: $ … $ nicht paarweise (Text: {s})")
    tiefe = 0
    for c in ohne:
        tiefe += {"{": 1, "}": -1}.get(c, 0)
        if tiefe < 0:
            break
    if tiefe != 0:
        raise ExcelFehler(f"{ort}: geschweifte Klammern {{ }} nicht ausgeglichen (Text: {s})")
    if "\\(" in str(s):                               # latex_text kennt nur $ als Formelgrenze
        raise ExcelFehler(f"{ort}: bitte $ … $ statt \\( … \\) schreiben (Text: {s})")
    meldung = F.formel_fehler(str(s), excel=True)
    if meldung:
        raise ExcelFehler(f"{ort}: {meldung} (Text: {s})")


# --- Lesen --------------------------------------------------------------------------
def _schluessel(s) -> str:
    return re.sub(r"\s+", " ", "" if s is None else str(s)).strip().lower()


_TAUSENDER = re.compile(r"^-?[1-9]\d{0,2}(\.\d{3})+$")


def _klartext(x: float) -> str:
    """Zahl fuer Meldungen (ohne LaTeX)."""
    return f"{x:g}".replace("-", "−").replace(".", ",")


_UNGUELTIG_IM_DATEINAMEN = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _zahl(wert, ort: str) -> float | None:
    """Zelle -> Zahl; leer -> None; verstaendliche Meldung sonst."""
    if wert is None or (isinstance(wert, str) and not wert.strip()):
        return None
    if isinstance(wert, bool):
        raise ExcelFehler(f"{ort}: WAHR/FALSCH ist keine Zahl")
    if isinstance(wert, (dt.datetime, dt.date, dt.time, dt.timedelta)):
        raise ExcelFehler(f"{ort}: Datum/Uhrzeit ({wert}) wird nicht unterstützt - bitte als "
                          "Zahl angeben, z. B. Minuten oder Sekunden")
    if isinstance(wert, (int, float)):
        x = float(wert)
    else:
        text = str(wert).strip().replace("−", "-").replace(" ", "")
        if text.startswith("#"):
            raise ExcelFehler(f"{ort}: Excel-Fehlerwert {text} statt einer Zahl")
        if _TAUSENDER.match(text):
            raise ExcelFehler(f"{ort}: {wert!r} ist mehrdeutig (Tausenderpunkt oder Dezimalpunkt?) "
                              "- bitte als Zahl ohne Tausenderpunkt eingeben")
        try:
            x = float(text.replace(",", "."))
        except ValueError:
            raise ExcelFehler(f"{ort}: {wert!r} ist keine Zahl") from None
    if not math.isfinite(x):
        raise ExcelFehler(f"{ort}: {wert!r} ist keine endliche Zahl")
    return x


def _ganzzahl(wert, ort: str, erlaubt) -> int | None:
    x = _zahl(wert, ort)
    if x is None:
        return None
    if x != int(x) or int(x) not in erlaubt:
        raise ExcelFehler(f"{ort}: {wert!r} ist nicht erlaubt (erlaubt: "
                          f"{', '.join(str(e) for e in erlaubt)})")
    return int(x)


def _blatt(wb, name: str):
    for ws in wb.worksheets:
        if _schluessel(ws.title) == _schluessel(name):
            return ws
    raise ExcelFehler(f"Blatt {name!r} fehlt (vorhanden: {', '.join(wb.sheetnames)})")


def angaben_lesen(wb) -> tuple[dict[str, object], dict[str, str]]:
    """Angaben und ihre Zellen (fuer Fehlermeldungen)."""
    ws = _blatt(wb, BLATT_DIAGRAMM)
    bekannt = {_schluessel(a): a for a, _s, _e in ANGABEN}
    werte = {a: s for a, s, _e in ANGABEN}
    zellen: dict[str, str] = {}
    for nr, zeile in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if not zeile or zeile[0] is None:
            continue
        k = _schluessel(zeile[0])
        if k not in bekannt:
            raise ExcelFehler(f"Blatt Diagramm, Zeile {nr}: unbekannte Angabe {zeile[0]!r}")
        wert = zeile[1] if len(zeile) > 1 else None
        zellen[bekannt[k]] = f"Blatt Diagramm, {bekannt[k]} (B{nr})"
        if wert is not None and not (isinstance(wert, str) and not wert.strip()):
            werte[bekannt[k]] = wert.strip() if isinstance(wert, str) else wert
    return werte, zellen


def reihen_lesen(wb, format_: str) -> list[Reihe]:
    ws = _blatt(wb, BLATT_REIHEN)
    kopf = [_schluessel(c.value) for c in ws[1]]
    try:
        idx = {name: kopf.index(_schluessel(name)) for name, _e in REIHEN_SPALTEN}
    except ValueError as e:
        raise ExcelFehler(f"Blatt Reihen: Spaltenüberschriften müssen lauten: "
                          f"{', '.join(n for n, _e in REIHEN_SPALTEN)}") from e
    reihen = []
    for nr, zeile in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        def zelle(name):
            i = idx[name]
            return zeile[i] if i < len(zeile) else None
        if zelle("Spalte") in (None, ""):
            continue
        felder = (1, 2) if format_ == "zweifeldrig" else (1,)
        feld = _ganzzahl(zelle("Feld"), f"Blatt Reihen, Zeile {nr}, Feld", felder) or 1
        darst = _schluessel(zelle("Darstellung") or "Linie")
        if darst not in DARSTELLUNGEN:
            raise ExcelFehler(f"Blatt Reihen, Zeile {nr}: Darstellung {zelle('Darstellung')!r} "
                              "(erlaubt: Linie, Punkte, Linie und Punkte)")
        fnr = _ganzzahl(zelle("Farbe Nr."), f"Blatt Reihen, Zeile {nr}, Farbe Nr.",
                        range(1, len(S.FARBEN) + 1))
        leg = zelle("Legendentext")
        # Tabulatoren/mehrfache Leerzeichen wie ein Leerzeichen (gleicher Text = gleiche Farbe)
        leg = re.sub(r"[ \t]+", " ", str(leg)).strip() if leg is not None else None
        reihen.append(Reihe(_name(zelle("Spalte")), leg or None,
                            feld, darst, fnr, nr))
    if not reihen:
        raise ExcelFehler("Blatt Reihen: keine Reihe angegeben")
    return reihen


def _formel_ohne_wert(wsf, nr: int, sp: int) -> bool:
    if wsf is None:
        return False
    f = wsf.cell(nr, sp).value
    return (isinstance(f, str) and f.startswith("=")) or type(f).__name__ == "ArrayFormula"


def _ohne_wert(c, wsf) -> bool:
    """Formelzelle ohne gespeicherten Wert. Ein leeres Textergebnis (=WENN(...;"";...)) speichert
    Excel als Typ "str" ohne Wert - das ist eine leere Zelle, kein fehlender Wert."""
    return c.value is None and c.data_type != "str" and _formel_ohne_wert(wsf, c.row, c.column)


def _name(s) -> str:
    """Spaltenname fuer den Abgleich: Zeilenumbrueche (Alt+Enter) und mehrfache Leerzeichen
    wie ein Leerzeichen."""
    return re.sub(r"\s+", " ", str(s)).strip()


def formeln_pruefen(wb, wb_formeln, blatt: str) -> None:
    """Formeln ohne gespeicherten Wert in einem Angaben-Blatt melden."""
    if wb_formeln is None:
        return
    ws, wsf = _blatt(wb, blatt), _blatt(wb_formeln, blatt)
    for zeile in ws.iter_rows():
        for c in zeile:
            if _ohne_wert(c, wsf):
                raise ExcelFehler(f"Blatt {blatt}, Zelle {c.coordinate}: Formel ohne berechneten "
                                  "Wert - die Datei in Excel öffnen, speichern und erneut versuchen")


def daten_lesen(wb, wb_formeln=None, benoetigt=None) -> dict[str, np.ndarray]:
    """Spalten des Blatts Daten (nur die Spalten in `benoetigt`, sonst alle); wb_formeln
    (ohne data_only geladen) erkennt Formeln ohne gespeicherten Wert."""
    ws = _blatt(wb, BLATT_DATEN)
    wsf = _blatt(wb_formeln, BLATT_DATEN) if wb_formeln is not None else None
    kopf = [_name(c.value) if c.value is not None else None for c in ws[1]]
    gesehen: dict[str, str] = {}
    for i, k in enumerate(kopf):
        if not k:
            continue
        buchstabe = ws.cell(1, i + 1).column_letter
        if k in gesehen:
            raise ExcelFehler(f"Blatt Daten: Spaltenüberschrift {k!r} doppelt "
                              f"(Spalten {gesehen[k]} und {buchstabe})")
        gesehen[k] = buchstabe
    lesen = [(i, k) for i, k in enumerate(kopf) if k and (benoetigt is None or k in benoetigt)]
    spalten: dict[str, list[float]] = {k: [] for _i, k in lesen}
    for zeile in ws.iter_rows(min_row=2):
        if all(zeile[i].value is None and not _ohne_wert(zeile[i], wsf)
               for i, _k in lesen if i < len(zeile)):
            continue
        for i, k in lesen:
            if i >= len(zeile):
                spalten[k].append(math.nan)
                continue
            c = zeile[i]
            wert, ort = c.value, f"Blatt Daten, Zelle {c.coordinate}"
            if _ohne_wert(c, wsf):
                raise ExcelFehler(f"{ort}: Formel ohne berechneten Wert - die Datei in Excel "
                                  "öffnen, speichern und erneut versuchen")
            if c.data_type == "e" and str(wert).upper() == "#N/A":
                wert = None                   # =NV(): in Excel-Diagrammen ueblich fuer Luecken
            v = _zahl(wert, ort)
            spalten[k].append(math.nan if v is None else v)
    ergebnis = {k: np.asarray(v, dtype=float) for k, v in spalten.items()}
    for k in kopf:                       # nicht gelesene Spalten nur als Name fuehren
        if k and k not in ergebnis:
            ergebnis[k] = None
    return ergebnis


# --- Zeichnen -----------------------------------------------------------------------
def _achse_einrichten(ax, achse: str, vmin, vmax, schritt, ort: str) -> None:
    vmin, vmax = _zahl(vmin, f"{ort} min"), _zahl(vmax, f"{ort} max")
    schritt = _zahl(schritt, f"{ort} Schritt")
    setze = ax.set_xlim if achse == "x" else ax.set_ylim
    lies = ax.get_xlim if achse == "x" else ax.get_ylim
    if vmin is not None or vmax is not None:
        lo, hi = lies()
        lo, hi = (lo if vmin is None else vmin), (hi if vmax is None else vmax)
        if lo >= hi:
            raise ExcelFehler(f"{ort}: min ({_klartext(lo)}) muss kleiner als max ({_klartext(hi)}) sein")
        setze(lo, hi)
    if schritt is not None:
        if schritt <= 0:
            raise ExcelFehler(f"{ort} Schritt muss positiv sein")
        lo, hi = lies()
        anzahl = math.floor((hi - lo) / schritt + 1e-9) + 1
        grenze = S.ACHSE["ticks"]["hoechstens"]
        if anzahl > grenze:
            raise ExcelFehler(f"{ort} Schritt {_klartext(schritt)} ergibt {anzahl} Teilstriche "
                              f"(höchstens {grenze}) - größeren Schritt wählen")
        start = math.ceil(lo / schritt - 1e-9)
        ticks = np.round(np.arange(start, start + anzahl) * schritt, 12)
        ticks = ticks[(ticks >= lo - 1e-9 * schritt) & (ticks <= hi + 1e-9 * schritt)]
        (ax.set_xticks if achse == "x" else ax.set_yticks)(ticks)
        setze(lo, hi)


def _nk(wert, ort) -> int | None:
    return _ganzzahl(wert, ort, range(0, 11))


def _farben_vergeben(reihen: list[Reihe]) -> dict[str, int]:
    """Farbindex je Legendentext (bzw. Spalte): ausdrueckliche Farbe Nr. hat Vorrang,
    die uebrigen bekommen die naechste freie Farbe in fester Reihenfolge."""
    def schluessel(r):
        return r.legende or r.spalte
    fest: dict[str, int] = {}
    for r in reihen:
        if r.farbe_nr is None:
            continue
        k = schluessel(r)
        if k in fest and fest[k] != r.farbe_nr - 1:
            raise ExcelFehler(f"Blatt Reihen, Zeile {r.zeile}: {k!r} hat zwei verschiedene Farben")
        andere = [kk for kk, v in fest.items() if v == r.farbe_nr - 1 and kk != k]
        if andere:
            raise ExcelFehler(f"Blatt Reihen, Zeile {r.zeile}: Farbe Nr. {r.farbe_nr} ist schon "
                              f"für {andere[0]!r} vergeben")
        fest[k] = r.farbe_nr - 1
    farben = dict(fest)
    frei = [i for i in range(len(S.FARBEN)) if i not in fest.values()]
    for r in reihen:
        k = schluessel(r)
        if k not in farben:
            if not frei:
                raise ExcelFehler(f"mehr als {len(S.FARBEN)} verschiedene Reihen - Reihen "
                                  "zusammenfassen oder auf zwei Abbildungen verteilen")
            farben[k] = frei.pop(0)
    return farben


def abbildung_aus_excel(datei: str | Path, ziel: str | Path | None = None,
                        ausgabe: bool = True) -> Path:
    """Erzeugt die Abbildung aus der Arbeitsmappe und gibt den PDF-Pfad zurueck."""
    datei = Path(datei)
    if not datei.exists():
        raise FileNotFoundError(datei)
    if datei.suffix.lower() not in (".xlsx", ".xlsm"):
        raise ExcelFehler("bitte als Excel-Arbeitsmappe (.xlsx) speichern")
    wb = load_workbook(datei, data_only=True)
    wb_formeln = load_workbook(datei, data_only=False)
    for blatt in (BLATT_DIAGRAMM, BLATT_REIHEN):
        formeln_pruefen(wb, wb_formeln, blatt)
    a, zellen = angaben_lesen(wb)
    format_ = _schluessel(a["Format"])
    if format_ not in FORMATE:
        raise ExcelFehler(f"Format {a['Format']!r} (erlaubt: {', '.join(FORMATE)})")
    for pflicht in ("Dateiname", "x-Spalte"):
        if not a[pflicht]:
            raise ExcelFehler(f"Blatt Diagramm: Angabe {pflicht!r} fehlt")
    dateiname = re.sub(r"\.(pdf|png|jpe?g|svg|eps|tiff?)$", "", str(a["Dateiname"]).strip(), flags=re.I)
    if _UNGUELTIG_IM_DATEINAMEN.search(dateiname) or dateiname.endswith((".", " ")):
        raise ExcelFehler(f"{zellen.get('Dateiname', 'Blatt Diagramm, Dateiname')}: "
                          f"{dateiname!r} ist als Dateiname nicht möglich "
                          '(nicht erlaubt: < > : " / \\ | ? * sowie Punkt oder Leerzeichen am Ende)')
    for angabe in ("x-Achsentitel", "y-Achsentitel", "y-Achsentitel Feld 2"):
        text_pruefen(a[angabe], zellen.get(angabe, f"Blatt Diagramm, {angabe}"))
    reihen = reihen_lesen(wb, format_)
    for r in reihen:
        text_pruefen(r.legende, f"Blatt Reihen, Legendentext (Zeile {r.zeile})")
    xs = _name(a["x-Spalte"])
    daten = daten_lesen(wb, wb_formeln, benoetigt={xs, *(r.spalte for r in reihen)})
    for name in [xs] + [r.spalte for r in reihen]:
        if name not in daten:
            raise ExcelFehler(f"Spalte {name!r} fehlt im Blatt Daten (vorhanden: {', '.join(daten)})")
    x = daten[xs]
    if not np.isfinite(x).any():
        raise ExcelFehler(f"Blatt Daten: Spalte {xs!r} enthält keine Zahlen")
    for r in reihen:
        if not (np.isfinite(x) & np.isfinite(daten[r.spalte])).any():
            raise ExcelFehler(f"Blatt Daten: Spalte {r.spalte!r} enthält keine Zahlen "
                              f"(Blatt Reihen, Zeile {r.zeile})")
    if format_ == "zweifeldrig" and not any(r.feld == 2 for r in reihen):
        raise ExcelFehler("Format zweifeldrig: keine Reihe für Feld 2 (Blatt Reihen, Spalte Feld)")

    farben = _farben_vergeben(reihen)
    eintraege = list(dict.fromkeys(r.legende for r in reihen if r.legende))
    legende_an = (_schluessel(a["Legende"]) not in ("nein", "n", "0", "false", "falsch")
                  and len(eintraege) >= 2)

    texte: dict[str, str] = {}                 # LaTeX-Text -> Ort (fuer Fehlermeldungen)
    ziel = datei.parent if ziel is None else Path(ziel)
    fig, axs = F.figur(format_, legende=len(eintraege) if legende_an else 0,
                       sharex=format_ == "zweifeldrig")
    try:
        return _zeichnen(fig, axs, a, zellen, reihen, daten, x, farben, legende_an, texte,
                         ziel / f"{dateiname}.pdf", ausgabe)
    except ExcelFehler:
        raise
    except (ValueError, RuntimeError) as e:
        meldung = str(e)
        # LaTeX konnte einen Text nicht messen (ValueError) oder nicht setzen (RuntimeError)
        if "Error measuring" in meldung or "LaTeX" in meldung or "\n!" in meldung:
            raise ExcelFehler(_latex_meldung(meldung, texte)) from None
        raise
    finally:
        F.plt.close(fig)


def _zeichnen(fig, axs, a, zellen, reihen, daten, x, farben, legende_an, texte, pdf, ausgabe):
    def text(original, ort):
        t = latex_text(original)
        if t:
            texte[t] = ort
        return t

    felder = list(np.atleast_1d(axs))
    for r in reihen:
        i = farben[r.legende or r.spalte]
        stil = dict(color=S.farbe(i))
        if r.darstellung == "punkte":
            stil.update(linestyle="none", marker="o")
        else:
            stil.update(linestyle=S.linienstil(i))
            if r.darstellung == "linie und punkte":
                stil.update(marker="o")
        y = daten[r.spalte]
        gueltig = ~(np.isnan(x) | np.isnan(y)) if r.darstellung == "punkte" else slice(None)
        felder[r.feld - 1].plot(x[gueltig], y[gueltig],
                                label=text(r.legende, f"Blatt Reihen, Legendentext (Zeile {r.zeile})")
                                or None, **stil)

    unten = felder[-1]
    unten.set_xlabel(text(a["x-Achsentitel"], zellen.get("x-Achsentitel", "x-Achsentitel")))
    felder[0].set_ylabel(text(a["y-Achsentitel"], zellen.get("y-Achsentitel", "y-Achsentitel")))
    if len(felder) == 2:
        felder[1].set_ylabel(text(a["y-Achsentitel Feld 2"],
                                  zellen.get("y-Achsentitel Feld 2", "y-Achsentitel Feld 2")))
        felder[0].tick_params(labelbottom=False)
    for k, ax in enumerate(felder):
        suffix = "" if k == 0 else " Feld 2"
        _achse_einrichten(ax, "y", a[f"y min{suffix}"], a[f"y max{suffix}"],
                          a[f"y Schritt{suffix}"], f"Blatt Diagramm, y{suffix}")
        F.deutsch(ax, _nk(a["Nachkommastellen x"], "Blatt Diagramm, Nachkommastellen x"),
                  _nk(a[f"Nachkommastellen y{suffix}"], f"Blatt Diagramm, Nachkommastellen y{suffix}"))
    _achse_einrichten(unten, "x", a["x min"], a["x max"], a["x Schritt"], "Blatt Diagramm, x")

    if legende_an:
        griffe, beschriftungen = [], []
        for ax in felder:
            for h, t in zip(*ax.get_legend_handles_labels()):
                if t not in beschriftungen:
                    griffe.append(h)
                    beschriftungen.append(t)
        F.legende_unten(unten, griffe, beschriftungen)
    return F.speichern(fig, pdf, ausgabe=ausgabe)


def _latex_meldung(meldung: str, texte: dict[str, str]) -> str:
    """Verstaendliche Meldung zu einem LaTeX-Fehler beim Setzen eines Textes."""
    grund = next((z[1:].strip() for z in meldung.splitlines() if z.startswith("!")), "")
    ort = next((o for t, o in sorted(texte.items(), key=lambda kv: -len(kv[0])) if t in meldung), None)
    teil = f" ({grund})" if grund else ""
    if ort:
        return (f"{ort}: LaTeX kann den Text nicht setzen{teil}. Bitte $ … $ paarweise setzen und "
                "\\si{…}, \\dot{…} usw. prüfen.")
    return f"LaTeX-Fehler{teil}. Bitte Achsentitel und Legendentexte prüfen."


# --- Vorlage ------------------------------------------------------------------------
BEISPIEL = {
    "angaben": {"Dateiname": "00-beispiel", "x-Spalte": "t",
                "x-Achsentitel": r"Zeit $t$ in \si{\minute}",
                "y-Achsentitel": r"Gastemperatur $T$ in \si{\degreeCelsius}",
                "x min": 0, "x max": 10, "x Schritt": 2, "y min": 0, "y max": 100, "y Schritt": 20},
    "reihen": [["Messung A", "Messung A", 1, "Linie", None],
               ["Messung B", "Messung B", 1, "Linie und Punkte", None]],
    "daten": {"t": [0, 2, 4, 6, 8, 10], "Messung A": [20, 45, 62, 74, 83, 90],
              "Messung B": [20, 34, 46, 55, 63, 70]},
}


def vorlage_schreiben(pfad: str | Path, beispiel: dict | None = None) -> Path:
    """Schreibt eine Excel-Vorlage, gefuellt mit `beispiel` (Standard: kleines Beispiel).

    beispiel = {"angaben": {Angabe: Wert}, "reihen": [[Spalte, Legende, Feld, Darstellung, Farbe]],
                "daten": {Spaltenname: [Werte]}}
    """
    beispiel = BEISPIEL if beispiel is None else beispiel
    blau = S.FARBEN[0].lstrip("#")
    kopf_font, kopf_fill = Font(bold=True, color="FFFFFF"), PatternFill("solid", fgColor=blau)
    wb = Workbook()
    ws = wb.active
    ws.title = BLATT_DIAGRAMM
    ws.append(["Angabe", "Wert", "Erläuterung"])
    for a, standard, erl in ANGABEN:
        ws.append([a, beispiel.get("angaben", {}).get(a, standard), erl])
    for spalte, breite in zip("ABC", (26, 48, 90)):
        ws.column_dimensions[spalte].width = breite
    zeile_von = {a: i + 2 for i, (a, _s, _e) in enumerate(ANGABEN)}

    def auswahl(blatt, formel, zellen, titel, text):
        dv = DataValidation(type="list", formula1=formel, allow_blank=True, showErrorMessage=True,
                            errorTitle=titel, error=text)
        blatt.add_data_validation(dv)
        dv.add(zellen)

    auswahl(ws, '"' + ",".join(FORMATE) + '"', f"B{zeile_von['Format']}", "Format",
            "Bitte ein Format aus der Liste wählen.")
    auswahl(ws, '"ja,nein"', f"B{zeile_von['Legende']}", "Legende", "Bitte ja oder nein wählen.")

    wr = wb.create_sheet(BLATT_REIHEN)
    wr.append([n for n, _e in REIHEN_SPALTEN])
    for zeile in beispiel.get("reihen", []):
        wr.append(list(zeile))
    for i, (_n, _erl) in enumerate(REIHEN_SPALTEN):
        wr.column_dimensions[chr(65 + i)].width = 22 if i != 1 else 40
    auswahl(wr, '"1,2"', "C2:C200", "Feld", "Feld 1 oder 2 (2 nur bei Format zweifeldrig).")
    auswahl(wr, '"Linie,Punkte,Linie und Punkte"', "D2:D200", "Darstellung",
            "Bitte Linie, Punkte oder Linie und Punkte wählen.")
    auswahl(wr, '"' + ",".join(str(i) for i in range(1, len(S.FARBEN) + 1)) + '"', "E2:E200",
            "Farbe Nr.", f"Bitte eine Zahl von 1 bis {len(S.FARBEN)} wählen oder leer lassen.")
    wr.cell(1, 7, "Hinweise").font = Font(bold=True)
    for k, (n, erl) in enumerate(REIHEN_SPALTEN, start=2):
        wr.cell(k, 7, f"{n}: {erl}")
    wr.column_dimensions["G"].width = 100

    wd = wb.create_sheet(BLATT_DATEN)
    daten = beispiel.get("daten", {})
    namen = list(daten) or ["x", "y1"]
    wd.append(namen)
    for werte in zip(*(daten[n] for n in namen)) if daten else []:
        wd.append([None if (isinstance(v, float) and math.isnan(v)) else v for v in werte])

    wa = wb.create_sheet(BLATT_ANLEITUNG)
    for z in ANLEITUNG:
        wa.append([z])
    for z in (1, ANLEITUNG.index("Achsentitel und Legendentexte") + 1):
        wa.cell(z, 1).font = Font(bold=True)
    wa.column_dimensions["A"].width = 120

    for blatt in (ws, wr, wd):
        for c in blatt[1]:
            if c.value is not None and not (blatt is wr and c.column == 7):
                c.font, c.fill = kopf_font, kopf_fill
        blatt.freeze_panes = "A2"
    for zeile in ws.iter_rows(min_row=2):
        zeile[2].alignment = Alignment(wrap_text=True, vertical="top")
    wb.properties.creator = "vfdb Referat 4"
    pfad = Path(pfad)
    pfad.parent.mkdir(parents=True, exist_ok=True)
    wb.save(pfad)
    return pfad


# --- Kommandozeile --------------------------------------------------------------------
def _meldung(e: BaseException) -> str:
    """Verstaendliche Meldung fuer Fehler ausserhalb der Arbeitsmappen-Pruefung."""
    from openpyxl.utils.exceptions import InvalidFileException
    if isinstance(e, ExcelFehler):
        return str(e)
    if isinstance(e, FileNotFoundError):
        return "Datei nicht gefunden"
    if isinstance(e, PermissionError):
        return ("Datei kann nicht geschrieben werden - ist das PDF (oder die Excel-Datei) noch "
                "in einem Programm geöffnet?")
    if isinstance(e, (InvalidFileException, zipfile.BadZipFile)):
        return ("keine gültige Excel-Arbeitsmappe - bitte in Excel als .xlsx speichern "
                "(ohne Kennwortschutz)")
    if isinstance(e, IsADirectoryError):
        return "das ist ein Ordner, keine Datei"
    text = str(e)
    if "lualatex" in text.lower() and "not found" in text.lower():
        return "LuaLaTeX nicht gefunden - siehe Installationsanleitung (docs/Installation.md)"
    return f"unerwarteter Fehler ({type(e).__name__}: {text.splitlines()[0] if text else ''})"


def main(argv: list[str] | None = None) -> int:
    for strom in (sys.stdout, sys.stderr):
        if hasattr(strom, "reconfigure"):
            strom.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(prog="vfdb-abbildung",
                                description="Abbildung im Leitfaden-Stil aus einer Excel-Arbeitsmappe erzeugen")
    p.add_argument("datei", nargs="*", help="Excel-Arbeitsmappe(n) (.xlsx)")
    p.add_argument("--ziel", help="Ordner für die PDF-Dateien (Standard: neben der Excel-Datei)")
    p.add_argument("--vorlage", metavar="PFAD", help="neue Vorlage (mit kleinem Beispiel) an PFAD anlegen")
    p.add_argument("--ueberschreiben", action="store_true", help="mit --vorlage: vorhandene Datei ersetzen")
    a = p.parse_args(argv)
    if not a.datei and not a.vorlage:
        p.print_help()
        return 2
    fehler = 0
    if a.vorlage:
        vorlage = Path(a.vorlage)
        if vorlage.suffix.lower() != ".xlsx":
            vorlage = vorlage.with_name(vorlage.name + ".xlsx")
        if vorlage.exists() and not a.ueberschreiben:
            print(f"FEHLER: {vorlage} gibt es schon (zum Ersetzen --ueberschreiben angeben)",
                  file=sys.stderr)
            fehler += 1
        else:
            try:                              # PDF-Name = Name der Excel-Datei
                beispiel = {**BEISPIEL, "angaben": {**BEISPIEL["angaben"], "Dateiname": vorlage.stem}}
                print(vorlage_schreiben(vorlage, beispiel))
            except Exception as e:  # noqa: BLE001
                print(f"FEHLER: {vorlage}: {_meldung(e)}", file=sys.stderr)
                fehler += 1
    dateien: list[str] = []
    for muster in a.datei:                    # Platzhalter auch unter Windows
        if Path(muster).exists():             # auch Namen mit [ ] (sonst Platzhalter)
            treffer = [muster]
        elif Path(muster + ".xlsx").is_file():
            treffer = [muster + ".xlsx"]      # Explorer blendet Endungen aus
        elif any(c in muster for c in "*?["):   # nur Arbeitsmappen, ohne Sperrdateien (~$name.xlsx)
            treffer = sorted(t for t in glob.glob(muster) if not Path(t).name.startswith("~$")
                             and Path(t).suffix.lower() in (".xlsx", ".xlsm"))
        else:
            treffer = [muster]
        if not treffer:
            print(f"FEHLER: keine Datei passt zu {muster}", file=sys.stderr)
            fehler += 1
        dateien += treffer
    namen: dict[str, str] = {}
    for d in dateien:
        try:
            pdf = abbildung_aus_excel(d, a.ziel)
            if str(pdf).lower() in namen:
                print(f"WARNUNG: {d} hat dasselbe PDF erzeugt wie {namen[str(pdf).lower()]} "
                      f"({pdf.name}) - Angabe Dateiname prüfen", file=sys.stderr)
            namen[str(pdf).lower()] = d
        except Exception as e:  # noqa: BLE001 - jede Datei einzeln melden, dann weiter
            print(f"FEHLER in {d}: {_meldung(e)}", file=sys.stderr)
            fehler += 1
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
