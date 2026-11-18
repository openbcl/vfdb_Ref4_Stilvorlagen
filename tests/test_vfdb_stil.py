"""Tests fuer vfdb_stil, das LaTeX-Paket und die Office-Dateien.

Tests mit Abbildungen brauchen LuaLaTeX und die Schriften TeX Gyre Heros und Fira Math;
ohne LuaLaTeX werden sie uebersprungen.
"""
import importlib.util
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import numpy as np
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader

import vfdb_stil as vs
from vfdb_stil import excel, farbpruefung

PT_MM = 25.4 / 72
REPO = Path(__file__).resolve().parents[1]
latex = pytest.mark.skipif(shutil.which("lualatex") is None, reason="LuaLaTeX nicht installiert")


def _modul(pfad: Path):
    spec = importlib.util.spec_from_file_location(pfad.stem, pfad)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _pdf_mm(pfad):
    box = PdfReader(pfad).pages[0].mediabox
    return float(box.width) * PT_MM, float(box.height) * PT_MM


def _pdf_text(pfad):
    return PdfReader(pfad).pages[0].extract_text()


# --- Stilwerte -----------------------------------------------------------------------
@pytest.mark.parametrize("name", list(vs.FORMATE))
def test_formatbreite_ist_summe(name):
    f = vs.FORMATE[name]
    assert f["rand_links_mm"] + f["achse_b_mm"] + f["rand_rechts_mm"] == pytest.approx(f["breite_mm"])


def test_breites_format_ist_textbreite():
    assert vs.FORMATE["breit"]["breite_mm"] == pytest.approx(vs.TEXTBREITE_MM)


def test_farben_namen_linienstile():
    assert len(vs.FARBEN) == len(vs.FARBNAMEN) == len(vs.LINIENSTILE) == 8
    assert len(set(vs.FARBEN)) == 8
    with pytest.raises(IndexError):
        vs.farbe(8)


def test_farbzyklus_hat_alle_8_farben():
    zyklus = list(vs.abbildung.rc_parameter()["axes.prop_cycle"])
    assert [z["color"] for z in zyklus] == vs.FARBEN


def test_spaltenregel():
    assert [vs.legende_spalten(n) for n in range(1, 8)] == [1, 2, 3, 2, 3, 3, 3]


def test_versionen_gleich():
    pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    sty = (REPO / "latex" / "vfdbstil.sty").read_text(encoding="utf-8")
    v = vs.STIL["version"]
    assert re.search(r'^version = "([^"]+)"', pyproject, re.M).group(1) == v
    assert f"v{v} " in re.search(r"\\ProvidesPackage\{vfdbstil\}\[[^\]]*\]", sty).group(0)
    for doku in ("README.md", "docs/Stilvorgaben.md"):
        genannt = re.findall(r"\b(\d+\.\d+\.\d+)\b", (REPO / doku).read_text(encoding="utf-8"))
        assert genannt and set(genannt) == {v}, doku


def test_matplotlib_strichmuster_wie_in_latex():
    """erzeuge_werte.py uebernimmt die Strichmuster von matplotlib - pruefen, ob sie stimmen."""
    import matplotlib
    mod = _modul(REPO / "latex" / "erzeuge_werte.py")
    for name, schluessel in (("gestrichelt", "lines.dashed_pattern"), ("gepunktet", "lines.dotted_pattern"),
                             ("strichpunkt", "lines.dashdot_pattern")):
        assert mod.MPL_MUSTER[name] == pytest.approx(list(matplotlib.rcParamsDefault[schluessel]))


# --- Zahlen --------------------------------------------------------------------------
@pytest.mark.parametrize("x, erwartet", [
    (1.5, "1,5"), (-2, "\u22122"), (-0.0, "0"), (1200, "1200"), (100000, "100000"),
    (0.125, "0,125"), (0.30000000000000004, "0,3"),
    (2.5e6, r"$2{,}5\cdot 10^{6}$"), (1e-5, r"$1\cdot 10^{-5}$"),
])
def test_zahl(x, erwartet):
    assert vs.zahl(x) == erwartet


def test_zahl_nachkomma():
    assert vs.zahl(2, 1) == "2,0"
    assert vs.zahl(5e-5, 2) == r"$5{,}00\cdot 10^{-5}$"        # nicht "0,00"
    assert vs.zahl(2.5e6, 1) == r"$2{,}5\cdot 10^{6}$"


def test_formatter_exponent_je_achse():
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    ax.set_ylim(0, 2e6)
    ax.set_yticks([0, 5e5, 1e6, 1.5e6, 2e6])
    vs.deutsch(ax)
    fig.draw_without_rendering()
    texte = [t.get_text() for t in ax.get_yticklabels()]
    plt.close(fig)
    assert texte[0] == "0" and all(r"\cdot" in t for t in texte[1:])


def test_felder_nebeneinander_mit_abstand():
    fig, (a1, a2) = vs.figur("breit", ncols=2)
    x1, _y, b1, _h = vs.achse_mm(a1)
    x2, *_ = vs.achse_mm(a2)
    assert x2 - (x1 + b1) == pytest.approx(vs.FORMATE["breit"]["rand_links_mm"], abs=0.01)


def test_formatter_rundungsrest_wird_null():
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    ax.set_ylim(-0.4, 0.4)
    f = vs.komma_formatter()
    ax.yaxis.set_major_formatter(f)
    assert f(-1.1102230246251565e-16) == "0"
    plt.close(fig)


# --- Farbpruefung ----------------------------------------------------------------------
def test_palette_besteht_pruefung():
    _bericht, ok = farbpruefung.pruefen(vs.FARBEN)
    assert ok


def test_farbabstand_algorithmus():
    """Rechenweg gegen einen festen Bezugswert (unabhaengig von stil.yaml)."""
    bezug = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
    d = min(farbpruefung.delta_e(a, b) for a, b in zip(bezug, bezug[1:]))
    assert d == pytest.approx(19.6, abs=0.05)


def test_graue_palette_faellt_durch():
    _bericht, ok = farbpruefung.pruefen(["#777777", "#787878"])
    assert not ok


def test_farbpruefung_eingaben(capsys):
    assert farbpruefung.main(["#2a78d6"]) == 0
    assert farbpruefung.main(["#gggggg,#2a78d6"]) == 2
    assert "FEHLER" in capsys.readouterr().err


# --- Excel: Text und Pruefungen (ohne LaTeX) -------------------------------------------------
def test_latex_text():
    assert excel.latex_text("A_b & c # d") == r"A\_b \& c \# d"
    assert excel.latex_text(r"$Y_{CO}$ in Vol.-%") == r"$Y_{CO}$ in Vol.-%"
    assert excel.latex_text(r"bereits \_ maskiert") == r"bereits \_ maskiert"
    assert excel.latex_text(r"\ce{CO_2} und x_1") == r"\ce{CO_2} und x\_1"


def _mappe(tmp_path, angaben=None, reihen=None, daten=None, name="m.xlsx"):
    beispiel = {"angaben": {"Dateiname": "x", "x-Spalte": "t", **(angaben or {})},
                "reihen": reihen if reihen is not None else [["y", "A", 1, "Linie", None]],
                "daten": daten if daten is not None else {"t": [0, 1, 2], "y": [0, 1, 4]}}
    return excel.vorlage_schreiben(tmp_path / name, beispiel)


