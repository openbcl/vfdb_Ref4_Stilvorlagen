"""Erzeugt die Office-Vorlagen aus stil/stil.yaml (Windows mit Microsoft Office).

    python office/erzeuge_office.py            # Vorlagen erzeugen
    python office/erzeuge_office.py --test     # zusaetzlich Test-PDFs nach office/test/

Voraussetzungen (nur fuer Pflegende): Microsoft Office (Excel, PowerPoint), LuaLaTeX,
pip install -e ".[office]"  (pywin32; PyMuPDF zum Messen der PDFs, Lizenz AGPL-3.0).
Excel und PowerPoint duerfen waehrend des Laufs nicht geoeffnet sein.

Erzeugt in office/:
* vfdb_Leitfaden.thmx                  Office-Design: Farben und Schrift
* vfdb_Abbildung_<format>.potx         PowerPoint-Vorlage je Format: Foliengroesse = Abbildung,
                                       Fuehrungslinien an der Achsenflaeche
* vfdb_Diagramm.crtx                   Excel-Diagrammvorlage (Punkt (XY) mit Linien, 8 Reihen)
* vfdb_Diagramm_<format>.xlsx          Excel-Arbeitsmappe mit fertig formatiertem Diagramm

Achsenflaeche, Achsentitel und Legende werden kalibriert: Das Skript fuegt das Diagramm wie
ein Anwender in die PowerPoint-Vorlage ein, speichert ein PDF, misst darin die Lage und
korrigiert die Excel-Werte. Bezug fuer Titel und Legende ist eine Python-Abbildung (vfdb_stil)
gleichen Formats.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from vfdb_stil import stil as S

OFFICE = Path(__file__).resolve().parent
AUSGABE = OFFICE                     # waehrend des Laufs ein temporaerer Ordner (siehe main)
PT = 72 / 25.4                       # mm -> pt
MM = 25.4 / 72                       # pt -> mm
SCHRIFT = S.STIL["schrift"]["office"]          # Begruendung in stil.yaml
RECHTEINHABER = "vfdb Referat 4"
SCHEMA_NAME = "vfdb Leitfaden"

# Office-Konstanten
PP_LAYOUT_BLANK, PP_TEMPLATE, PP_THEME, PP_PDF = 12, 26, 31, 32
PP_GUIDE_H, PP_GUIDE_V = 1, 2
MSO_LATIN = 1
XL_XY_LINIEN = 75                    # xlXYScatterLinesNoMarkers
XL_KATEGORIE, XL_WERT = 1, 2
XL_TICK_INNEN, XL_TICK_AUSSEN = 2, 3
XL_KEIN = -4142                      # xlNone
XL_LEGENDE_UNTEN = -4107
XL_MINIMUM = 4                       # xlMinimum (Achsenkreuzung)
XL_XLSX = 51
XL_FREI = 3                          # xlFreeFloating
DATEN_BIS = 10001                    # Datenbereich der Diagrammreihen (Zeile 2 bis 10001)
ZAHLENFORMAT = f"General;{S.ZAHLEN['minuszeichen']}General"   # Minuszeichen nach stil.yaml
# Linienstile stil.yaml -> MsoLineDashStyle
STRICH = {"durchgezogen": 1, "gestrichelt": 4, "gepunktet": 3, "strichpunkt": 5,
          "strich-punkt-punkt": 6, "fein-gepunktet": 11, "lang-gestrichelt": 7}
# Theme-Farbplaetze (MsoThemeColorSchemeIndex)
THEME = {1: S.TEXT, 2: "#ffffff", 3: S.GRAU, 4: S.GRAU_FLAECHE,
         **{4 + i: S.FARBEN[i - 1] for i in range(1, 7)}, 11: S.FARBEN[6], 12: S.FARBEN[7]}

# Legendenfeld fuer eine Zeile: Excel verteilt die Zeilen gleichmaessig auf die Feldhoehe,
# daher Hoehe = Zeilenzahl x zeile_mm (Anwender ziehen das Feld bei mehr Zeilen groesser)
LEGENDE_ZEILEN_PLATZ = 1
UEBERSTAND_MM = 15.0                 # Excel-Diagrammobjekt rechts/unten groesser als die Folie
TOLERANZ_MM = 0.2                    # Excel rastet die Plotflaeche in 1-pt-Schritten (0,35 mm) ein
WARNGRENZE_MM = 0.25                 # bestes erreichbares Ergebnis liegt bei etwa 0,2 mm
TITEL_X, TITEL_Y = "Zeit t in min", "Gastemperatur T in °C"
VERBOSE = False


def bgr(hexfarbe: str) -> int:
    """#rrggbb -> Office-RGB (BGR-Ganzzahl)."""
    h = hexfarbe.lstrip("#")
    return int(h[0:2], 16) + 256 * int(h[2:4], 16) + 65536 * int(h[4:6], 16)


