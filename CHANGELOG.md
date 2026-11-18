# Änderungen

Änderungen an den Stilwerten verändern alle damit erzeugten Abbildungen; sie werden hier deshalb einzeln aufgeführt. Versionsnummern nach [Semantic Versioning](https://semver.org/lang/de/): Änderungen an Stilwerten erhöhen mindestens die zweite Stelle.

## 0.1.0 – Entwurf (noch nicht veröffentlicht)

Erste Fassung zur Abstimmung in Referat 4.

- Stilvorgaben und `stil/stil.yaml`, abgeleitet aus den Abbildungen von Kapitel 4: Formate standard / zweifeldrig / breit, Schrift TeX Gyre Heros / Fira Math (9 / 8 pt), Farb- und Linienstilreihenfolge (8 Reihen), Achsen, Legende, Pfeile, Schemata.
- Python-Paket `vfdb_stil` (matplotlib, LuaLaTeX) mit Prüfung von Maßen und Beschriftung.
- Excel als Datenquelle: Vorlage und Befehl `vfdb-abbildung`.
- LaTeX-Paket `vfdbstil.sty` für TikZ-Schemata und PGFPlots-Diagramme.
- Office-Vorlagen (Stufe B) für Excel und PowerPoint, Schrift Arial.
- Rechnerische Farbprüfung `vfdb-farbpruefung`.

Abweichungen von den Kapitel-4-Abbildungen: Legenden zeilenweise statt spaltenweise; Linienstil der Reihe 8 vorläufig durchgezogen.