@pytest.mark.parametrize("angaben, reihen, daten, meldung", [
    ({"Dateiname": None}, None, None, "Dateiname"),
    ({}, [["fehlt", "A", 1, "Linie", None]], None, "fehlt"),
    ({"x min": 4, "x max": 0}, None, None, "kleiner"),
    ({"x min": 0, "x max": 10, "x Schritt": 0.01}, None, None, "Teilstriche"),
    ({}, [["y", "A", 1, "Linie", 2.7]], None, "nicht erlaubt"),
    ({}, [["y", "A", 0, "Linie", None]], None, "nicht erlaubt"),
    ({"Format": "zweifeldrig"}, None, None, "Feld 2"),
    ({}, [["y", "A", 1, "Linie", 2], ["z", "B", 1, "Linie", 2]],
     {"t": [0, 1], "y": [0, 1], "z": [1, 2]}, "schon"),
    ({}, [[f"y{i}", f"R{i}", 1, "Linie", None] for i in range(9)],
     {"t": [0, 1], **{f"y{i}": [0, i] for i in range(9)}}, "mehr als 8"),
    ({}, None, {"t": [0, 1], "y": ["1.200", 3]}, "mehrdeutig"),
    ({}, None, {"t": [0, 1], "y": [None, None]}, "keine Zahlen"),
])
def test_excel_fehlermeldungen(tmp_path, angaben, reihen, daten, meldung):
    pfad = _mappe(tmp_path, angaben, reihen, daten)
    with pytest.raises(excel.ExcelFehler, match=meldung):
        excel.abbildung_aus_excel(pfad, tmp_path, ausgabe=False)


def test_excel_doppelte_spaltenkoepfe(tmp_path):
    pfad = _mappe(tmp_path)
    wb = load_workbook(pfad)
    wb["Daten"]["C1"] = "y"
    wb.save(pfad)
    with pytest.raises(excel.ExcelFehler, match="doppelt"):
        excel.abbildung_aus_excel(pfad, tmp_path, ausgabe=False)


def test_excel_formel_ohne_wert(tmp_path):
    pfad = _mappe(tmp_path)
    wb = load_workbook(pfad)
    wb["Daten"]["B2"] = "=A2*2"          # openpyxl speichert keinen berechneten Wert
    wb.save(pfad)
    with pytest.raises(excel.ExcelFehler, match="Formel"):
        excel.abbildung_aus_excel(pfad, tmp_path, ausgabe=False)


def test_excel_formel_mit_leerem_ergebnis_ist_luecke(tmp_path):
    """=WENN(...;"";...) speichert Excel als <c t="str"><f>..</f><v/></c> - eine Luecke."""
    pfad = _mappe(tmp_path, daten={"t": [0, 1, 2, 3], "y": [0, 1, 4, 9]})
    wb = load_workbook(pfad)
    wb["Daten"]["B3"] = '=IF(A3=1,"",A3)'
    wb.save(pfad)
    tmp = tmp_path / "neu.xlsx"
    with zipfile.ZipFile(pfad) as alt, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as neu:
        for eintrag in alt.infolist():
            inhalt = alt.read(eintrag.filename)
            if eintrag.filename == "xl/worksheets/sheet3.xml":
                inhalt = re.sub(rb'<c r="B3"([^>]*)><f>(.*?)</f>(<v\s*/>|<v></v>)?</c>',
                                rb'<c r="B3" t="str"><f>\2</f><v/></c>', inhalt)
                assert b't="str"' in inhalt
            neu.writestr(eintrag, inhalt)
    werte = excel.daten_lesen(load_workbook(tmp, data_only=True), load_workbook(tmp), {"t", "y"})
    assert np.isnan(werte["y"][1]) and werte["y"][2] == 4


def test_excel_nv_ist_luecke_und_klammerformel_wird_gemeldet(tmp_path):
    pfad = _mappe(tmp_path, daten={"t": [0, 1, 2], "y": [0, "#N/A", 4]})
    werte = excel.daten_lesen(load_workbook(pfad, data_only=True), None, {"t", "y"})
    assert np.isnan(werte["y"][1])
    with pytest.raises(excel.ExcelFehler, match=r"statt \\\("):
        excel.text_pruefen(r"Zeit \(t_\mathrm{a}\) in min", "Test")


def test_cli_dateiname_mit_eckigen_klammern(tmp_path, monkeypatch):
    (tmp_path / "Abb 4-3 [Entwurf].xlsx").write_bytes(b"x")
    gelesen = []
    monkeypatch.setattr(excel, "abbildung_aus_excel", lambda d, z: gelesen.append(Path(d).name) or Path(d))
    assert excel.main([str(tmp_path / "Abb 4-3 [Entwurf].xlsx")]) == 0
    assert excel.main([str(tmp_path / "Abb 4-3 [Entwurf]")]) == 0       # ohne Endung
    assert gelesen == ["Abb 4-3 [Entwurf].xlsx"] * 2


@latex
def test_excel_tabulator_bis_zum_pdf(tmp_path):
    """Mitkopierter Tabulator in Titel und Legende: als Leerzeichen gesetzt, kein Abbruch."""
    pfad = _mappe(tmp_path, {"y-Achsentitel": "Gastemperatur\t$T$ in K"},
                  reihen=[["y", "Messung\tA", 1, "Linie", None], ["z", "Messung B", 1, "Linie", None]],
                  daten={"t": [0, 1, 2], "y": [0, 1, 4], "z": [1, 2, 3]})
    pdf = excel.abbildung_aus_excel(pfad, tmp_path, ausgabe=False)
    text = _pdf_text(pdf)
    assert "Gastemperatur" in text and "Messung A" in text


def test_excel_spaltennamen_mit_zeilenumbruch(tmp_path):
    pfad = _mappe(tmp_path, reihen=[["Q  langsam", "A", 1, "Linie", None]],
                  daten={"t": [0, 1], "Q\nlangsam": [0, 1]})
    werte = excel.daten_lesen(load_workbook(pfad, data_only=True), None, {"t", "Q langsam"})
    assert list(werte["Q langsam"]) == [0, 1]
    assert excel.reihen_lesen(load_workbook(pfad), "standard")[0].spalte == "Q langsam"


def test_excel_farbvergabe():
    R = excel.Reihe
    reihen = [R("a", "A", 1, "linie", 2, 2), R("b", "B", 1, "linie", None, 3), R("c", "C", 1, "linie", None, 4)]
    assert excel._farben_vergeben(reihen) == {"A": 1, "B": 0, "C": 2}


def test_vorlage_nicht_ueberschreiben(tmp_path, capsys):
    ziel = tmp_path / "v.xlsx"
    ziel.write_bytes(b"inhalt")
    assert excel.main(["--vorlage", str(ziel)]) == 1
    assert ziel.read_bytes() == b"inhalt"


def test_cli_macht_nach_fehler_weiter(tmp_path, capsys):
    kaputt = tmp_path / "daten.csv"
    kaputt.write_text("a;b", encoding="utf-8")
    fehlt = tmp_path / "gibtsnicht.xlsx"
    falsch = tmp_path / "umbenannt.xlsx"
    falsch.write_text("a;b", encoding="utf-8")
    assert excel.main([str(kaputt), str(fehlt), str(falsch), str(tmp_path / "x*.xlsx")]) == 1
    err = capsys.readouterr().err
    assert ".xlsx" in err and "nicht gefunden" in err and "keine gültige" in err
    assert "keine Datei passt" in err


def test_vorlage_dateiname_aus_excel_name(tmp_path):
    assert excel.main(["--vorlage", str(tmp_path / "05-rauchgas.xlsx")]) == 0
    wb = load_workbook(tmp_path / "05-rauchgas.xlsx")
    werte = {z[0].value: z[1].value for z in wb[excel.BLATT_DIAGRAMM].iter_rows(min_row=2)}
    assert werte["Dateiname"] == "05-rauchgas"


def test_cli_ohne_endung_und_ohne_sperrdatei(tmp_path, monkeypatch, capsys):
    (tmp_path / "abb.xlsx").write_bytes(b"x")
    (tmp_path / "~$abb.xlsx").write_bytes(b"x")          # Sperrdatei einer geoeffneten Mappe
    (tmp_path / "abb.pdf").write_bytes(b"x")             # zuvor erzeugtes PDF
    (tmp_path / "05.2-abb.xlsx").write_bytes(b"x")       # Punkt im Namen
    gelesen = []
    monkeypatch.setattr(excel, "abbildung_aus_excel", lambda d, z: gelesen.append(Path(d).name) or Path(d))
    assert excel.main([str(tmp_path / "abb")]) == 0
    assert excel.main([str(tmp_path / "05.2-abb")]) == 0
    assert excel.main([str(tmp_path / "*")]) == 0
    assert gelesen == ["abb.xlsx", "05.2-abb.xlsx", "05.2-abb.xlsx", "abb.xlsx"]