def masse(format_: str) -> dict:
    """Masse der Abbildung in mm; Hoehe mit einer Legendenzeile (wie Python/LaTeX)."""
    f = S.FORMATE[format_]
    unten = S.LEGENDE["abstand_mm"] + S.LEGENDE["zeile_mm"] + S.LEGENDE["zuschlag_unten_mm"]
    return dict(breite=f["breite_mm"], links=f["rand_links_mm"], oben=f["rand_oben_mm"],
                achse_b=f["achse_b_mm"], achse_h=f["achse_h_mm"], unten=unten,
                hoehe=f["rand_oben_mm"] + f["achse_h_mm"] + unten)


def linienstil_name(i: int) -> str:
    ls = S.STIL["linienstile"]
    return ls[i]["name"] if i < len(ls) else "durchgezogen"


# --- Nachbearbeitung der Dateien ---------------------------------------------------------
def bereinigen(pfad: Path) -> None:
    """Entfernt persoenliche Metadaten (Autor, zuletzt geaendert, Firma, lokaler Speicherpfad)
    und benennt Design, Farb- und Schriftschema um. Office-Dateien sind ZIP-Archive mit XML."""
    tmp = pfad.with_suffix(pfad.suffix + ".tmp")
    with zipfile.ZipFile(pfad) as alt, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as neu:
        for info in alt.infolist():
            daten = alt.read(info.filename)
            if info.filename == "docProps/core.xml":
                t = daten.decode("utf-8")
                for tag in ("dc:creator", "cp:lastModifiedBy"):
                    t = re.sub(rf"<{tag}>[^<]*</{tag}>", f"<{tag}>{RECHTEINHABER}</{tag}>", t)
                daten = t.encode("utf-8")
            elif info.filename == "docProps/app.xml":
                t = daten.decode("utf-8")
                t = re.sub(r"<(Company|Manager)>[^<]*</\1>", r"<\1></\1>", t)
                daten = t.encode("utf-8")
            elif info.filename == "xl/workbook.xml":
                t = daten.decode("utf-8")      # Speicherpfad der Arbeitsmappe (absPath)
                t = re.sub(r"<mc:AlternateContent[^>]*>(?:(?!</mc:AlternateContent>).)*?"
                           r"x15ac:absPath.*?</mc:AlternateContent>", "", t, flags=re.S)
                daten = t.encode("utf-8")
            if info.filename.endswith(".xml") and ("theme" in info.filename.lower()
                                                   or info.filename == "docProps/app.xml"):
                t = daten.decode("utf-8")
                t = re.sub(r'(<a:(?:clrScheme|fontScheme|theme)\b[^>]*?\bname=")[^"]*"',
                           rf'\g<1>{SCHEMA_NAME}"', t)
                t = re.sub(r'(<thm15:themeFamily [^>]*name=")[^"]*"', rf'\g<1>{SCHEMA_NAME}"', t)
                t = re.sub(r"<vt:lpstr>Office</vt:lpstr>", f"<vt:lpstr>{SCHEMA_NAME}</vt:lpstr>", t)
                daten = t.encode("utf-8")
            neu.writestr(info, daten)
    tmp.replace(pfad)


