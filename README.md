# 🏗️ PipeCraft – Feld-Rechner Rohrleitungsbau

Ein Streamlit-Werkzeug für Schweißer und Vorrichter im Rohrleitungs-/Pipelinebau:
Sägelängen, Rohr-Geometrie und Abwicklungen, Schweiß-Nachschlagewerte und ein
Lernmodul für das Fallnaht-Schweißen (Stovepipe) mit Zellulose-Elektroden.

> Alle Zahlen sind **Richtwerte**. Verbindlich sind die freigegebene WPS, die
> einschlägige Norm (API 1104, ISO/EN) und die Projektspezifikation.

## Bereiche

| Bereich | Inhalt |
|---|---|
| 🪚 **Smarte Säge** | Sägelänge aus Fertigmaß, Fitting-/Spalt-/Dichtungsabzüge, Schnittliste, Verschnitt-Optimierung |
| 📐 **Geometrie** | 2D-/3D-Etage, Standard-Bogen, Segment-Bogen, Stutzen-Abwicklung (Sattelschnitt), schräger/versetzter Stutzen, Rohr-Verschneidung, Passstück 3D, Keilspalt |
| 🔥 **Schweißen** | a-/z-Maß, Nahtvorbereitung, Vorwärmen (Pipeline-Chart + EN 1011-2) / PWHT |
| 🧮 **Rechner** | Dreiecksrechner, Kreisteiler / Lochbild |
| 🎓 **Fallnaht** | Lern- und Nachschlagemodul: Überblick (Elektrode & Polarität), Nahtvorbereitung, Elektrodenhaltung & Führungstechnik, Strom & Lagen (Wurzelspalt & Keyhole), Vorwärmen, Fehler & RT-Auswertung |
| 📚 **Smart Data** | Flansch- & Schraubenmaße (EN 1092-1), Rohrmaße / Schedule (ASME B36.10M), Hebezeug / Anschlagmittel, PN ↔ Class |

## Lokal starten

```
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Tests

```
pytest -q
```