def test_vorlage_ohne_endung(tmp_path):
    assert excel.main(["--vorlage", str(tmp_path / "neu")]) == 0
    assert (tmp_path / "neu.xlsx").exists()


@pytest.mark.parametrize("angaben, meldung", [
    ({"Dateiname": "05:abb"}, "Dateiname nicht möglich"),
    ({"Dateiname": "05/abb"}, "Dateiname nicht möglich"),
    ({"y-Achsentitel": "Temperatur $T in K"}, r"y-Achsentitel \(B\d+\).*paarweise"),
    ({"y-Achsentitel": "Klammer {"}, r"y-Achsentitel \(B\d+\).*Klammern"),
])
def test_excel_texte_und_dateiname(tmp_path, angaben, meldung):
    pfad = _mappe(tmp_path, angaben)
    with pytest.raises(excel.ExcelFehler, match=meldung):
        excel.abbildung_aus_excel(pfad, tmp_path, ausgabe=False)


def test_excel_formel_ohne_wert_im_blatt_diagramm(tmp_path):
    pfad = _mappe(tmp_path)
    wb = load_workbook(pfad)
    ws = wb["Diagramm"]
    zeile = next(c.row for c in ws["A"] if c.value == "x max")
    ws.cell(zeile, 2).value = "=5*2"
    wb.save(pfad)
    with pytest.raises(excel.ExcelFehler, match=f"Blatt Diagramm, Zelle B{zeile}: Formel"):
        excel.abbildung_aus_excel(pfad, tmp_path, ausgabe=False)


def test_excel_legende_falsch_und_tausender():
    assert excel._schluessel(False) == "false" and excel._schluessel(0) == "0"
    assert excel._zahl("0.500", "x") == 0.5                      # fuehrende 0: kein Tausenderpunkt
    with pytest.raises(excel.ExcelFehler, match="mehrdeutig"):
        excel._zahl("1.200", "x")


# --- Office-Dateien ------------------------------------------------------------------------
@pytest.mark.parametrize("datei", sorted((REPO / "office").glob("vfdb_*.*")))
def test_office_ohne_persoenliche_metadaten(datei):
    with zipfile.ZipFile(datei) as z:
        for n in z.namelist():
            if n.endswith(".xml"):
                t = z.read(n).decode("utf-8")
                assert "absPath" not in t and not re.search(r"[A-Za-z]:\\\\", t), n
                for name in re.findall(r'<a:(?:theme|clrScheme|fontScheme)\b[^>]*?\bname="([^"]*)"', t):
                    assert name == "vfdb Leitfaden", (n, name)
            if n.startswith("docProps/") and n.endswith(".xml"):
                t = z.read(n).decode("utf-8")
                for tag in ("dc:creator", "cp:lastModifiedBy"):
                    m = re.search(rf"<{tag}>([^<]*)<", t)
                    assert m is None or m.group(1) in ("", "vfdb Referat 4"), (n, m.group(1))
                m = re.search(r"<Company>([^<]*)<", t)
                assert m is None or m.group(1) == "", (n, m.group(1))


@pytest.mark.parametrize("datei", sorted((REPO / "office").glob("vfdb_*.*")))
def test_office_design_nach_stil(datei):
    with zipfile.ZipFile(datei) as z:
        themen = [n for n in z.namelist() if "theme" in n.lower() and n.endswith(".xml")
                  and "themeManager" not in n]
        for n in themen:
            t = z.read(n).decode("utf-8")
            if "<a:clrScheme" not in t:
                continue
            akzente = re.findall(r'<a:accent\d><a:srgbClr val="([0-9A-F]{6})"', t)
            assert akzente == [f.lstrip("#").upper() for f in vs.FARBEN[:6]], n
            assert re.findall(r'<a:latin typeface="([^"]*)"', t)[:2] == [vs.STIL["schrift"]["office"]] * 2


# --- Abbildungen (LuaLaTeX) --------------------------------------------------------------
@latex
@pytest.mark.parametrize("name", list(vs.FORMATE))
def test_pdf_hat_formatmasse(tmp_path, name):
    fig, ax = vs.figur(name)
    for a in np.atleast_1d(ax):
        a.plot([0, 1], [0, 1], **vs.reihe(0))
    pfad = vs.speichern(fig, tmp_path / name, ausgabe=False)
    f = vs.FORMATE[name]
    felder = 2 if name == "zweifeldrig" else 1
    hoehe = f["rand_oben_mm"] + felder * f["achse_h_mm"] + (felder - 1) * f.get("feldabstand_mm", 0) \
        + f["rand_unten_mm"]
    assert _pdf_mm(pfad) == pytest.approx((f["breite_mm"], hoehe), abs=0.05)


@latex
def test_legende_passt_rand_an_achse_bleibt(tmp_path):
    fig, ax = vs.figur("standard", legende=3)
    for i, name in enumerate(["sehr lange Legendenbeschriftung A", "ebenso lange Beschriftung B",
                              "und noch eine Beschriftung C"]):
        ax.plot([0, 1], [i, i + 1], label=name, **vs.reihe(i))
    vs.legende_unten(ax)
    f = vs.FORMATE["standard"]
    assert vs.achse_mm(ax)[2:] == pytest.approx((f["achse_b_mm"], f["achse_h_mm"]), abs=0.01)
    assert not [w for w in vs.pruefen(fig) if w.startswith("Rand")]


@latex
@pytest.mark.parametrize("woerter, passt", [(3, True), (4, True), (5, True), (6, True), (7, False)])
def test_legende_ragt_nicht_ueber_den_rand(woerter, passt):
    """Spalten werden zusammengelegt, bis die Legende passt; ist schon ein einzelner Eintrag
    zu lang (7 Woerter), meldet pruefen() das."""
    fig, ax = vs.figur("standard", legende=3)
    for i in range(3):
        ax.plot([0, 1], [0, i], label=" ".join(["Beschriftung"] * woerter), **vs.reihe(i))
    vs.legende_unten(ax)
    rand = [w for w in vs.pruefen(fig) if w.startswith("Rand")]
    assert (not rand) == passt


@latex
def test_legende_zeilenabstand(tmp_path):
    fig, ax = vs.figur("standard", legende=4)
    for i in range(4):
        ax.plot([0, 1], [0, i], label=f"Reihe {i + 1}", **vs.reihe(i))
    leg = vs.legende_unten(ax)
    fig.draw_without_rendering()
    r = fig.canvas.get_renderer()
    ys = sorted({round(t.get_window_extent(r).y0, 3) for t in leg.get_texts()})
    abstand_mm = (ys[1] - ys[0]) / fig.dpi * 25.4
    assert abstand_mm == pytest.approx(vs.STIL["legende"]["zeile_mm"], abs=0.1)


def test_legende_ohne_eintraege_und_nur_unterstes_feld():
    fig, (a1, a2) = vs.figur("zweifeldrig", sharex=True)
    assert vs.legende_unten(a2) is None
    a1.plot([0, 1], [0, 1], label="A")
    with pytest.raises(ValueError, match="untersten"):
        vs.legende_unten(a1)


def test_legende_zeilenweise():
    from vfdb_stil.abbildung import _zeilenweise
    assert _zeilenweise("abc", 2) == ["a", "c", "b"]
    assert _zeilenweise("abcd", 2) == ["a", "c", "b", "d"]
    assert _zeilenweise("abcde", 3) == ["a", "d", "b", "e", "c"]
    assert _zeilenweise("", 3) == []


def test_phasengrenzen_durchgezogen():
    fig, ax = vs.figur("standard")
    vs.pfeilachsen(ax, 10, 10)
    for _ in range(3):                     # Linienstil-Zyklus weiterdrehen
        ax.plot([0, 1], [0, 1])
    vs.phasenbalken(ax, 0, 5, "Phase")
    assert all(l.get_linestyle() == "-" for l in ax.lines[-2:])