# --- PowerPoint ------------------------------------------------------------------------
def design_setzen(pres) -> None:
    theme = pres.SlideMaster.Theme
    for idx, farbe in THEME.items():
        theme.ThemeColorScheme.Colors(idx).RGB = bgr(farbe)
    theme.ThemeFontScheme.MajorFont.Item(MSO_LATIN).Name = SCHRIFT
    theme.ThemeFontScheme.MinorFont.Item(MSO_LATIN).Name = SCHRIFT


def standardformen_setzen(folie) -> None:
    """Voreinstellung fuer neue Linien, Formen (Rechteck usw.) und Textfelder:
    Linie 0,6 pt in der Pfeilfarbe, Formen ohne Fuellung, Schrift 9 pt in der Textfarbe."""
    linie = folie.Shapes.AddLine(10, 10, 50, 10)
    linie.Line.Weight = S.PFEILE["linie_pt"]
    linie.Line.ForeColor.RGB = bgr(S.farbwert(S.PFEILE["farbe"]))
    linie.SetShapesDefaultProperties()
    linie.Delete()
    form = folie.Shapes.AddShape(1, 10, 10, 50, 20)          # msoShapeRectangle
    form.Line.Weight = S.PFEILE["linie_pt"]
    form.Line.ForeColor.RGB = bgr(S.farbwert(S.PFEILE["farbe"]))
    form.Fill.Visible = False
    tr = form.TextFrame.TextRange
    tr.Text = "x"
    tr.Font.Size = S.PT_BESCHRIFTUNG
    tr.Font.Name = SCHRIFT
    tr.Font.Color.RGB = bgr(S.TEXT)
    form.SetShapesDefaultProperties()
    form.Delete()
    form = folie.Shapes.AddTextbox(1, 10, 10, 50, 10)
    form.Line.Weight = S.PFEILE["linie_pt"]
    form.Line.ForeColor.RGB = bgr(S.farbwert(S.PFEILE["farbe"]))
    form.Line.Visible = False
    tr = form.TextFrame.TextRange
    tr.Text = "x"
    tr.Font.Size = S.PT_BESCHRIFTUNG
    tr.Font.Name = SCHRIFT
    tr.Font.Color.RGB = bgr(S.TEXT)
    form.SetShapesDefaultProperties()
    form.Delete()


def powerpoint_vorlagen(ppt, test_ordner: Path | None) -> list[Path]:
    erzeugt = []
    for format_ in ("standard", "breit"):
        m = masse(format_)
        pres = ppt.Presentations.Add(WithWindow=False)
        try:
            pres.PageSetup.SlideWidth = m["breite"] * PT
            pres.PageSetup.SlideHeight = m["hoehe"] * PT
            design_setzen(pres)
            for x in (m["links"], m["links"] + m["achse_b"]):
                pres.Guides.Add(PP_GUIDE_V, x * PT)
            for y in (m["oben"], m["oben"] + m["achse_h"]):
                pres.Guides.Add(PP_GUIDE_H, y * PT)
            folie = pres.Slides.Add(1, PP_LAYOUT_BLANK)
            standardformen_setzen(folie)
            if format_ == "standard":
                pfad = AUSGABE / "vfdb_Leitfaden.thmx"
                pres.SaveCopyAs(str(pfad), PP_THEME)
                erzeugt.append(pfad)
            pfad = AUSGABE / f"vfdb_Abbildung_{format_}.potx"
            pres.SaveCopyAs(str(pfad), PP_TEMPLATE)
            erzeugt.append(pfad)
            if test_ordner:
                _testfolie(folie, m)
                pdf = test_ordner / f"test_powerpoint_{format_}.pdf"
                pres.SaveCopyAs(str(pdf), PP_PDF)
                erzeugt.append(pdf)
        finally:
            pres.Close()
    return erzeugt


