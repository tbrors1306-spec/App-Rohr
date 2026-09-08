"""Die Anreisstabelle muss beim Ausdrucken vollstaendig sein.

Auf der Baustelle wird die Seite ueber den Browser gedruckt ("Teilen ->
Drucken" bzw. "Als PDF sichern"). st.dataframe ist aber ein Scroll-Fenster
mit fester Hoehe: Streamlit baut nur die Zeilen auf, die gerade sichtbar
sind. Was man wegscrollt, steht nicht auf der Seite - und was nicht auf der
Seite steht, kann kein Drucker mitnehmen. Bei 36 Stationen kaeme rund ein
Drittel aufs Blatt, ohne jeden Hinweis auf den Rest.

Genau das ist die gefaehrliche Sorte Fehler: sie faellt erst am Rohr auf.
Darum der Haken "Zum Ausdrucken" - der schaltet auf eine feste Tabelle um,
in der jede Station steht. Dieser Test haelt beides fest.
"""
import unittest

import matplotlib
matplotlib.use("Agg")

import pandas as pd

import streamlit_app as app


class FakeSt:
    """Nur so viel Streamlit, wie die Funktion anfasst."""

    def __init__(self, haken):
        self.haken = haken
        self.dataframe_aufrufe = []
        self.table_aufrufe = []
        self.captions = []
        self.checkbox_kwargs = None

    def checkbox(self, label, **kw):
        self.checkbox_label = label
        self.checkbox_kwargs = kw
        return self.haken

    def dataframe(self, daten, **kw):
        self.dataframe_aufrufe.append((daten, kw))

    def table(self, daten):
        self.table_aufrufe.append(daten)

    def caption(self, text):
        self.captions.append(text)


class TestDrucktabelle(unittest.TestCase):

    def setUp(self):
        self.echt = app.st
        # 36 Stationen - die groesste Einstellung, die die Werkzeuge anbieten
        self.daten = pd.DataFrame({
            "Nr": list(range(36)),
            "Winkel": ["%d Grad" % (i * 10) for i in range(36)],
            "Umfangsmass s (mm)": [i * 14.6928 for i in range(36)],
            "Abtrag h (mm)": [i * 0.6543 for i in range(36)],
        })

    def tearDown(self):
        app.st = self.echt

    def _lauf(self, haken):
        app.st = FakeSt(haken)
        app._anreiss_tabelle(self.daten, "druck_test", 260)
        return app.st

    def test_ohne_haken_bleibt_das_scroll_fenster(self):
        """Auf dem Handy soll die Tabelle kompakt bleiben - Normalfall."""
        st = self._lauf(False)
        self.assertEqual(len(st.dataframe_aufrufe), 1)
        self.assertEqual(st.table_aufrufe, [])
        _, kw = st.dataframe_aufrufe[0]
        self.assertEqual(kw["height"], 260, "die Scroll-Hoehe muss erhalten bleiben")

    def test_mit_haken_steht_jede_station_auf_dem_blatt(self):
        """Der eigentliche Zweck: nichts darf im Ausdruck fehlen."""
        st = self._lauf(True)
        self.assertEqual(st.dataframe_aufrufe, [],
                         "im Druckmodus darf kein Scroll-Fenster mehr kommen")
        self.assertEqual(len(st.table_aufrufe), 1)
        gedruckt = st.table_aufrufe[0]
        self.assertEqual(len(gedruckt), 36)
        self.assertEqual(list(gedruckt["Nr"]), list(range(36)))
        self.assertEqual(list(gedruckt.columns), list(self.daten.columns))

    def test_masse_stehen_auf_zehntel_auf_dem_blatt(self):
        """s = 14.6928 mm liest am Massband niemand ab - 14.7 schon. st.table
        zeigt Kommazahlen von sich aus mit vier Stellen, darum feste Texte."""
        st = self._lauf(True)
        gedruckt = st.table_aufrufe[0]
        self.assertEqual(gedruckt["Umfangsmass s (mm)"].iloc[1], "14.7")
        self.assertEqual(gedruckt["Abtrag h (mm)"].iloc[1], "0.7")

    def test_stationsnummer_bleibt_eine_ganze_zahl(self):
        """Aus Station 7 darf keine "7.0" werden."""
        st = self._lauf(True)
        self.assertEqual(list(st.table_aufrufe[0]["Nr"]), list(range(36)))

    def test_kein_zeilenzaehler_im_ausdruck(self):
        """st.table kennt kein hide_index - ohne leeren Index stuende neben
        der Stationsnummer noch eine zweite, sinnlose Zahl."""
        st = self._lauf(True)
        self.assertEqual(set(st.table_aufrufe[0].index), {""})

    def test_die_urspruenglichen_daten_bleiben_unberuehrt(self):
        """Gerundet wird nur fuers Blatt - die Zeichnung rechnet weiter mit
        den vollen Werten."""
        self._lauf(True)
        self.assertAlmostEqual(self.daten["Umfangsmass s (mm)"][1], 14.6928)

    def test_der_haken_erklaert_sich(self):
        """Jedes Bedienelement in der App hat einen Hilfetext."""
        st = self._lauf(False)
        self.assertIn("Ausdrucken", st.checkbox_label)
        self.assertTrue(st.checkbox_kwargs.get("help"))

    def test_alle_drei_anreisswerkzeuge_benutzen_die_funktion(self):
        """Stutzen, Stutzen schraeg und Rohr-Verschneidung geben Stationen aus.
        Kommt ein viertes Werkzeug dazu, faellt hier auf, wenn es vergessen
        wurde."""
        import io
        from pathlib import Path
        quelle = io.open(Path(app.__file__), encoding="utf-8").read()
        self.assertEqual(quelle.count("_anreiss_tabelle("), 4,
                         "erwartet: Definition + drei Aufrufe")
        for schluessel in ('"druck_stutzen"', '"druck_stutzen_schraeg"',
                           '"druck_verschneidung"'):
            self.assertIn(schluessel, quelle)


if __name__ == "__main__":
    unittest.main()