@latex
@pytest.mark.parametrize("ziel, erwartet", [("abb", "abb.pdf"), ("abb.png", "abb.pdf"), ("abb.pdf", "abb.pdf")])
def test_speichern_endung(tmp_path, ziel, erwartet):
    fig, ax = vs.figur("standard")
    ax.plot([0, 1], [0, 1])
    assert vs.speichern(fig, tmp_path / ziel, ausgabe=False).name == erwartet


@latex
def test_excel_beispiel(tmp_path):
    pfad = excel.abbildung_aus_excel(REPO / "beispiele" / "excel" / "t2_brandentwicklung.xlsx",
                                     tmp_path, ausgabe=False)
    f, leg = vs.FORMATE["zweifeldrig"], vs.STIL["legende"]
    hoehe = (f["rand_oben_mm"] + 2 * f["achse_h_mm"] + f["feldabstand_mm"]
             + leg["abstand_mm"] + 2 * leg["zeile_mm"] + leg["zuschlag_unten_mm"])   # 4 Eintraege, 2 Zeilen
    assert _pdf_mm(pfad) == pytest.approx((f["breite_mm"], hoehe), abs=0.05)


@latex
def test_excel_vorlage_ist_lauffaehig(tmp_path):
    pfad = excel.vorlage_schreiben(tmp_path / "v.xlsx")
    pdf = excel.abbildung_aus_excel(pfad, tmp_path, ausgabe=False)
    assert pdf.name == "00-beispiel.pdf"


@latex
def test_excel_ticks_ohne_rundungsrest(tmp_path):
    pfad = _mappe(tmp_path, {"y min": -0.4, "y max": 0.4, "y Schritt": 0.1},
                  daten={"t": [0, 1, 2], "y": [-0.4, 0, 0.4]})
    pdf = excel.abbildung_aus_excel(pfad, tmp_path, ausgabe=False)
    text = _pdf_text(pdf)
    assert "e-16" not in text and "\u22c5" not in text and "10\u221216" not in text
    assert "\u22120,4" in text and "0,1" in text


@latex
def test_excel_textspalten_werden_nicht_gelesen(tmp_path):
    pfad = _mappe(tmp_path, daten={"t": [0, 1, 2], "y": [0, 1, 4], "Bemerkung": ["a", "b", "c"]})
    assert excel.abbildung_aus_excel(pfad, tmp_path, ausgabe=False).exists()


@latex
def test_fehlende_zeichen_werden_gemeldet():
    assert vs.fehlende_zeichen("CO\u2082 und \u1e41") == ["\u2082", "\u1e41"]
    assert vs.fehlende_zeichen("Q\u0307 in kW") == ["\u0307"]          # Punkt aus Word
    assert vs.fehlende_zeichen("Temperatur in \u00b0C, $\\dot{Q}$, \u2264") == []
    assert vs.fehlende_zeichen("Wa\u0308rme") == []                    # zerlegtes \u00e4 ist richtig
    assert vs.abbildung.formelbefehle_ausserhalb(r"a \alpha $\beta$ \si{\kilo\watt}") == [r"\alpha"]


@pytest.mark.parametrize("text, erwartet", [
    (r"Rate \dot{Q} in kW", [r"\dot{Q}"]),
    (r"Index Y_\mathrm{CO}", [r"Y_\mathrm{CO}"]),
    ("\u00dcberdruck $\\Delta p$ in \\si{\\milli\\bar}", []),     # siunitx-Einheit bar
    (r"\SI{5}{\bar} und \qty{2}{\bar}", []),
    (r"\qtyrange{0}{10}{\bar}, \SIrange{1}{2}{\bar}, \qtylist{1;2}{\bar}", []),
    (r"\si{\bar\tothe{2}}, \(\alpha\), \ensuremath{\beta}", []),
    (r"\ce{CO2} und $\bar{x}$", []),
    (r"Rate \dot{Q}_\mathrm{max} in kW", [r"\dot{Q}_\mathrm{max}"]),   # Index gehoert dazu
    (r"\frac{1}{2} und \sqrt[3]{x}", [r"\frac{1}{2}", r"\sqrt[3]{x}"]),
    (r"Druckdifferenz \Delta p in \si{\pascal}, \dot Q", [r"\Delta p", r"\dot Q"]),
])
def test_formelbefehle_mit_argument_und_einheiten(text, erwartet):
    assert vs.abbildung.formelbefehle_ausserhalb(text) == erwartet


def test_index_hinter_formel_wird_gemeldet():
    assert "geh\u00f6rt in die Formel" in vs.abbildung.formel_fehler(r"Rate $\dot{Q}$_\mathrm{max} in kW")
    assert vs.abbildung.formel_fehler(r"Fl\u00e4che in m$^2$, $\dot{Q}_\mathrm{max}$") is None


@pytest.mark.parametrize("text", ["$\theta$ oben", "$\rho$", "$\nu$", "$\beta$"])
def test_fehlendes_r_wird_gemeldet(text):
    assert "Steuerzeichen" in vs.abbildung.formel_fehler(text)


@pytest.mark.parametrize("text", ["Druck $p$ in \\si{\\milli\bar}", "Kraft in \\si{\\kilo\newton}",
                                  "Masse in \\si{\tonne}", "Spannung in \\si{\volt}",
                                  "Brandlast \num{800} in MJ/m²"])
def test_fehlendes_r_in_einheiten_wird_gemeldet(text):
    assert "Steuerzeichen" in vs.abbildung.formel_fehler(text)


def test_hochzahl_ausserhalb_der_formel_wird_gemeldet():
    assert "Hochzahl" in vs.abbildung.formel_fehler(r"Fläche $A$ in m^2")
    for gut in (r"Fläche in m$^2$", "Fläche in m²", r"in \si{kW/m^2}", r"$q''$ in \si{\kilo\watt\per\square\metre}"):
        assert vs.abbildung.formel_fehler(gut) is None


def test_marker_auf_dem_rand_werden_ganz_gezeichnet():
    fig, ax = vs.figur()
    (ln,) = ax.plot([0, 1, 3], [0, 1, 9], ls="none", marker="o", label="A")
    ax.set_xlim(0, 2)                                    # (3, 9) liegt ausserhalb
    vs.abbildung._marker_ganz_zeigen(fig)
    neu = [a for a in ax.get_children() if a is not ln and getattr(a, "get_marker", None)
           and a.get_marker() == "o"]
    vs.abbildung.plt.close(fig)
    assert ln.get_marker() in ("None", "none") and len(neu) == 1
    x = np.asarray(neu[0].get_xdata(), dtype=float)
    assert not neu[0].get_clip_on() and list(x[np.isfinite(x)]) == [0, 1]
    assert neu[0].get_zorder() > 2.5                     # ueber der Achslinie wie PGFPlots


def test_marker_mit_markevery_und_kategorien():
    fig, (a1, a2) = vs.figur("zweifeldrig")
    a1.plot(np.arange(101), np.arange(101), marker="o", markevery=10)
    a2.plot(["Holz", "PVC", "PE"], [1, 2, 3], "o-")
    vs.abbildung._marker_ganz_zeigen(fig)                # vorher: ValueError bei Kategorien
    neu = [a for a in a1.get_children() if getattr(a, "get_markevery", None) and a.get_marker() == "o"]
    vs.abbildung.plt.close(fig)
    assert neu and neu[0].get_markevery() == 10


@latex
def test_warnungen_dezimalpunkt_legendenplatz_und_zweimal_speichern(tmp_path):
    fig, ax = vs.figur(legende=2)
    ax.plot([0, 2.5], [0, 1])
    ax.set_xlim(0, 2.5)
    w = vs.abbildung.pruefen(fig)
    assert any("Dezimalkomma" in x for x in w) and any("keine Legende" in x for x in w)
    vs.speichern(fig, tmp_path / "a.pdf", ausgabe=False)
    assert vs.speichern(fig, tmp_path / "b.pdf", ausgabe=False).exists()   # Notebook-Zelle erneut