def _testfolie(folie, m) -> None:
    """Achsenrahmen, Linien in allen Farben/Stilen und Text 9/8 pt zur Kontrolle."""
    x0, y0, b, h = m["links"] * PT, m["oben"] * PT, m["achse_b"] * PT, m["achse_h"] * PT
    r = folie.Shapes.AddShape(1, x0, y0, b, h)       # msoShapeRectangle
    r.Fill.Visible = False
    r.Line.ForeColor.RGB = bgr(S.farbwert(S.ACHSE["gitter"]["farbe"]))
    r.Line.Weight = S.ACHSE["gitter"]["linie_pt"]
    for i in range(len(S.FARBEN)):
        y = y0 + h * (i + 1) / (len(S.FARBEN) + 1)
        ln = folie.Shapes.AddLine(x0 + 5 * PT, y, x0 + b - 5 * PT, y)
        ln.Line.ForeColor.RGB = bgr(S.FARBEN[i])
        ln.Line.Weight = S.LINIEN["daten_pt"]
        ln.Line.DashStyle = STRICH[linienstil_name(i)]
    for text, groesse, y in ((f"{TITEL_Y} ({S.PT_BESCHRIFTUNG:g} pt)", S.PT_BESCHRIFTUNG, y0 + h + 4 * PT),
                             (f"Legende {S.PT_LEGENDE:g} pt", S.PT_LEGENDE, y0 + h + 9 * PT)):
        tb = folie.Shapes.AddTextbox(1, x0, y, b, 10)
        tb.TextFrame.TextRange.Text = text
        tb.TextFrame.TextRange.Font.Size = groesse
        tb.TextFrame.TextRange.Font.Name = SCHRIFT


# --- Excel -----------------------------------------------------------------------------
def diagramm_formatieren(win32, ch, n_reihen: int) -> None:
    ca = ch.ChartArea
    ca.Format.Line.Visible = False
    ca.Format.Fill.Visible = False
    ca.Font.Name = SCHRIFT
    ca.Font.Size = S.PT_TICKS
    ca.Font.Color = bgr(S.TEXT)
    # kein (automatischer) Gesamttitel: Ein- und Ausschalten setzt "autoTitleDeleted"
    ch.HasTitle = True
    ch.HasTitle = False
    for typ, titel in ((XL_KATEGORIE, TITEL_X), (XL_WERT, TITEL_Y)):
        ax = ch.Axes(typ)
        ax.Format.Line.Visible = True
        ax.Format.Line.ForeColor.RGB = bgr(S.farbwert(S.ACHSE["farbe"]))
        ax.Format.Line.Weight = S.ACHSE["linie_pt"]
        richtung = XL_TICK_INNEN if S.ACHSE["ticks"]["richtung"] == "innen" else XL_TICK_AUSSEN
        ax.MajorTickMark = richtung
        ax.MinorTickMark = richtung if S.ACHSE["ticks"]["nebenticks"] else XL_KEIN
        ax.Crosses = XL_MINIMUM               # Achsen am Rand, auch bei negativen Werten
        ax.TickLabels.Font.Size = S.PT_TICKS
        ax.TickLabels.NumberFormat = ZAHLENFORMAT
        ax.HasMajorGridlines = S.ACHSE["gitter"]["sichtbar"]
        if S.ACHSE["gitter"]["sichtbar"]:
            gl = ax.MajorGridlines.Format.Line
            gl.ForeColor.RGB = bgr(S.farbwert(S.ACHSE["gitter"]["farbe"]))
            gl.Weight = S.ACHSE["gitter"]["linie_pt"]
        ax.HasTitle = True
        ax.AxisTitle.Text = titel
        schrift = ax.AxisTitle.Format.TextFrame2.TextRange.Font
        schrift.Size = S.PT_BESCHRIFTUNG
        schrift.Bold = False
        schrift.Name = SCHRIFT
        # Formelzeichen kursiv (Vorbild fuer eigene Achsentitel: Zeichen markieren, Strg+I);
        # Characters ist nur ueber die typisierte Bindung (makepy) erreichbar
        zeichen = titel.split()[1]                       # "t" bzw. "T"
        start = titel.index(f" {zeichen} ") + 2
        win32.gencache.EnsureDispatch(ax.AxisTitle).GetCharacters(start, 1).Font.Italic = True
    for i in range(n_reihen):
        s = ch.SeriesCollection(i + 1)
        ln = s.Format.Line
        ln.Visible = True
        ln.ForeColor.RGB = bgr(S.FARBEN[i])
        ln.Weight = S.LINIEN["daten_pt"]
        ln.DashStyle = STRICH[linienstil_name(i)]
        s.MarkerStyle = XL_KEIN
    ch.HasLegend = True
    ch.Legend.Position = XL_LEGENDE_UNTEN
    ch.Legend.Font.Size = S.PT_LEGENDE
    ch.Legend.Format.Line.Visible = bool(S.LEGENDE["rahmen"])
    ch.Legend.Format.Fill.Visible = False
    ch.PlotArea.Format.Line.Visible = False
    ch.PlotArea.Format.Fill.Visible = False


