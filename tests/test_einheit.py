"""Rohrlaengen in Metern eingeben - und trotzdem in mm bauen.

Im Grossrohrleitungsbau ist ein Rohr 300 m lang. "300000" in ein Feld zu
tippen, in dem eine Null zu viel oder zu wenig niemandem auffaellt, ist eine
Fehlerquelle. Darum die Spalte "Einheit": eingegeben wird in m, gerechnet,
gezeichnet und gesaegt wird weiter in mm - ein Vorbau von 47 mm und ein Rohr
von 300 m stehen in derselben Rechnung.

Zwei Dinge muessen dabei stimmen und werden hier festgehalten: die Umrechnung
selbst, und dass die Zeichnung lange Masse lesbar beschriftet.
"""
import json
import unittest
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import pandas as pd

import streamlit_app as app
from modules.calculations import PipeCalculator
from modules.utils import Visualizer, _laengentext

DATA = Path(__file__).resolve().parent.parent / "data" / "pipe_dimensions.json"


class TestLaengentext(unittest.TestCase):
    """Wie eine Laenge an der Masslinie steht."""

    def test_saegemasse_bleiben_in_millimetern(self):
        """Bis 10 m ist mm das Mass, mit dem angerissen und gesaegt wird."""
        self.assertEqual(_laengentext(800), "800")
        self.assertEqual(_laengentext(2500), "2500")
        self.assertEqual(_laengentext(9999), "9999")

    def test_lange_rohre_stehen_in_metern(self):
        """300000 an einer Masslinie liest niemand."""
        self.assertEqual(_laengentext(300000), "300 m")
        self.assertEqual(_laengentext(10000), "10 m")

    def test_kein_komma_wenn_es_nichts_zu_zeigen_gibt(self):
        """Also "12 m" statt "12,00 m" - die Zeichnung ist voll genug."""
        self.assertEqual(_laengentext(12000), "12 m")
        self.assertEqual(_laengentext(12500), "12,5 m")
        self.assertEqual(_laengentext(287450), "287,45 m")

    def test_komma_nicht_punkt(self):
        """Auf dem Zettel wird mit Komma geschrieben."""
        self.assertNotIn(".", _laengentext(287450))

    def test_rundung_kippt_nicht_ueber_die_grenze(self):
        """Knapp unter 10 m bleibt mm, sonst gaebe es einen Sprung, bei dem
        dieselbe Laenge zweierlei heisst."""
        self.assertEqual(_laengentext(9999.4), "9999")
        self.assertEqual(_laengentext(10000.0), "10 m")


class TestEinheitSpalte(unittest.TestCase):
    """Die Umrechnung beim Einlesen der Tabelle."""

    def _tab(self, zeilen):
        d = app._spool_leer()
        return pd.concat([d, pd.DataFrame(zeilen)], ignore_index=True)

    def test_meter_werden_zu_millimetern(self):
        z, hinweise = app._parts_in_mm(self._tab(
            [{"Bauteil": "Rohr", "Mass (mm)": 300, "Einheit": "m"}]))
        self.assertEqual(z[0]["Mass (mm)"], 300000.0)
        self.assertEqual(hinweise, [])

    def test_millimeter_bleiben_wie_sie_sind(self):
        for einheit in ("mm", None, ""):
            z, hinweise = app._parts_in_mm(self._tab(
                [{"Bauteil": "Rohr", "Mass (mm)": 800, "Einheit": einheit}]))
            self.assertEqual(z[0]["Mass (mm)"], 800, "Einheit %r" % einheit)
            self.assertEqual(hinweise, [])

    def test_nachkommastellen_ueberleben(self):
        """287,45 m sind 287450 mm - keine verlorene Stelle."""
        z, _ = app._parts_in_mm(self._tab(
            [{"Bauteil": "Rohr", "Mass (mm)": 287.45, "Einheit": "m"}]))
        self.assertAlmostEqual(z[0]["Mass (mm)"], 287450.0, places=6)

    def test_meter_bei_einer_armatur_wird_gemeldet(self):
        """Eine Armatur hat ihre Baulaenge in mm. Die Einheit dort still zu
        schlucken hiesse: aus einem 300er Schieber werden 300 m."""
        z, hinweise = app._parts_in_mm(self._tab(
            [{"Bauteil": "Armatur mit Flanschen", "Mass (mm)": 300,
              "Einheit": "m"}]))
        self.assertEqual(z[0]["Mass (mm)"], 300, "das Mass darf nicht wachsen")
        self.assertEqual(len(hinweise), 1)
        self.assertIn("Zeile 1", hinweise[0])
        self.assertIn("Armatur mit Flanschen", hinweise[0])

    def test_alte_datei_ohne_die_spalte_laeuft_weiter(self):
        """Routen von vor dieser Aenderung kennen die Spalte nicht - sie sind
        in mm gemeint und muessen genauso rauskommen."""
        alt = pd.DataFrame([{"Bauteil": "Rohr", "Mass (mm)": 1200}])
        z, hinweise = app._parts_in_mm(alt)
        self.assertEqual(z[0]["Mass (mm)"], 1200)
        self.assertEqual(hinweise, [])

    def test_die_tabelle_selbst_wird_nicht_veraendert(self):
        """Umgerechnet wird nur die Kopie fuer den Rechner - in der Tabelle
        soll weiter stehen, was er eingegeben hat."""
        t = self._tab([{"Bauteil": "Rohr", "Mass (mm)": 300, "Einheit": "m"}])
        app._parts_in_mm(t)
        self.assertEqual(t["Mass (mm)"].iloc[0], 300)