@latex
def test_speichern_laesst_figur_unveraendert(tmp_path):
    """Marker-Ersatz nur fuer den Speichervorgang: danach Legende mit Marker, neue Grenzen."""
    fig, ax = vs.figur(legende=2)
    (ln,) = ax.plot([0, 5, 10], [0, 5, 10], marker="o", label="A")
    ax.plot([0, 10], [10, 0], label="B")
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); vs.deutsch(ax)
    vs.legende_unten(ax)
    vs.speichern(fig, tmp_path / "a.pdf", ausgabe=False)
    assert ln.get_marker() == "o" and len(ax.get_lines()) == 2
    assert not [a for a in ax.get_children() if getattr(a, "get_label", lambda: "")() == "_nolegend_"
                and getattr(a, "get_marker", lambda: None)() == "o"]
    leg = vs.legende_unten(ax)
    assert leg.legend_handles[0].get_marker() == "o"


def test_deutsch_laesst_kategorien_und_eigene_beschriftung_stehen():
    fig, (a1, a2) = vs.figur("zweifeldrig")
    a1.bar(["Holz", "PVC", "PE"], [0.015, 0.12, 0.06])
    a2.plot([0, 1, 2], [0, 1, 2])
    a2.set_xticks([0.5, 1.5], ["$t_1$", "$t_2$"])
    vs.deutsch(a1); vs.deutsch(a2)
    assert not isinstance(a1.xaxis.get_major_formatter(), vs.KommaFormatter)
    assert not isinstance(a2.xaxis.get_major_formatter(), vs.KommaFormatter)
    assert isinstance(a1.yaxis.get_major_formatter(), vs.KommaFormatter)
    vs.abbildung.plt.close(fig)


@latex
def test_deutsch_vor_dem_zeichnen_farbskala_format_und_ausgeblendete_achsen():
    from matplotlib.ticker import FormatStrFormatter
    fig, ax = vs.figur()
    vs.deutsch(ax)
    ax.bar(["A", "B"], [1, 2])
    assert any("vor dem Zeichnen" in w for w in vs.abbildung.pruefen(fig))
    fig, ax = vs.figur("breit")
    cb = fig.colorbar(ax.contourf(np.arange(25).reshape(5, 5) / 25, levels=6))
    vs.deutsch(ax)
    assert any("Farbskala" in w for w in vs.abbildung.pruefen(fig))
    vs.deutsch(cb.ax)
    assert not any("Dezimalkomma" in w for w in vs.abbildung.pruefen(fig))
    fig, ax = vs.figur()
    ax.plot([0, 1], [0, 1])
    ax.yaxis.set_major_formatter(FormatStrFormatter("%.2f"))
    vs.deutsch(ax)
    assert isinstance(ax.yaxis.get_major_formatter(), vs.KommaFormatter)
    assert ax.yaxis.get_major_formatter()(0.5) == "$0{,}50$" or "0,50" in ax.yaxis.get_major_formatter()(0.5)
    fig, ax = vs.figur()
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_axis_off()
    assert vs.abbildung.pruefen(fig) == []
    vs.abbildung.plt.close("all")


def test_deutsch_laesst_formate_mit_einheit_stehen_und_behaelt_nachkomma():
    from matplotlib.ticker import StrMethodFormatter
    for fmt in ("{x:.0f} %", "{x:.1f} °C", "{x:.0%}"):
        fig, ax = vs.figur()
        ax.yaxis.set_major_formatter(fmt)
        vs.deutsch(ax)
        assert isinstance(ax.yaxis.get_major_formatter(), StrMethodFormatter)
        vs.abbildung.plt.close(fig)
    fig, (a1, a2) = vs.figur("zweifeldrig", sharex=True)
    a2.xaxis.set_major_formatter("{x:.2f}")
    vs.deutsch(a1); vs.deutsch(a2)
    assert a2.xaxis.get_major_formatter().nachkomma == 2
    vs.abbildung.plt.close(fig)
    for fmt in ("{x:,.0f}", "{x:.1e}", "{x}"):            # reine Zahlenformate: umgestellt
        fig, ax = vs.figur()
        ax.xaxis.set_major_formatter(fmt)
        vs.deutsch(ax)
        assert isinstance(ax.xaxis.get_major_formatter(), vs.KommaFormatter), fmt
        vs.abbildung.plt.close(fig)


@latex
def test_eigenes_format_mit_dezimalpunkt_wird_gemeldet():
    fig, ax = vs.figur()
    ax.plot([0, 1000], [0, 1])
    ax.xaxis.set_major_formatter("{x:.1f} kW")
    vs.deutsch(ax)
    w = vs.abbildung.pruefen(fig)
    vs.abbildung.plt.close(fig)
    assert any("eigenes Achsenformat" in x for x in w)


def test_legende_folgt_der_zeichenreihenfolge_auch_mit_errorbar():
    fig, ax = vs.figur(legende=2)
    ax.errorbar([1, 2], [1, 2], yerr=0.2, label="Messung", **vs.reihe(0))
    ax.plot([1, 2], [2, 1], label="Rechnung", **vs.reihe(1))
    h, l = ax.get_legend_handles_labels()
    assert l == ["Rechnung", "Messung"]                  # matplotlib-Reihenfolge
    assert sorted(l, key=lambda x: vs.abbildung._zeichenfolge(ax, h[l.index(x)])) == ["Messung", "Rechnung"]
    vs.abbildung.plt.close(fig)


@latex
def test_dezimalpunkt_warnung_nur_bei_zahlenachsen():
    fig, ax = vs.figur()
    ax.bar(["Szenario 1.1", "Szenario 1.2"], [1, 2])
    vs.deutsch(ax)
    w = vs.abbildung.pruefen(fig)
    vs.abbildung.plt.close(fig)
    assert not any("Dezimalkomma" in x for x in w)


@latex
def test_legende_unten_felder_nebeneinander_getrennt():
    fig, (a1, a2) = vs.figur("breit", legende=2, ncols=2)
    a1.plot([0, 1], [0, 1], label="A"); a1.plot([0, 1], [1, 0], label="B")
    a2.plot([0, 1], [0, 1], label="C"); a2.plot([0, 1], [1, 0], label="D")
    leg = vs.legende_unten(a2)
    vs.abbildung.plt.close(fig)
    assert [t.get_text() for t in leg.get_texts()] == ["C", "D"]


@latex
def test_latex_marker_durchgezogen_und_gefuellt(tmp_path):
    (tmp_path / "m.tex").write_text(r"""\documentclass[border=0pt]{standalone}
\usepackage[schriften]{vfdbstil}
\begin{document}\begin{tikzpicture}\vfdbRahmen{10}{3}
\begin{axis}[vfdb, xmin=0, xmax=2, ymin=0, ymax=2]
\addplot coordinates {(0,0) (2,2)};
\addplot+[only marks, mark=*] coordinates {(1,0.5)};
\addplot+[vfdb reihe=3, mark=o] coordinates {(0.5,1.5) (1.5,1.5)};
\addplot+[mark=*, mark options={solid, fill=white}] coordinates {(0.5,0.5)};
\addplot+[mark=*, mark options={solid, scale=1.2}] coordinates {(1.5,0.5)};
\addplot+[vfdbGrau, mark=*] coordinates {(1.8,0.2)};
\addplot+[vfdb flaeche farbig=1] coordinates {(0,0) (0.4,0.3) (0.8,0)} \closedcycle;
\end{axis}\end{tikzpicture}\end{document}
""", encoding="utf-8")
    bauen = _modul(REPO / "latex" / "bauen.py")
    pdf, _w = bauen.bauen(tmp_path / "m.tex", tmp_path / "aus")
    import pymupdf
    zeichnungen = pymupdf.open(pdf)[0].get_drawings()
    orange = tuple(int(vs.FARBEN[1][i:i + 2], 16) / 255 for i in (1, 3, 5))
    gefuellt = [d for d in zeichnungen if d.get("fill") and
                all(abs(a - b) < 0.01 for a, b in zip(d["fill"], orange))]
    assert gefuellt and all(not d.get("dashes") or d["dashes"].startswith("[]") for d in gefuellt)
    ringe = [d for d in zeichnungen if d.get("color") and not d.get("fill")
             and d["rect"].width < 6 and d["rect"].height < 6]          # leere Marker der Reihe 3
    assert ringe and all(not d.get("dashes") or d["dashes"].startswith("[]") for d in ringe)
    marker = [d for d in zeichnungen if 3 < d["rect"].width < 8 and 3 < d["rect"].height < 8]
    assert len(marker) == 6                              # Reihe 4/5 mit mark options wie in LaTeX.md
    assert all(not d.get("dashes") or d["dashes"].startswith("[]") for d in marker)
    assert any(d.get("fill") and min(d["fill"]) > 0.99 for d in marker)   # Fuellung weiss
    def farbe(i):
        return tuple(int(vs.FARBEN[i][k:k + 2], 16) / 255 for k in (1, 3, 5))
    def gleich(a, b):
        return a is not None and all(abs(x - y) < 0.01 for x, y in zip(a, b))
    assert any(gleich(d.get("fill"), farbe(4)) for d in marker)          # scale=1.2: Reihenfarbe
    grau = tuple(int(vs.farbwert("grau")[k:k + 2], 16) / 255 for k in (1, 3, 5))
    assert any(gleich(d.get("fill"), grau) and gleich(d.get("color"), grau) for d in marker)
    assert any(gleich(d.get("fill"), farbe(0)) and d["rect"].width > 20 for d in zeichnungen)  # Flaeche