def layout_setzen(ch, m: dict, k: dict) -> None:
    """Achsenflaeche, Achsentitel und Legende setzen (mm); k = Korrekturen aus der Messung."""
    L, T = m["links"] + k["dx"], m["oben"] + k["dy"]
    W, H = m["achse_b"] + k["dw"], m["achse_h"] + k["dh"]
    pa = ch.PlotArea
    # erst verkleinern, dann verschieben, dann Endgroesse (sonst ragt die Flaeche
    # zwischenzeitlich ueber den Diagrammrand und Excel lehnt ab)
    for attr, wert in (("InsideWidth", W * PT * 0.5), ("InsideHeight", H * PT * 0.5),
                       ("InsideLeft", L * PT), ("InsideTop", T * PT),
                       ("InsideWidth", W * PT), ("InsideHeight", H * PT)):
        for _versuch in range(3):
            try:
                setattr(pa, attr, wert)
                break
            except Exception:  # noqa: BLE001 - frisches Diagramm: erst neu zeichnen lassen
                ch.Refresh()
                _ = ch.ChartArea.Width
        else:
            raise RuntimeError(f"PlotArea.{attr} = {wert * MM:.2f} mm von Excel abgelehnt")
    xt, yt, lg = ch.Axes(XL_KATEGORIE).AxisTitle, ch.Axes(XL_WERT).AxisTitle, ch.Legend
    xt.Top = (T + H + S.ACHSE["titel_abstand_x_mm"] + k["tx"]) * PT
    xt.Left = (L + W / 2) * PT - xt.Width / 2
    yt.Left = (L - S.ACHSE["titel_abstand_y_mm"] + k["ty"]) * PT - yt.Width
    yt.Top = (T + H / 2) * PT - yt.Height / 2
    # Legendenfeld: Breite der Achsenflaeche, Platz fuer mehrere Zeilen
    lg.Width = W * PT
    lg.Height = LEGENDE_ZEILEN_PLATZ * S.LEGENDE["zeile_mm"] * PT
    lg.Left = L * PT
    lg.Top = (T + H + S.LEGENDE["abstand_mm"] + k["tl"]) * PT


def _seite(pdf: Path):
    import pymupdf
    return pymupdf.open(pdf)[0]


def achsen_im_pdf(pdf: Path) -> tuple[float, float, float, float]:
    """(links, oben, Breite, Hoehe) der Achsenflaeche in mm, gemessen an den Achsenlinien."""
    linien = []
    for zeichnung in _seite(pdf).get_drawings():
        if abs((zeichnung.get("width") or 0) - S.ACHSE["linie_pt"]) > 0.05:
            continue
        for el in zeichnung["items"]:
            if el[0] == "l":
                linien.append((el[1].x * MM, el[1].y * MM, el[2].x * MM, el[2].y * MM))
    waag = max((l for l in linien if abs(l[1] - l[3]) < 0.01), key=lambda l: abs(l[2] - l[0]))
    senk = max((l for l in linien if abs(l[0] - l[2]) < 0.01), key=lambda l: abs(l[3] - l[1]))
    links, rechts = min(senk[0], waag[0], waag[2]), max(waag[0], waag[2])
    oben, unten = min(senk[1], senk[3]), waag[1]
    return links, oben, rechts - links, unten - oben


