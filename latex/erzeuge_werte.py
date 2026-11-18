"""Erzeugt latex/vfdbstil-werte.tex aus stil/stil.yaml (einzige Quelle der Stilwerte).

    python latex/erzeuge_werte.py          # schreibt die Datei
    python latex/erzeuge_werte.py --pruefen  # Fehlercode 1, wenn die Datei veraltet ist
"""
from __future__ import annotations

import sys
from pathlib import Path

from vfdb_stil import stil as S

ZIEL = Path(__file__).resolve().parent / "vfdbstil-werte.tex"

# Strichmuster von matplotlib (rcParams-Vorgaben lines.dashed_pattern usw.), in Vielfachen
# der Linienstaerke (lines.scale_dashes = True) - damit sehen TikZ und Python gleich aus.
MPL_MUSTER = {"gestrichelt": [3.7, 1.6], "gepunktet": [1.0, 1.65],
              "strichpunkt": [6.4, 1.6, 1.0, 1.6], "durchgezogen": None}


def _pt(x: float) -> str:
    return f"{x:.3f}".rstrip("0").rstrip(".") + "pt"


def strichmuster(eintrag: dict, lw: float) -> str:
    """TikZ-Strichmuster eines Linienstils aus stil.yaml fuer Linienstaerke lw (pt)."""
    muster = eintrag.get("muster") or MPL_MUSTER.get(eintrag["name"])
    if not muster:
        return "solid"
    teile = [f"{'on' if i % 2 == 0 else 'off'} {_pt(m * lw)}" for i, m in enumerate(muster)]
    return "dash pattern=" + " ".join(teile)