@latex
def test_latex_beschriftung_textfarbe_und_fehlerbalken(tmp_path):
    (tmp_path / "f.tex").write_text(r"""\documentclass[border=0pt]{standalone}
\usepackage[schriften]{vfdbstil}
\begin{document}\begin{tikzpicture}\vfdbRahmen{10}{3}
\begin{axis}[vfdb, xmin=0, xmax=4, ymin=0, ymax=40]
\addplot coordinates {(0,0) (4,10)} node[pos=0.5, above] {TextA};
\addplot+[vfdb reihe=5] coordinates {(0,5) (4,15)} node[pos=0.3, below] {TextE};
\addplot+[only marks, mark=*, error bars/.cd, y dir=both, y fixed=3] coordinates {(1,30) (3,30)};
\end{axis}\end{tikzpicture}
\begin{vfdbschema}{10}{3}\draw[vfdb reihe=2] (0,0) -- (40,40) node[right] {TextS};\end{vfdbschema}
\end{document}
""", encoding="utf-8")
    bauen = _modul(REPO / "latex" / "bauen.py")
    pdf, _w = bauen.bauen(tmp_path / "f.tex", tmp_path / "aus")
    import pymupdf
    seite = pymupdf.open(pdf)[0]
    farben = {s["text"]: s["color"] for b in seite.get_text("dict")["blocks"] for z in b.get("lines", [])
              for s in z["spans"] if s["text"].startswith("Text")}
    text = int(vs.STIL["farben"]["text"].lstrip("#"), 16)
    assert farben == {"TextA": text, "TextE": text, "TextS": text}
    balken = [d for d in seite.get_drawings() if d["rect"].width < 0.5 and 5 < d["rect"].height < 15
              and d.get("color") and abs(d["color"][1] - int(vs.FARBEN[2][3:5], 16) / 255) < 0.01]
    assert balken and all(abs(d["width"] - 1.39) < 0.05 and d["dashes"].startswith("[]") for d in balken)


@latex
def test_bauen_meldet_fehler_in_paketoption(tmp_path):
    (tmp_path / "o.tex").write_text(r"""\documentclass[border=0pt]{standalone}
\usepackage[schrift]{vfdbstil}
\begin{document}x\end{document}
""", encoding="utf-8")
    bauen = _modul(REPO / "latex" / "bauen.py")
    with pytest.raises(bauen.BauFehler, match="schrift"):
        bauen.bauen(tmp_path / "o.tex", tmp_path / "aus")


def test_rand_hinweis_nennt_noetigen_rand_und_hinweis_wird_nicht_abgeschnitten():
    fig, ax = vs.figur("standard", unten=14)
    assert "unten=17)" in vs.abbildung._unten_hinweis(fig, 2.3)
    assert vs.hinweis(ax, "Text", xy=(0.5, -0.1), xytext=(0.5, 0.5)).get_annotation_clip() is False
    vs.abbildung.plt.close(fig)


def test_excel_legendentext_mit_tabulator_gleiche_farbe(tmp_path):
    pfad = _mappe(tmp_path, {"Format": "zweifeldrig"},
                  reihen=[["y", "Messung\tA", 1, "Linie", None], ["z", "Messung  A", 2, "Linie", None]],
                  daten={"t": [0, 1], "y": [0, 1], "z": [1, 2]})
    reihen = excel.reihen_lesen(load_workbook(pfad), "zweifeldrig")
    assert {r.legende for r in reihen} == {"Messung A"}


@latex
def test_legende_unten_nimmt_eintraege_aller_felder():
    fig, (a1, a2) = vs.figur("zweifeldrig", legende=2, sharex=True)
    a1.plot([0, 1], [0, 1], label="A")
    a1.plot([0, 1], [1, 0], label="B")
    a2.plot([0, 1], [0, 1], label="A")
    leg = vs.legende_unten(a2)
    vs.abbildung.plt.close(fig)
    assert leg is not None and [t.get_text() for t in leg.get_texts()] == ["A", "B"]


@latex
def test_bauen_fehlermeldung_bei_leerzeichen_im_namen(tmp_path):
    (tmp_path / "Abb 4-3.tex").write_text(r"""\documentclass[border=0pt]{standalone}
\usepackage[schriften]{vfdbstil}
\begin{document}\begin{tikzpicture}\vfdbRahmen{10}{3}
\begin{axis}[vfdb]\addplot table {gibtsnicht.csv};\end{axis}\end{tikzpicture}\end{document}
""", encoding="utf-8")
    bauen = _modul(REPO / "latex" / "bauen.py")
    with pytest.raises(bauen.BauFehler, match="gibtsnicht.csv"):
        bauen.bauen(tmp_path / "Abb 4-3.tex", tmp_path / "aus")


def test_zeilenumbruch_ausserhalb_der_formel_ist_erlaubt():
    assert vs.abbildung.formel_fehler("Zeile 1\nZeile 2 $T$") is None
    assert vs.abbildung.formel_fehler("$T$ in \\si{\\kilo\\watt}\nzweite Zeile") is None
    assert "\\r\\n" in vs.abbildung.formel_fehler("Zeit $t$\r\nin min")


def test_steuerzeichen_im_excel_weg():
    assert vs.abbildung.formel_fehler("Gastemperatur\t$T$ in K", excel=True) is None
    assert "Alt+Enter" in vs.abbildung.formel_fehler("$T_\n1$", excel=True)
    assert "r vor" not in vs.abbildung.formel_fehler("A\x0bB", excel=True)


@latex
def test_zu_langer_achsentitel_wird_gemeldet():
    fig, (a1, a2) = vs.figur("zweifeldrig")
    a1.set_ylabel(r"Rauchgastemperatur $T$ in \si{\degreeCelsius}")
    a2.set_ylabel(r"$T$ in \si{\degreeCelsius}")
    warnungen = vs.abbildung.pruefen(fig)
    vs.abbildung.plt.close(fig)
    assert sum("laenger als die Achse" in w for w in warnungen) == 1
    assert not any("\\\\" in w for w in warnungen)     # Text wie eingegeben, ohne doppelte \


def test_bauen_warnt_bei_kombinierendem_punkt(tmp_path):
    bauen = _modul(REPO / "latex" / "bauen.py")
    (tmp_path / "t.tex").write_text("% Q\u0307 im Kommentar\n\\vfdbPfeilachsen{Rate Q\u0307}\n"
                                    "Wa\u0308rme\n", encoding="utf-8")
    w = bauen._kombinierende_zeichen(tmp_path / "t.tex")
    assert len(w) == 1 and "t.tex:2" in w[0] and "U+0307" in w[0]