def texte_im_pdf(pdf: Path) -> dict[str, float]:
    """Lage der Texte in mm: x-Titel (Grundlinie), y-Titel (Grundlinie, x), erste
    Legendenzeile (Grundlinie)."""
    lage = {}
    for block in _seite(pdf).get_text("rawdict")["blocks"]:
        for zeile in block.get("lines", []):
            for span in zeile["spans"]:
                text = "".join(c["c"] for c in span["chars"])
                ox, oy = span["origin"]
                if text.startswith(TITEL_X.split()[0]):
                    lage["x_titel"] = oy * MM
                elif text.startswith(TITEL_Y.split()[0]):
                    lage["y_titel"] = ox * MM
                elif text.startswith("ETK"):
                    lage["legende"] = oy * MM
    return lage


def referenz_python(format_: str, ordner: Path) -> dict[str, float]:
    """Lage von Titeln und Legende in der Python-Abbildung gleichen Formats (Bezug)."""
    skript = ordner / "referenz.py"
    pdf = ordner / f"referenz_{format_}.pdf"
    skript.write_text(
        "import vfdb_stil as vs\n"
        f"fig, ax = vs.figur({format_!r}, legende=3)\n"
        "for i, n in enumerate(['ETK', 'Hydrokarbonkurve', 'Außenbrandkurve']):\n"
        "    ax.plot([0, 1], [0, i], label=n, **vs.reihe(i))\n"
        "ax.set_xlabel(r'Zeit $t$ in \\si{\\minute}')\n"
        "ax.set_ylabel(r'Gastemperatur $T$ in \\si{\\degreeCelsius}')\n"
        "vs.legende_unten(ax)\n"
        f"vs.speichern(fig, {str(pdf)!r}, ausgabe=False)\n", encoding="utf-8")
    subprocess.run([sys.executable, str(skript)], check=True)
    return texte_im_pdf(pdf)