def inhalt() -> str:
    st = S.STIL
    z = ["% Automatisch erzeugt aus stil/stil.yaml mit latex/erzeuge_werte.py.",
         "% Nicht von Hand aendern - Werte nur in stil/stil.yaml pflegen.",
         "% SPDX-License-Identifier: MIT",
         rf"\def\vfdbStilVersion{{{st['version']}}}", "",
         "% Farben (feste Reihenfolge)"]
    for i, f in enumerate(S.FARBEN, start=1):
        z.append(rf"\definecolor{{vfdbFarbe{i}}}{{HTML}}{{{f.lstrip('#').upper()}}}"
                 f"  % {S.FARBNAMEN[i - 1]}")
    for name, wert in (("Text", S.TEXT), ("Grau", S.GRAU), ("GrauHell", S.GRAU_HELL),
                       ("GrauFlaeche", S.GRAU_FLAECHE)):
        z.append(rf"\definecolor{{vfdb{name}}}{{HTML}}{{{wert.lstrip('#').upper()}}}")
    z += [rf"\def\vfdbFlaecheDeckkraft{{{S.FLAECHE_DECKKRAFT}}}", "",
          "% Schrift",
          rf"\def\vfdbSchriftText{{{S.SCHRIFT_TEXT}}}",
          rf"\def\vfdbSchriftFormel{{{S.SCHRIFT_FORMEL}}}",
          rf"\def\vfdbPtBeschriftung{{{S.PT_BESCHRIFTUNG:g}}}",
          rf"\def\vfdbPtTicks{{{S.PT_TICKS:g}}}",
          rf"\def\vfdbPtLegende{{{S.PT_LEGENDE:g}}}",
          rf"\def\vfdbZeilenabstand{{{S.ZEILENABSTAND:g}}}", "",
          "% Formate (Masse in mm): \\vfdb@<format>@<groesse>"]
    for name, f in S.FORMATE.items():
        for k, v in f.items():
            z.append(rf"\@namedef{{vfdb@{name}@{k.replace('_mm', '')}}}{{{v:g}}}")
    a, lin, p, leg, sc, zl = S.ACHSE, S.LINIEN, S.PFEILE, S.LEGENDE, S.SCHEMA, S.ZAHLEN
    hl = lin["hilfslinie"]

    def farbe(name: str, neu: str) -> str:
        hexwert = S.farbwert(name).lstrip("#").upper()
        return rf"\definecolor{{{neu}}}{{HTML}}{{{hexwert}}}  % {name}"

    def wahr(b: bool) -> str:
        return "true" if b else "false"

    z += ["", "% Zuordnung der Farben",
          farbe(a["farbe"], "vfdbAchsenfarbe"),
          farbe(a["gitter"]["farbe"], "vfdbGitterfarbe"),
          farbe(hl["farbe"], "vfdbHilfsfarbe"),
          farbe(p["farbe"], "vfdbPfeilfarbe"),
          "", "% Zahlen",
          rf"\def\vfdbSisetup{{{zl['siunitx']}}}",
          rf"\def\vfdbDezimalkomma{{{wahr(zl['dezimalzeichen'] == ',')}}}",
          # echtes Minus als \textminus (funktioniert auch ohne Unicode-Schrift)
          rf"\def\vfdbMinuszeichen{{{chr(92) + 'textminus' if zl['minuszeichen'] == chr(0x2212) else '-'}}}",
          rf"\def\vfdbExponentAb{{{zl['exponent_ab']:g}}}",
          rf"\def\vfdbExponentUnter{{{zl['exponent_unter']:g}}}",
          "", "% Achsen (Schalter)",
          rf"\def\vfdbTickAusrichtung{{{'inside' if a['ticks']['richtung'] == 'innen' else 'outside'}}}",
          rf"\def\vfdbNebenticks{{{wahr(a['ticks']['nebenticks'])}}}",
          rf"\def\vfdbGitter{{{wahr(a['gitter']['sichtbar'])}}}",
          rf"\def\vfdbObenRechts{{{1 if a['oben_rechts'] else 0}}}",
          rf"\def\vfdbAchseUeberDaten{{{wahr(not a['gitter']['hinter_daten'])}}}",
          rf"\def\vfdbDatenrand{{{a['datenrand']:g}}}",
          rf"\def\vfdbFormatliste{{{', '.join(S.FORMATE)}}}",
          rf"\def\vfdbLegendeRahmen{{{'vfdbText' if leg['rahmen'] else 'none'}}}",
          rf"\def\vfdbMassBeidseitig{{{1 if p['mass'].get('beidseitig') else 0}}}",
          "", "% Achsen, Linien, Pfeile (pt) und Abstaende (mm)",
          rf"\def\vfdbAchseLinie{{{_pt(a['linie_pt'])}}}",
          rf"\def\vfdbTickLaenge{{{_pt(a['ticks']['laenge_pt'])}}}",
          rf"\def\vfdbTickLinie{{{_pt(a['ticks']['linie_pt'])}}}",
          rf"\def\vfdbTickAbstand{{{_pt(a['ticks']['abstand_pt'])}}}",
          rf"\def\vfdbGitterLinie{{{_pt(a['gitter']['linie_pt'])}}}",
          rf"\def\vfdbTitelAbstandY{{{a['titel_abstand_y_mm']:g}mm}}",
          rf"\def\vfdbTitelAbstandX{{{a['titel_abstand_x_mm']:g}mm}}",
          rf"\def\vfdbDatenLinie{{{_pt(lin['daten_pt'])}}}",
          rf"\def\vfdbDuennLinie{{{_pt(lin['duenn_pt'])}}}",
          rf"\def\vfdbHilfsLinie{{{_pt(lin['hilfslinie']['linie_pt'])}}}",
          rf"\def\vfdbHilfsMuster{{{strichmuster({'name': hl['stil']}, hl['linie_pt'])}}}",
          # Marker: matplotlib-Groesse = Durchmesser, pgfplots "mark size" = Radius
          rf"\def\vfdbMarkerRadius{{{_pt(lin['marker_pt'] / 2)}}}",
          rf"\def\vfdbPfeilLinie{{{_pt(p['linie_pt'])}}}",
          # Pfeilspitzen (arrows.meta): Laenge/Breite + 1 x Linienstaerke, wie die umrandete
          # Spitze von matplotlib
          rf"\def\vfdbSpitzeAchse{{{_pt(p['achse']['spitze_laenge_pt'])} 1}}",
          rf"\def\vfdbSpitzeHinweis{{{_pt(p['hinweis']['spitze_laenge_pt'])} 1}}",
          rf"\def\vfdbSpitzeMass{{{_pt(p['mass']['spitze_laenge_pt'])} 1}}",
          # Abstand Hinweispfeil - Text: matplotlib rahmt den Text mit 2 pt Luft (pad 4 pt)
          rf"\def\vfdbHinweisAbstandText{{{_pt(p['hinweis']['abstand_text_pt'] + 2.0)}}}",
          rf"\def\vfdbHinweisAbstandZiel{{{_pt(p['hinweis']['abstand_ziel_pt'])}}}",
          rf"\def\vfdbLegendeAbstand{{{leg['abstand_mm']:g}mm}}",
          rf"\def\vfdbLegendeZeile{{{leg['zeile_mm']:g}mm}}",
          rf"\def\vfdbLegendeAbstandMM{{{leg['abstand_mm']:g}}}",
          rf"\def\vfdbLegendeZeileMM{{{leg['zeile_mm']:g}}}",
          rf"\def\vfdbLegendeZuschlagMM{{{leg['zuschlag_unten_mm']:g}}}",
          rf"\def\vfdbLegendeSpaltenHoechstens{{{max(int(v) for v in leg['spalten'].values())}}}",
          rf"\def\vfdbLegendeSpaltenAbEintraegen{{{max(int(k) for k in leg['spalten'])}}}",
          *(rf"\@namedef{{vfdb@spalten@{int(k)}}}{{{int(v)}}}" for k, v in sorted(leg['spalten'].items())),
          # em der Legendenschrift als pt (PGFPlots wertet em sonst in der Grundschrift aus)
          rf"\def\vfdbLegendeSymbol{{{_pt(leg['symbollaenge_em'] * S.PT_LEGENDE)}}}",
          rf"\def\vfdbLegendeTextabstand{{{_pt(leg['textabstand_em'] * S.PT_LEGENDE)}}}",
          rf"\def\vfdbLegendeSpalten{{{_pt(leg['spaltenabstand_em'] * S.PT_LEGENDE)}}}",
          rf"\def\vfdbPhasenAbstand{{{sc['phasenbalken_mm']:g}}}",
          rf"\def\vfdbPhasengrenzeOben{{{sc['phasengrenze_oben_mm']:g}}}",
          rf"\def\vfdbPhasengrenzeUnten{{{sc['phasengrenze_unten_mm']:g}}}",
          rf"\def\vfdbPhasentext{{{sc['phasentext_mm']:g}}}",
          "", "% Linienstile der Reihen (fuer Datenlinien)"]
    for i in range(1, len(S.FARBEN) + 1):
        e = st["linienstile"][i - 1] if i <= len(st["linienstile"]) else {"name": "durchgezogen"}
        z.append(rf"\@namedef{{vfdb@strich@{i}}}{{{strichmuster(e, lin['daten_pt'])}}}")
    z.append(rf"\def\vfdbAnzahlFarben{{{len(S.FARBEN)}}}")
    return "\n".join(z) + "\n"


if __name__ == "__main__":
    neu = inhalt()
    if "--pruefen" in sys.argv:
        alt = ZIEL.read_text(encoding="utf-8") if ZIEL.exists() else ""
        if alt != neu:
            print(f"{ZIEL.name} ist veraltet - python latex/erzeuge_werte.py ausfuehren")
            sys.exit(1)
        print(f"{ZIEL.name} ist aktuell")
    else:
        ZIEL.write_text(neu, encoding="utf-8", newline="\n")
        print(ZIEL)