@latex
def test_formelbefehl_ausserhalb_klare_meldung(tmp_path):
    fig, ax = vs.figur()
    ax.set_ylabel(r"Rate \dot{Q} in kW")
    with pytest.raises(ValueError, match=r"bitte \$\\dot\{Q\}\$ schreiben"):
        vs.speichern(fig, tmp_path / "a.pdf", ausgabe=False)
    fig, ax = vs.figur()
    ax.plot([0, 1], [0, 1], label=r"Y_\mathrm{CO}")
    ax.plot([0, 1], [1, 0], label="B")
    with pytest.raises(ValueError, match=r"\$Y_\\mathrm\{CO\}\$"):
        vs.legende_unten(ax)
    vs.abbildung.plt.close("all")


@pytest.mark.parametrize("x, nk, erwartet", [
    (0.125, 2, "0,13"), (0.625, 2, "0,63"), (2.5, 0, "3"), (-0.004, 2, "0,00"),
    (0.00012345678912, None, "0,0001234567891"), (999999.99999, None, r"$1\cdot 10^{6}$"),
    (1.235e-5, 2, r"$1{,}24\cdot 10^{-5}$"), (3.5e-9, 0, r"$4\cdot 10^{-9}$"),
    (7.25e-8, 1, r"$7{,}3\cdot 10^{-8}$"),
])
def test_zahl_wie_latex(x, nk, erwartet):
    """Gleiche Ergebnisse wie \\vfdbZahl (kaufmaennisch gerundet, gueltige Stellen)."""
    assert vs.zahl(x, nk) == erwartet


@latex
def test_latex_zahlen_wie_python(tmp_path):
    (tmp_path / "z.tex").write_text(r"""\documentclass[border=0pt]{standalone}
\usepackage[ngerman]{babel}
\usepackage[schriften]{vfdbstil}
\begin{document}
\begin{tikzpicture}\vfdbRahmen{10}{3}
\begin{axis}[vfdb, ymin=0, ymax=2e6, ytick distance=5e5, xmin=0, xmax=0.0003, xtick distance=0.00005]
\addplot coordinates {(0,0) (0.0003,2e6)};\end{axis}\end{tikzpicture}
\begin{tikzpicture}\vfdbRahmen{10}{3}
\begin{axis}[vfdb, ymin=0, ymax=0.0003, xmin=0.0001, xmax=0.0005, xtick distance=0.00005]
\addplot coordinates {(0.0001,0) (0.0005,0.0003)};\end{axis}\end{tikzpicture}
A\vfdbZahl{0.00012345678912}B{\pgfkeys{/tikz/vfdb nachkomma=2}\vfdbZahl{0.125}C\vfdbZahl{-0.004}}D%
{\pgfkeys{/tikz/vfdb nachkomma=0}\vfdbZahl{2.5}}E{\pgfkeys{/tikz/vfdb nachkomma=2}\vfdbZahl{1.235e-5}}F
\end{document}
""", encoding="utf-8")
    bauen = _modul(REPO / "latex" / "bauen.py")
    pdf, warnungen = bauen.bauen(tmp_path / "z.tex", tmp_path / "aus")
    text = _pdf_text(pdf).replace("\n", " ")
    assert "500000" not in text                       # ganze y-Achse als a*10^n
    assert "0,00005" not in text                      # Teilstrich 5e-5 -> Achse als a*10^n (wie Python)
    assert "0,00015" in text                          # Teilstriche 1e-4 ... 5e-4 ausgeschrieben
    werte = re.search(r"A(.*?)B(.*?)C(.*?)D(.*?)E(.*?)F", text.replace(" ", ""))
    assert werte and werte.groups()[:4] == ("0,0001234567891", "0,13", "0,00", "3")
    assert werte.group(5).startswith("1,24")          # Mantisse kaufmaennisch gerundet
    assert any("kein Format" in w for w in warnungen)  # Text neben dem Diagramm: Breite weicht ab


@latex
def test_latex_teilstriche_ausdruck_rauschen_schaetzung(tmp_path):
    """tick distance als Ausdruck (5*60), Rechenrauschen bei grossen Werten (999000.1),
    geschaetzter Abstand ohne tick distance (0 ... 0,0009 -> ausgeschrieben wie Python)."""
    (tmp_path / "z.tex").write_text(r"""\documentclass[border=0pt]{standalone}
\usepackage[ngerman]{babel}
\usepackage[schriften]{vfdbstil}
\begin{document}
\begin{tikzpicture}\vfdbRahmen{10}{3}
\begin{axis}[vfdb, xmin=0, xmax=3600, xtick distance=5*60, ymin=999000, ymax=1001000, ytick distance=500]
\addplot coordinates {(0,999000) (3600,1001000)};\end{axis}\end{tikzpicture}
\begin{tikzpicture}\vfdbRahmen{10}{3}
\begin{axis}[vfdb, xmin=0, xmax=0.0009, ymin=0.00005, ymax=0.0009]
\addplot coordinates {(0,0.00005) (0.0009,0.0009)};\end{axis}\end{tikzpicture}
\begin{tikzpicture}\vfdbRahmen{10}{3}
\begin{axis}[vfdb, xmin=0, xmax=0.0004, ymin=0, ymax=1]
\addplot coordinates {(0,0) (0.0004,1)};\end{axis}\end{tikzpicture}
\begin{tikzpicture}\vfdbRahmen{10}{3}
\begin{axis}[vfdb]
\addplot coordinates {(99990,0) (100010,1)};\end{axis}\end{tikzpicture}
\begin{tikzpicture}\vfdbRahmen{10}{3}
\begin{axis}[vfdb, xmin=0, xmax=999999]
\addplot coordinates {(0,0) (999999,1)};\end{axis}\end{tikzpicture}
\end{document}
""", encoding="utf-8")
    bauen = _modul(REPO / "latex" / "bauen.py")
    pdf, _w = bauen.bauen(tmp_path / "z.tex", tmp_path / "aus")
    text = _pdf_text(pdf).replace("\n", " ")
    assert "3600" in text and "300" in text           # x ausgeschrieben, nicht 3,6*10^3
    assert "9,995" in text and "990001" not in text   # y als a*10^5, ohne Rauschen
    assert "0,0002" in text or "0,0001" in text       # 0 ... 0,0009 ausgeschrieben
    assert "0,00005" not in text                      # 0 ... 0,0004: Teilstrich 5e-5 -> a*10^n
    assert "99992" in text and "99991" not in text    # ohne Grenzen: einheitlich, ohne Rauschen
    assert "1000000" not in text and "900000" not in text   # Teilstrich 10^6 knapp ausserhalb


@latex
def test_excel_latex_fehler_mit_zelle(tmp_path):
    """Ein Text, den erst LaTeX ablehnt (die Vorpruefung laesst ihn durch)."""
    excel.text_pruefen(r"Temperatur \foo in K", "Test")
    pfad = _mappe(tmp_path, {"y-Achsentitel": r"Temperatur \foo in K"})
    with pytest.raises(excel.ExcelFehler, match=r"y-Achsentitel \(B\d+\): LaTeX kann den Text nicht setzen"):
        excel.abbildung_aus_excel(pfad, tmp_path, ausgabe=False)


def test_excel_formelbefehl_ausserhalb_von_dollar(tmp_path):
    pfad = _mappe(tmp_path, {"y-Achsentitel": r"Koeffizient \alpha in kW/s²"})
    with pytest.raises(excel.ExcelFehler, match=r"\\alpha steht außerhalb"):
        excel.abbildung_aus_excel(pfad, tmp_path, ausgabe=False)


def test_excel_spalte_nur_formeln_ohne_wert(tmp_path):
    pfad = _mappe(tmp_path)
    wb = load_workbook(pfad)
    for r in range(2, 5):
        wb["Daten"][f"A{r}"] = f"={r}*1"
        wb["Daten"][f"B{r}"] = f"=A{r}*2"
    wb.save(pfad)
    with pytest.raises(excel.ExcelFehler, match="Formel ohne berechneten Wert"):
        excel.abbildung_aus_excel(pfad, tmp_path, ausgabe=False)