def excel_vorlagen(win32, xl, ppt, test_ordner: Path | None) -> list[Path]:
    import numpy as np
    erzeugt = []
    t = np.r_[np.linspace(0, 10, 101), np.linspace(10.5, 120, 220)]   # dicht am Anfang
    reihen = [("ETK", 20 + 345 * np.log10(8 * t + 1)),
              ("Hydrokarbonkurve", 20 + 1080 * (1 - 0.325 * np.exp(-0.167 * t) - 0.675 * np.exp(-2.5 * t))),
              ("Außenbrandkurve", 20 + 660 * (1 - 0.687 * np.exp(-0.32 * t) - 0.313 * np.exp(-3.8 * t)))]
    n = len(S.FARBEN)                  # alle 8 Reihen vorformatiert, 4 bis 8 als leere Plaetze
    namen = [r[0] for r in reihen] + [f"Reihe {i}" for i in range(len(reihen) + 1, n + 1)]
    for format_ in ("standard", "breit"):
        m = masse(format_)
        wb = xl.Workbooks.Add()
        try:
            wb.ApplyTheme(str(AUSGABE / "vfdb_Leitfaden.thmx"))
            ws = wb.Worksheets(1)
            ws.Name = "Daten"
            ws.Cells(1, 1).Value = "t in min"
            for j, name in enumerate(namen):
                ws.Cells(1, j + 2).Value = name
            werte = [[float(t[k])] + [float(y[k]) for _n, y in reihen] for k in range(len(t))]
            ws.Range(ws.Cells(2, 1), ws.Cells(len(t) + 1, len(reihen) + 1)).Value = werte
            # Diagrammobjekt rechts/unten groesser als die Abbildung: Excel haelt rechts Platz
            # fuer ueberstehende Beschriftungen frei, unten liegt Platz fuer weitere
            # Legendenzeilen; der Ueberstand wird beim PDF-Export abgeschnitten.
            obj = ws.ChartObjects().Add(ws.Cells(2, 12).Left, ws.Cells(2, 12).Top,
                                        (m["breite"] + UEBERSTAND_MM) * PT,
                                        (m["hoehe"] + UEBERSTAND_MM) * PT)
            obj.Placement = XL_FREI          # Groesse/Lage unabhaengig von Zeilen und Spalten
            ch = obj.Chart
            ch.ChartType = XL_XY_LINIEN
            # Datenbereich bis Zeile DATEN_BIS: leere Zellen bleiben Luecken, eigene Daten mit
            # mehr Zeilen als das Beispiel werden ohne Anpassung gezeichnet
            ch.SetSourceData(ws.Range(ws.Cells(1, 1), ws.Cells(DATEN_BIS, n + 1)))
            diagramm_formatieren(win32, ch, n)
            achsen = {XL_KATEGORIE: (0, 120, 15), XL_WERT: (0, 1200, 200)}
            for typ, (lo, hi, schritt) in achsen.items():
                ax = ch.Axes(typ)
                ax.MinimumScale, ax.MaximumScale, ax.MajorUnit = lo, hi, schritt
            k = kalibrieren(ppt, ch, format_, m)
            print(f"  {format_}: Achsenflaeche auf {k['rest']:.2f} mm, Titel/Legende auf "
                  f"{k['rest_text']:.2f} mm genau")
            if format_ == "standard":
                # Diagrammvorlage mit automatischen Achsgrenzen (passt zu beliebigen Daten)
                for typ in achsen:
                    ax = ch.Axes(typ)
                    ax.MinimumScaleIsAuto = ax.MaximumScaleIsAuto = ax.MajorUnitIsAuto = True
                pfad = AUSGABE / "vfdb_Diagramm.crtx"
                ch.SaveChartTemplate(str(pfad))
                erzeugt.append(pfad)
                for typ, (lo, hi, schritt) in achsen.items():
                    ax = ch.Axes(typ)
                    ax.MinimumScale, ax.MaximumScale, ax.MajorUnit = lo, hi, schritt
                layout_setzen(ch, m, k)
            if test_ordner:
                erzeugt.append(_export_ueber_powerpoint(ppt, ch, format_, test_ordner))
            pfad = AUSGABE / f"vfdb_Diagramm_{format_}.xlsx"
            ws.Cells(1, 1).Select()
            wb.SaveAs(str(pfad), XL_XLSX)
            erzeugt.append(pfad)
        finally:
            wb.Close(SaveChanges=False)
    return erzeugt


def kalibrieren(ppt, ch, format_: str, m: dict, durchgaenge: int = 6) -> dict:
    """Layout so setzen, dass Achsenflaeche (auf TOLERANZ_MM) sowie Titel und erste
    Legendenzeile (wie in Python) im PDF richtig liegen; bester Durchgang wird behalten."""
    k = dict(dx=0.0, dy=0.0, dw=0.0, dh=0.0, tx=0.0, ty=0.0, tl=0.0)
    bester = None
    with tempfile.TemporaryDirectory() as tmp:
        ref = referenz_python(format_, Path(tmp))
        for _ in range(durchgaenge):
            layout_setzen(ch, m, k)
            pdf = _export_ueber_powerpoint(ppt, ch, format_, Path(tmp), "kalibrierung")
            links, oben, b, h = achsen_im_pdf(pdf)
            ist = texte_im_pdf(pdf)
            fehler = dict(dx=links - m["links"], dy=oben - m["oben"],
                          dw=b - m["achse_b"], dh=h - m["achse_h"])
            fehler_text = dict(tx=ist["x_titel"] - ref["x_titel"], ty=ist["y_titel"] - ref["y_titel"],
                               tl=ist["legende"] - ref["legende"])
            rest = max(abs(v) for v in fehler.values())
            rest_text = max(abs(v) for v in fehler_text.values())
            if VERBOSE:
                print("    " + ", ".join(f"{n} {v:+.2f}" for n, v in {**fehler, **fehler_text}.items()))
            if bester is None or max(rest, rest_text) < max(bester["rest"], bester["rest_text"]):
                bester = dict(k, rest=rest, rest_text=rest_text)
            if rest < TOLERANZ_MM and rest_text < TOLERANZ_MM:
                break
            for name, f in {**fehler, **fehler_text}.items():
                k[name] -= f
    layout_setzen(ch, m, bester)
    if bester["rest"] > WARNGRENZE_MM or bester["rest_text"] > WARNGRENZE_MM:
        print(f"  WARNUNG {format_}: Abweichung Achsenflaeche {bester['rest']:.2f} mm, "
              f"Titel/Legende {bester['rest_text']:.2f} mm")
    return bester