class TestEinheitDurchgerechnet(unittest.TestCase):
    """Ende zu Ende: 300 m muessen dasselbe ergeben wie 300000 mm."""

    @classmethod
    def setUpClass(cls):
        with open(DATA, encoding="utf-8") as f:
            cls.calc = PipeCalculator(pd.DataFrame(json.load(f)))

    def _bauen(self, zeilen):
        parts, _ = app._parts_in_mm(pd.DataFrame(zeilen))
        return self.calc.build_spool(parts, 300, "PN 16", dir_start="O",
                                     stock_len=18000.0, count_ends=False)

    def test_meter_und_millimeter_ergeben_dieselbe_route(self):
        a = self._bauen([{"Bauteil": "Rohr", "Mass (mm)": 300, "Einheit": "m"},
                         {"Bauteil": "Bogen 90", "Richtung": "N"},
                         {"Bauteil": "Rohr", "Mass (mm)": 12000}])
        b = self._bauen([{"Bauteil": "Rohr", "Mass (mm)": 300000},
                         {"Bauteil": "Bogen 90", "Richtung": "N"},
                         {"Bauteil": "Rohr", "Mass (mm)": 12000}])
        self.assertEqual(a["warnings"], [])
        self.assertAlmostEqual(a["total_axis"], b["total_axis"], places=6)
        self.assertEqual(a["cut_rows"], b["cut_rows"])
        self.assertEqual(a["mto"], b["mto"])

    def test_die_stangenstoesse_werden_mitgezaehlt(self):
        """300 m saegt niemand am Stueck - bei 18-m-Stangen sind das 16
        zusaetzliche Rundnaehte."""
        sp = self._bauen([{"Bauteil": "Rohr", "Mass (mm)": 300,
                           "Einheit": "m"}])
        rohr = [c for c in sp["cut_rows"] if c["Herkunft"] == "Kette"][0]
        self.assertEqual(rohr["Saegelaenge (mm)"], 300000)
        self.assertEqual(rohr["Rohrstoesse"], 16)

    def test_die_zeichnung_beschriftet_in_metern(self):
        """Auf dem Blatt darf keine sechsstellige Zahl an der Masslinie
        stehen."""
        sp = self._bauen([{"Bauteil": "Rohr", "Mass (mm)": 300, "Einheit": "m"},
                          {"Bauteil": "Bogen 90", "Richtung": "N"},
                          {"Bauteil": "Rohr", "Mass (mm)": 2500}])
        fig = Visualizer.plot_spool(sp, "", modus="Aufmass & Saegen")
        texte = [t.get_text() for a in fig.axes for t in a.texts]
        self.assertIn("300 m", texte)
        self.assertIn("2500", texte, "kurze Masse bleiben in mm")
        self.assertNotIn("300000", texte)


class TestEinheitSpeichern(unittest.TestCase):
    """Die Einheit muss die Datei ueberleben - sonst wird aus 300 m beim
    naechsten Oeffnen ein Rohr von 300 mm."""

    def test_einheit_kommt_aus_der_datei_zurueck(self):
        d = pd.concat([app._spool_leer(),
                       pd.DataFrame([{"Bauteil": "Rohr", "Mass (mm)": 300,
                                      "Einheit": "m"}])], ignore_index=True)
        wieder = app._df_zurueck(json.loads(json.dumps(app._df_rein(d))),
                                 app._spool_leer)
        self.assertEqual(wieder["Einheit"].iloc[0], "m")
        parts, _ = app._parts_in_mm(wieder)
        self.assertEqual(parts[0]["Mass (mm)"], 300000.0)

    def test_die_spalte_steht_in_der_leeren_route(self):
        self.assertIn("Einheit", list(app._spool_leer().columns))


if __name__ == "__main__":
    unittest.main()