@latex
@pytest.mark.parametrize("skript, pdf", [
    ("nominelle_temperaturzeitkurven.py", "nominelle_temperaturzeitkurven.pdf"),
    ("t2_brandentwicklung.py", "t2_brandentwicklung.pdf"),
    ("schema_brandphasen.py", "schema_brandphasen.pdf"),
])
def test_python_beispiele_laufen(tmp_path, skript, pdf):
    kopie = tmp_path / "python" / skript
    kopie.parent.mkdir()
    shutil.copy(REPO / "beispiele" / "python" / skript, kopie)
    lauf = subprocess.run([sys.executable, str(kopie)], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    assert lauf.returncode == 0, lauf.stderr
    assert "WARNUNG" not in lauf.stdout
    neu = tmp_path / "pdf" / pdf
    assert _pdf_mm(neu) == pytest.approx(_pdf_mm(REPO / "beispiele" / "pdf" / pdf), abs=0.05)


# --- LaTeX-Paket -----------------------------------------------------------------------
def test_latex_werte_aktuell():
    mod = _modul(REPO / "latex" / "erzeuge_werte.py")
    assert mod.ZIEL.read_text(encoding="utf-8") == mod.inhalt(), \
        "latex/vfdbstil-werte.tex veraltet - python latex/erzeuge_werte.py ausfuehren"


@latex
@pytest.mark.parametrize("tex, python_pdf", [
    ("schema_brandphasen_tikz", "schema_brandphasen"),
    ("nominelle_temperaturzeitkurven_pgfplots", "nominelle_temperaturzeitkurven"),
])
def test_latex_beispiel_gleiche_groesse_wie_python(tmp_path, tex, python_pdf):
    bauen = _modul(REPO / "latex" / "bauen.py")
    pdf, warnungen = bauen.bauen(REPO / "beispiele" / "latex" / f"{tex}.tex", tmp_path)
    assert not warnungen
    assert _pdf_mm(pdf) == pytest.approx(_pdf_mm(REPO / "beispiele" / "pdf" / f"{python_pdf}.pdf"), abs=0.05)


@latex
def test_latex_zahlen_und_log_achse(tmp_path):
    (tmp_path / "t.tex").write_text(r"""\documentclass[border=0pt]{standalone}
\usepackage[ngerman]{babel}
\usepackage[schriften]{vfdbstil}
\begin{document}
\vfdbZahl{-0.5};\vfdbZahl{12345.678};\vfdbZahl{100000};\vfdbZahl{0.125};\vfdbZahl{0}
\begin{tikzpicture}\begin{axis}[vfdb, ymode=log, ymin=1, ymax=1000]
\addplot coordinates {(0,1) (1,1000)};\end{axis}\end{tikzpicture}
\end{document}
""", encoding="utf-8")
    bauen = _modul(REPO / "latex" / "bauen.py")
    pdf, _w = bauen.bauen(tmp_path / "t.tex", tmp_path / "aus")
    text = _pdf_text(pdf)
    for erwartet in ("\u22120,5", "12345,678", "100000", "0,125"):
        assert erwartet in text
    assert "2,3" not in text and "4,61" not in text      # keine ln-Werte an der log-Achse


@latex
def test_latex_unbekanntes_format_meldet_fehler(tmp_path):
    (tmp_path / "t.tex").write_text(r"""\documentclass[border=0pt]{standalone}
\usepackage[schriften]{vfdbstil}
\begin{document}\begin{vfdbschema}[Standard]{10}{3}\end{vfdbschema}\end{document}
""", encoding="utf-8")
    bauen = _modul(REPO / "latex" / "bauen.py")
    with pytest.raises(bauen.BauFehler, match="Unbekanntes Format"):
        bauen.bauen(tmp_path / "t.tex", tmp_path / "aus")


def test_bauen_meldet_fehlende_dateien(tmp_path):
    bauen = _modul(REPO / "latex" / "bauen.py")
    assert bauen.main([str(tmp_path / "gibtsnicht*.tex")]) == 1


def test_bauen_meldungen_mit_folgezeilen():
    """Folgezeilen "(Font) ..." und "<argument> ..." gehoeren zur Meldung, Dateimarken nicht;
    nach 79 Bytes (nicht Zeichen) umbrochene Zeilen werden ohne Leerzeichen verbunden."""
    bauen = _modul(REPO / "latex" / "bauen.py")
    zeilen = ["./t.tex:6: Undefined control sequence.", r"<argument> \minuten", "",
              "LaTeX Font Warning: Font shape `TU/x/m/n' undefined",
              "(Font)              using `TU/y/m/n' instead on input line 7.",
              "(./datei.tex) [1]", "",
              "Package test Warning: Größenänderungen sind nicht vorgesehen, bitte die Abbil",
              "dung prüfen.", ""]
    assert len(zeilen[7]) < 79 <= len(zeilen[7].encode("utf-8"))
    fehler = bauen._meldungen(zeilen, lambda z: re.match(r"^\S+:\d+: ", z))
    assert fehler == [r"./t.tex:6: Undefined control sequence. <argument> \minuten"]
    warn = bauen._meldungen(zeilen, lambda z: "Warning" in z)
    assert warn[0].endswith("instead on input line 7.") and "datei.tex" not in warn[0]
    assert "Abbildung prüfen" in warn[1]


@pytest.mark.skipif(shutil.which("xelatex") is None, reason="XeLaTeX nicht installiert")
def test_vorlage_mit_xelatex(tmp_path):
    for name in ("vfdbstil.sty", "vfdbstil-werte.tex", "vorlage_schema.tex"):
        shutil.copy(REPO / "latex" / name, tmp_path)
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", "vorlage_schema.tex"],
                       cwd=tmp_path, capture_output=True, text=True, errors="replace", timeout=300)
    assert r.returncode == 0, r.stdout[-2000:]


@latex
def test_latex_nachkomma_legende_marker_unterordner(tmp_path):
    (tmp_path / "daten").mkdir()
    (tmp_path / "daten" / "m.csv").write_text("t;A\n0;0.25\n1;0.75\n", encoding="utf-8")
    (tmp_path / "t.tex").write_text(r"""\documentclass[border=0pt]{standalone}
\usepackage[ngerman]{babel}
\usepackage[schriften]{vfdbstil}
\begin{document}
\begin{tikzpicture}\vfdbRahmen{\vfdbRandEintraege{4}}{3}
\begin{axis}[vfdb, xmin=123400, xmax=123500, xtick distance=20, ymin=0, ymax=1,
  ytick distance=0.25, vfdb nachkomma y=2, vfdb legende=4]
\addplot+[mark=o] table[x expr=123400+100*\thisrow{t}, y=A, col sep=semicolon] {daten/m.csv};
\addlegendentry{A}
\addplot coordinates {(123400,0) (123500,1)}; \addlegendentry{B}
\addplot coordinates {(123400,1) (123500,0)}; \addlegendentry{C}
\addplot coordinates {(123400,0.5) (123500,0.5)}; \addlegendentry{D}
\end{axis}\end{tikzpicture}
\end{document}
""", encoding="utf-8")
    bauen = _modul(REPO / "latex" / "bauen.py")
    pdf, warnungen = bauen.bauen(tmp_path / "t.tex", tmp_path / "aus")
    text = _pdf_text(pdf)
    assert "123420" in text and "123420," not in text      # kein Rechenrauschen, x ohne Nachkomma
    assert "0,25" in text and "0,50" in text                # y mit 2 Nachkommastellen
    f, leg = vs.FORMATE["standard"], vs.STIL["legende"]
    rand = leg["abstand_mm"] + 2 * leg["zeile_mm"] + leg["zuschlag_unten_mm"]   # 4 Eintraege, 2 Zeilen
    assert _pdf_mm(pdf)[1] == pytest.approx(f["rand_oben_mm"] + f["achse_h_mm"] + rand, abs=0.05)
