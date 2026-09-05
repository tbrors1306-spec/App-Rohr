# 🏗️ PipeCraft – Feld-Rechner Rohrleitungsbau

Ein Streamlit-Werkzeug für Schweißer und Vorrichter im Rohrleitungs-/Pipelinebau:
Sägelängen, Rohr-Geometrie und Abwicklungen, Nachschlagewerte und ein
Lernmodul für das Fallnaht-Schweißen (Stovepipe) mit Zellulose-Elektroden.

> Alle Zahlen sind **Richtwerte**. Verbindlich sind die freigegebene WPS, die
> einschlägige Norm (API 1104, ISO/EN) und die Projektspezifikation.

## Bereiche

| Bereich | Inhalt |
|---|---|
| 🪚 **Smarte Säge** | Sägelänge aus Fertigmaß, Fitting-/Spalt-/Dichtungsabzüge, Schnittliste, Verschnitt-Optimierung |
| 🧭 **Rohrfolge-Skizze** | Leitung als **Bauteilkette** eingeben (eine Zeile je Bauteil, in Einbaureihenfolge) → isometrische Skizze mit Kompassrose. **Bemaßung wie auf einer Fertigungsiso**: jedes Rohr bekommt seine eigene Maßlinie dicht am Rohr, darüber das Gesamtmaß je gerader Lauf; Formteile bleiben ohne Maß. **Versprung** (Höhen- und Seitenversatz in einem Zug) als eigenes Bauteil, mit schraffierter Versatzfläche und einzeln bemaßten Schenkeln. **Ansichten** (Aufmaß & Sägen / Schweißen / Montage / Alles) statt alles gleichzeitig. **Nahtliste** mit Nummern WF1…WFn, Art, DN, Ort, Koordinaten und Werkstatt/Baustelle. **Positionsnummern** als Ballons, dazu eine Stückliste mit Wanddicke (Schedule), Werkstoff und Norm. **Abzweige** mit eigener DN und Anrissmaß. Sägeliste standardmäßig als **Achsmaß** – Bögen, Flansche, T-Stücke und Reduzierungen werden sofort abgezogen. Ausgabe als **A3-Feldzettel** (PDF/PNG) mit Rahmen, Rasterbezügen, Legende und Titelblock. Näherung, keine Fertigungsiso. |
| 📐 **Geometrie** | 2D-/3D-Etage, Standard-Bogen, Segment-Bogen, Stutzen-Abwicklung (Sattelschnitt), schräger/versetzter Stutzen, Rohr-Verschneidung, Passstück 3D, Keilspalt |
| 🧮 **Rechner** | Dreiecksrechner, Kreisteiler / Lochbild |
| 🎓 **Fallnaht** | Lern- und Nachschlagemodul: Überblick (Elektrode & Polarität), Nahtvorbereitung, Elektrodenhaltung & Führungstechnik, Strom & Lagen (Wurzelspalt & Keyhole), Vorwärmen, Fehler & RT-Auswertung |
| 📚 **Smart Data** | Flansch- & Schraubenmaße (EN 1092-1), Rohrmaße / Schedule (ASME B36.10M), Fitting-Einbaumaße je DN (Vorbau, Flansch-b, T-Stück, Reduzierung) |

## Lokal starten

```
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Tests

```
pytest -q
```

## Lizenz

Apache License 2.0 – siehe [LICENSE](LICENSE).