def _export_ueber_powerpoint(ppt, ch, format_: str, ordner: Path, name: str = "test_excel") -> Path:
    """Diagramm in die PowerPoint-Vorlage einfuegen und als PDF speichern (Weg fuer Anwender)."""
    pres = ppt.Presentations.Open(str(AUSGABE / f"vfdb_Abbildung_{format_}.potx"),
                                  ReadOnly=False, Untitled=True, WithWindow=False)
    try:
        ch.ChartArea.Copy()
        form = pres.Slides(1).Shapes.Paste()
        form.Left, form.Top = 0, 0
        pdf = ordner / f"{name}_{format_}.pdf"
        pres.SaveCopyAs(str(pdf), PP_PDF)
        return pdf
    finally:
        pres.Close()


def _laeuft(prozess: str) -> bool:
    ausgabe = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {prozess}"], capture_output=True,
                             text=True, errors="replace").stdout
    return prozess.lower() in ausgabe.lower()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--test", action="store_true", help="Test-PDFs nach office/test/ schreiben")
    p.add_argument("--ausfuehrlich", action="store_true", help="Abweichungen je Kalibrierschritt")
    a = p.parse_args(argv)
    global VERBOSE
    VERBOSE = a.ausfuehrlich
    offen = [n for n in ("EXCEL.EXE", "POWERPNT.EXE") if _laeuft(n)]
    if offen:
        print(f"Bitte zuerst {' und '.join(offen)} schliessen (das Skript startet und beendet "
              "eigene Office-Instanzen).", file=sys.stderr)
        return 1
    import pythoncom
    import win32com.client as win32
    global AUSGABE
    test = OFFICE / "test" if a.test else None
    if test:
        test.mkdir(exist_ok=True)
    pythoncom.CoInitialize()
    erzeugt: list[Path] = []
    # Erst in einen temporaeren Ordner erzeugen und bereinigen; nur bei Erfolg nach office/
    # verschieben (bei einem Abbruch bleiben keine unbereinigten Dateien zurueck)
    with tempfile.TemporaryDirectory(prefix="vfdb_office_") as tmp:
        AUSGABE = Path(tmp)
        ppt = win32.DispatchEx("PowerPoint.Application")
        try:
            xl = win32.DispatchEx("Excel.Application")
            try:
                xl.Visible = False
                xl.DisplayAlerts = False
                erzeugt += powerpoint_vorlagen(ppt, test)
                erzeugt += excel_vorlagen(win32, xl, ppt, test)
            finally:
                xl.Quit()
        finally:
            ppt.Quit()
        for pfad in erzeugt:
            if pfad.parent == AUSGABE:
                bereinigen(pfad)
                ziel = OFFICE / pfad.name
                shutil.copy(pfad, ziel)
                print(ziel)
            else:
                print(pfad)
    return 0


if __name__ == "__main__":
    sys.exit(main())
