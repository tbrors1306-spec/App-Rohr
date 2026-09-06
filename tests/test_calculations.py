import unittest
import math
import sys
import os

import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.calculations import (
    PipeCalculator, FieldCalc, PipeRef, HandbookCalculator,
)


def _mock_df():
    return pd.DataFrame({
        'DN':          [100, 150, 80],
        'D_Aussen':    [114.3, 168.3, 88.9],
        'Radius_BA3':  [152, 229, 114],
        'T_Stueck_H':  [105, 143, 86],
        'Red_Laenge_L': [102, 152, 89],
        'Flansch_b_16': [52, 62, 46],
        'Flansch_b_10': [52, 62, 46],
        'LK_k_16':      [180, 240, 160],
        'LK_k_10':      [180, 240, 160],
        'Schraube_M_16': ['M16', 'M20', 'M16'],
        'Schraube_M_10': ['M16', 'M20', 'M16'],
        'Lochzahl_16':  [8, 8, 8],
        'Lochzahl_10':  [8, 8, 8],
    })


class TestPipeCalculator(unittest.TestCase):
    def setUp(self):
        self.df = _mock_df()
        self.calc = PipeCalculator(self.df)

    def test_get_deduction_90_deg_bend(self):
        # "Bogen" @ 90° = Radius_BA3 (tan(45) = 1)
        self.assertAlmostEqual(self.calc.get_deduction("Bogen", 100, "PN 16", 90.0), 152.0, places=6)

    def test_get_deduction_custom_angle(self):
        got = self.calc.get_deduction("Bogen", 100, "PN 16", 45.0)
        self.assertAlmostEqual(got, 152 * math.tan(math.radians(22.5)), places=1)

    def test_get_deduction_legacy_labels(self):
        # alte gespeicherte Typ-Strings müssen weiter funktionieren
        self.assertEqual(self.calc.get_deduction("Bogen 90° (BA3)", 100, "PN 16"), 152.0)
        got = self.calc.get_deduction("Bogen (Zuschnitt)", 100, "PN 16", 45.0)
        self.assertAlmostEqual(got, 152 * math.tan(math.radians(22.5)), places=1)

    def test_tolerance_stack(self):
        r = self.calc.apply_tolerance_stack(1000.0, 3, 2.0)
        self.assertEqual(r['compensation'], 6.0)
        self.assertEqual(r['adjusted'], 1006.0)

    def test_wedge_gap_parallel(self):
        r = self.calc.calculate_wedge_gap(100, {'12': 3, '3': 3, '6': 3, '9': 3})
        self.assertEqual(r['max_gap'], 0.0)

    def test_wedge_gap_tilted(self):
        r = self.calc.calculate_wedge_gap(100, {'12': 6, '3': 3, '6': 0, '9': 3})
        self.assertGreater(r['angle'], 0.0)
        self.assertAlmostEqual(r['max_gap'], 6.0, places=6)      # g12 - g6

    def test_2d_offset_zero_angle_errors(self):
        self.assertIn("error", self.calc.calculate_2d_offset(100, 500, 0))

    def test_2d_offset_45(self):
        res = self.calc.calculate_2d_offset(100, 500, 45)
        self.assertAlmostEqual(res['hypotenuse'], 500 / math.sin(math.radians(45)), places=1)

    def test_bend_details_90(self):
        d = self.calc.calculate_bend_details(100, 90)
        self.assertAlmostEqual(d['vorbau'], 152.0, places=1)          # r*tan(45)
        self.assertAlmostEqual(d['bogen_mitte'], 152 * math.pi / 2, places=1)

    def test_segment_bend(self):
        r = self.calc.calculate_segment_bend(150, 1000, 3, 90.0)
        self.assertAlmostEqual(r['miter_angle'], 22.5, places=3)
        self.assertGreater(r['mid_back'], r['mid_belly'])

    # -------------------------------------------------- Phase 3 --------------
    def test_branch_development_standard(self):
        r = self.calc.calculate_branch_development(150, 80, 24)
        # h_max = R - sqrt(R^2 - r^2)
        R, rr = 168.3 / 2, 88.9 / 2
        self.assertAlmostEqual(r['h_max'], R - math.sqrt(R ** 2 - rr ** 2), places=1)
        self.assertAlmostEqual(r['branch_circ'], math.pi * 88.9, places=1)

    def test_branch_development_too_big(self):
        self.assertIn("error", self.calc.calculate_branch_development(80, 150))

    def test_branch_development_angle_deeper(self):
        flat = self.calc.calculate_branch_development(150, 80, 24, beta_deg=0)
        tilt = self.calc.calculate_branch_development(150, 80, 24, beta_deg=30)
        self.assertGreater(tilt['h_max'], flat['h_max'])

    def test_equal_pipe_miter_90(self):
        m = self.calc.calculate_equal_pipe_miter(100, 90, 24)
        self.assertAlmostEqual(m['miter_angle'], 45.0, places=3)
        self.assertAlmostEqual(m['h_peak'], 114.3, places=1)          # = OD

    def test_equal_pipe_miter_bad_angle(self):
        self.assertIn("error", self.calc.calculate_equal_pipe_miter(100, 200))

    def test_spool_3d_pure_offset(self):
        s = self.calc.calculate_spool_3d(800, 300, 400, 45)
        self.assertAlmostEqual(s['true_offset'], 500.0, places=3)
        self.assertAlmostEqual(s['travel'], 500 / math.sin(math.radians(45)), places=1)
        self.assertAlmostEqual(s['roll_angle'], math.degrees(math.atan2(300, 400)), places=2)

    def test_spool_3d_straight(self):
        s = self.calc.calculate_spool_3d(1000, 0, 0, 45)
        self.assertTrue(s['straight'])

    # -------------------------------------------------- Bauteilkette -------
    @staticmethod
    def _z(t, m=None, r=None, d=None, ma=None, s=None, w=None):
        return {"Bauteil": t, "Mass (mm)": m, "Richtung": r, "DN": d,
                "Massart": ma, "Seite (mm)": s, "Winkel": w}

    def test_spool_empty(self):
        self.assertIn("error", self.calc.build_spool([], 100))

    def test_spool_saegeliste_ist_nur_rohr(self):
        """Kernversprechen: die Saegeliste sind die Rohr-Zeilen. Ohne Angabe
        gilt Achsmass - der Bogen wird also abgezogen, ohne dass man daran
        denken muss. Mit 'Rohrlaenge' bleibt das Mass unangetastet."""
        z = self._z
        parts = [z("Rohr", 800), z("Bogen 90", r="N"), z("Rohr", 2500)]
        sp = self.calc.build_spool(parts, 100, "PN 16", dir_start="O")
        r = float(self.df[self.df["DN"] == 100]["Radius_BA3"].iloc[0])
        self.assertEqual([c["Saegelaenge (mm)"] for c in sp["cut_rows"]],
                         [round(800 - r), round(2500 - r)])
        roh = [dict(x, **{"Massart": "Rohrlaenge"}) for x in parts]
        sp2 = self.calc.build_spool(roh, 100, "PN 16", dir_start="O")
        self.assertEqual([c["Saegelaenge (mm)"] for c in sp2["cut_rows"]],
                         [800, 2500])
        self.assertEqual(sp["warnings"], [])

    def test_spool_bauteile_direkt_aneinander(self):
        """Flansch + zwei Armaturen ohne Rohr dazwischen: 3 Flanschverbindungen,
        aber nur 2 Vorschweissflansche - kein Rohrstueck noetig."""
        z = self._z
        parts = [z("Rohr", 800), z("Vorschweissflansch"),
                 z("Armatur mit Flanschen", 300), z("Armatur mit Flanschen", 250),
                 z("Vorschweissflansch"), z("Rohr", 1200)]
        sp = self.calc.build_spool(parts, 100, "PN 16", dir_start="O")
        self.assertEqual(sp["warnings"], [])
        self.assertEqual(sp["flanschverbindungen"], 3)
        self.assertTrue(any(m["Position"].startswith("Vorschweissflansch")
                            and m["Menge"] == "2 St" for m in sp["mto"]))

    def test_spool_flansch_dreht_sich_automatisch(self):
        """Der zweite Vorschweissflansch muss andersherum eingebaut werden."""
        z = self._z
        parts = [z("Rohr", 800), z("Vorschweissflansch"),
                 z("Armatur mit Flanschen", 300), z("Vorschweissflansch"),
                 z("Rohr", 900)]
        sp = self.calc.build_spool(parts, 100, "PN 16", dir_start="O")
        lagen = [it["ends"] for it in sp["items"] if it["part"] == "Vorschweissflansch"]
        self.assertEqual(lagen, [("S", "F"), ("F", "S")])
        self.assertEqual(sp["warnings"], [])

    def test_spool_meldet_fehlenden_flansch(self):
        """Schweissende trifft Flanschende -> muss gemeldet werden."""
        z = self._z
        parts = [z("Rohr", 800), z("Armatur mit Flanschen", 300), z("Rohr", 900)]
        sp = self.calc.build_spool(parts, 100, "PN 16", dir_start="O")
        self.assertTrue(any("Vorschweissflansch" in w for w in sp["warnings"]))

    def test_spool_naht_je_stoss_keine_doppelzaehlung(self):
        """Zwei Boegen direkt aneinander: 1 Naht dazwischen, nicht 2."""
        z = self._z
        parts = [z("Rohr", 500), z("Bogen 90", r="N"), z("Bogen 90", r="Hoch"),
                 z("Rohr", 500)]
        sp = self.calc.build_spool(parts, 100, "PN 16", dir_start="O",
                                   count_ends=False)
        self.assertEqual(sp["naehte"], 3)          # Rohr|B, B|B, B|Rohr

    def test_spool_rohrstoesse_aus_stangenlaenge(self):
        z = self._z
        sp = self.calc.build_spool([z("Rohr", 20000)], 100, "PN 16",
                                   stock_len=6000, count_ends=False)
        self.assertEqual(sp["cut_rows"][0]["Rohrstoesse"], 3)
        self.assertEqual(sp["naehte"], 3)

    def test_klappe_zwei_dichtungen_ein_schraubensatz(self):
        """Eine Klappe in Zwischenflanschbauform wird zwischen zwei Flanschen
        eingespannt: beide Stoesse brauchen eine Dichtung, durchgespannt wird
        aber mit EINEM Satz laengerer Schrauben."""
        z = self._z
        sp = self.calc.build_spool(
            [z("Rohr", 500), z("Vorschweissflansch"), z("Klappe", 50),
             z("Vorschweissflansch"), z("Rohr", 500)],
            80, "PN 16", dir_start="O", count_ends=False)
        self.assertEqual(sp["warnings"], [])
        self.assertEqual(sp["flanschverbindungen"], 2)
        pos = {r["Benennung"]: r["Anzahl"] for r in sp["pos_rows"]}
        loch = int(self.df[self.df["DN"] == 80]["Lochzahl_16"].iloc[0])
        self.assertEqual(pos["Flanschdichtung PN 16"], "2 St")
        # ein durchgehender Satz - und kein normaler daneben
        self.assertIn("Schraubensatz M16 durchgehend (Klappe)", pos)
        self.assertEqual(pos["Schraubensatz M16 durchgehend (Klappe)"],
                         "%d St" % loch)
        self.assertNotIn("Schraubensatz M16", pos,
                         "die Klappe darf keinen zweiten Satz erzeugen")

    def test_demontagestueck_hat_flansche_an_beiden_enden(self):
        """Das Einbaustueck sitzt zwischen zwei Flanschen - beide Stoesse sind
        Flanschverbindungen, keine Naehte."""
        z = self._z
        sp = self.calc.build_spool(
            [z("Rohr", 500), z("Vorschweissflansch"), z("Demontagestueck", 220),
             z("Vorschweissflansch"), z("Rohr", 500)],
            80, "PN 16", dir_start="O", count_ends=False)
        self.assertEqual(sp["warnings"], [])
        self.assertEqual(sp["flanschverbindungen"], 2)
        # Baulaenge kommt aus der Eingabe und steckt in der Gesamtlaenge
        stueck = next(it for it in sp["items"]
                      if it["part"] == "Demontagestueck")
        self.assertEqual(stueck["len"], 220.0)

    def test_versprung_richtung_steuert_den_versatz(self):
        """Die Spalte Richtung sagt beim Versprung, wohin der Versatz geht -
        und zwar nur fuer ihre eigene Achse.

        Sie wurde zeitweise gar nicht ausgewertet; danach kippte mit der Seite
        auch das Oben, und bei "Runter" hob sich das Vorzeichen doppelt auf.
        """
        z = self._z

        def _ende(richtung, hoehe=500, seite=400, start="O"):
            sp = self.calc.build_spool(
                [z("Rohr", 1000), z("Versprung", hoehe, r=richtung, s=seite, w=45),
                 z("Rohr", 1000)], 80, "PN 16", dir_start=start,
                count_ends=False)
            return [round(v) for v in sp["nahtliste"][-1]["p"]], sp["warnings"]

        # Lauf nach Osten: N/S drehen nur die Seite, das Oben bleibt oben
        (x, y, zz), w = _ende("N")
        self.assertEqual((y, zz), (400, 500))
        self.assertEqual(w, [])
        (x, y, zz), _ = _ende("S")
        self.assertEqual((y, zz), (-400, 500), "S darf die Hoehe nicht kippen")

        # Hoch/Runter drehen nur die Hoehe, die Seite bleibt
        (x, y, zz), _ = _ende("Hoch")
        self.assertEqual((y, zz), (400, 500))
        (x, y, zz), _ = _ende("Runter")
        self.assertEqual((y, zz), (400, -500),
                         "Runter muss nach unten gehen, nicht nach oben")

        # Ohne Seitenversatz gilt dasselbe
        (x, y, zz), _ = _ende("Runter", seite=0)
        self.assertEqual((y, zz), (0, -500))

    def test_versprung_richtung_laengs_wird_gemeldet(self):
        """Eine Richtung parallel zur Laufrichtung ergaebe keinen Versatz."""
        z = self._z
        sp = self.calc.build_spool(
            [z("Rohr", 1000), z("Versprung", 500, r="O", s=400, w=45),
             z("Rohr", 1000)], 80, "PN 16", dir_start="O", count_ends=False)
        self.assertTrue(any("Laufrichtung" in x for x in sp["warnings"]),
                        "die unmoegliche Richtung wird still verschluckt")

    def test_nahtliste_deckt_sich_mit_der_zaehlung(self):
        """Summe und Liste duerfen nie auseinanderlaufen - eine Quelle."""
        z = self._z
        sp = self.calc.build_spool(
            [z("Rohr", 1000), z("Vorschweissflansch"),
             z("Armatur mit Flanschen", 300), z("Vorschweissflansch"),
             z("Rohr", 20000), z("Bogen 90"),
             z("Versprung", 800, s=600, w=45), z("Rohr", 500)],
            100, "PN 16", stock_len=6000,
            branches=[{"An Bauteil": 1, "Art": "Anschweissstutzen", "Richtung": "Hoch",
                       "DN": 50, "Abstand (mm)": 400, "Rohrlaenge (mm)": 800,
                       "Ende": "Vorschweissflansch"}])
        rund = [n for n in sp["nahtliste"] if n["art"] == "Rundnaht"]
        flan = [n for n in sp["nahtliste"] if n["art"] == "Flanschverbindung"]
        self.assertEqual(sp["naehte"], len(rund))
        self.assertEqual(sp["flanschverbindungen"], len(flan))
        self.assertEqual([n["nr"] for n in sp["nahtliste"]],
                         ["WF%d" % k for k in range(1, len(sp["nahtliste"]) + 1)])

    def test_nahtliste_baustelle_am_montagestoss(self):
        """Am Montagestoss und an den freien Enden wird auf der Baustelle
        geschweisst, dazwischen in der Werkstatt."""
        z = self._z
        sp = self.calc.build_spool(
            [z("Rohr", 1000), z("Montagestoss"), z("Rohr", 1000)],
            100, "PN 16", count_ends=True)
        feld = [n["was"] for n in sp["nahtliste"] if n["feld"]]
        self.assertEqual(len(feld), 4)          # 2 freie Enden + 2 am Stoss
        self.assertTrue(all("Montagestoss" in w or "Anschluss" in w for w in feld))
        sp2 = self.calc.build_spool([z("Rohr", 1000), z("Bogen 90"), z("Rohr", 1000)],
                                    100, "PN 16", count_ends=False)
        self.assertEqual([n for n in sp2["nahtliste"] if n["feld"]], [])

    def test_rohr_an_rohr_zieht_nichts_ab(self):
        """Zwei stumpf verschweisste Rohre: das Achsmass des einen endet dort,
        wo das andere anfaengt - da gibt es nichts abzuziehen."""
        z = self._z
        sp = self.calc.build_spool([z("Rohr", 1000), z("Rohr", 500)], 100,
                                   "PN 16", dir_start="O", count_ends=False)
        self.assertEqual([c["Abzug (mm)"] for c in sp["cut_rows"]], [0, 0])
        self.assertEqual([c["Saegelaenge (mm)"] for c in sp["cut_rows"]],
                         [1000, 500])

    def test_achsmass_ist_die_voreinstellung(self):
        """Leere Massart-Zelle = Achsmass. Wer am Bau misst, misst Mitte-Mitte."""
        z = self._z
        parts = [z("Vorschweissflansch"), z("Rohr", 2000), z("Bogen 90", r="N")]
        sp = self.calc.build_spool(parts, 100, "PN 16", dir_start="O",
                                   count_ends=False)
        row = self.df[self.df["DN"] == 100].iloc[0]
        erwartet = float(row["Flansch_b_16"]) + float(row["Radius_BA3"])
        self.assertEqual(sp["cut_rows"][0]["Abzug (mm)"], round(erwartet))
        self.assertEqual(sp["cut_rows"][0]["Massart"], "Achsmass")

    def test_nahtliste_koordinaten_folgen_der_route(self):
        """Die Naht am Ende eines 1000er Rohrs nach Osten liegt 1000 weiter."""
        z = self._z
        sp = self.calc.build_spool([z("Rohr", 1000), z("Rohr", 500)], 100, "PN 16",
                                   dir_start="O", x_start=5000, y_start=2000,
                                   el_start=16000, count_ends=False)
        n = sp["nahtliste"][0]
        self.assertEqual([round(v) for v in n["p"]], [6000, 2000, 16000])

    def test_nahtliste_stutzen_traegt_die_abzweig_dn(self):
        """Die Sattelnaht laeuft um das Abzweigrohr, nicht um das Hauptrohr."""
        z = self._z
        sp = self.calc.build_spool(
            [z("Rohr", 2000)], 100, "PN 16", count_ends=False,
            branches=[{"An Bauteil": 1, "Art": "Anschweissstutzen", "Richtung": "Hoch",
                       "DN": 50, "Abstand (mm)": 800, "Rohrlaenge (mm)": 600,
                       "Ende": "offen"}])
        sattel = [n for n in sp["nahtliste"] if "Anschweissstutzen" in n["was"]]
        self.assertEqual(len(sattel), 1)
        self.assertEqual(sattel[0]["dn"], 50)


    def test_nahtnummern_laufen_der_leitung_entlang(self):
        """WF1 am Anfang, dann der Reihe nach - die inneren Naehte des
        Versprungs liegen zwischen seinen beiden Kettenstoessen."""
        z = self._z
        sp = self.calc.build_spool(
            [z("Rohr", 1000), z("Versprung", 800, s=600, w=45), z("Rohr", 900)],
            80, "PN 16", dir_start="O", count_ends=False)
        orte = [n["was"] for n in sp["nahtliste"]]
        self.assertEqual(orte, ["Rohr / Versprung", "Bogen / Schraegrohr",
                                "Schraegrohr / Bogen", "Versprung / Rohr"])

    def test_abzweignaehte_liegen_an_ihrer_stelle(self):
        """Die Naehte eines Stutzens auf halber Strecke stehen zwischen den
        Naehten davor und danach, nicht am Ende der Liste."""
        z = self._z
        sp = self.calc.build_spool(
            [z("Rohr", 2000), z("Bogen 90", r="N"), z("Rohr", 2000)],
            80, "PN 16", dir_start="O", count_ends=False,
            branches=[{"An Bauteil": 1, "Art": "Anschweissstutzen",
                       "Richtung": "Hoch", "DN": 50, "Abstand (mm)": 1000,
                       "Rohrlaenge (mm)": 600, "Ende": "offenes Ende"}])
        orte = [n["was"] for n in sp["nahtliste"]]
        self.assertLess(orte.index("Anschweissstutzen auf DN 80"),
                        orte.index("Rohr / Bogen 90"))
        self.assertEqual([n["nr"] for n in sp["nahtliste"]],
                         ["WF%d" % k for k in range(1, len(orte) + 1)])


    def test_positionsnummern_haengen_am_bauteil(self):
        """Gleiche Bauteilart + DN teilen sich eine Positionsnummer."""
        z = self._z
        sp = self.calc.build_spool(
            [z("Rohr", 1000), z("Bogen 90", r="N"), z("Rohr", 800),
             z("Bogen 90", r="Hoch"), z("Rohr", 500)],
            100, "PN 16", count_ends=False)
        rohre = {it["pos"] for it in sp["items"] if it["part"] == "Rohr"}
        boegen = {it["pos"] for it in sp["items"] if it["part"] == "Bogen 90"}
        self.assertEqual(len(rohre), 1)
        self.assertEqual(len(boegen), 1)
        self.assertNotEqual(rohre, boegen)
        pos = {r["Pos"] for r in sp["pos_rows"]}
        self.assertEqual(pos, set(range(1, len(sp["pos_rows"]) + 1)))

    def test_stueckliste_wand_nur_wo_sinnvoll(self):
        """Dichtung und Schrauben haben keine Wanddicke, Rohr schon."""
        z = self._z
        sp = self.calc.build_spool(
            [z("Rohr", 1000), z("Vorschweissflansch"), z("Blindflansch")],
            100, "PN 16", schedule="XS", count_ends=False)
        w = {r["Benennung"]: r["Wand (mm)"] for r in sp["pos_rows"]}
        self.assertEqual(w["Rohr"], "8.56")
        self.assertEqual(w["Vorschweissflansch"], "8.56")
        self.assertEqual(w["Blindflansch"], "")
        for name, v in w.items():
            if name.startswith(("Flanschdichtung", "Schraubensatz")):
                self.assertEqual(v, "")

    def test_spool_abzweig_eigene_dn(self):
        """Abzweig mit kleinerer DN taucht getrennt in der Stueckliste auf."""
        z = self._z
        parts = [z("Rohr", 1000), z("T-Stueck"), z("Rohr", 1000)]
        br = [{"An Bauteil": 2, "Art": "Fertig-T", "Richtung": "Hoch",
               "DN": 80, "Rohrlaenge (mm)": 1200, "Ende": "Vorschweissflansch"}]
        sp = self.calc.build_spool(parts, 150, "PN 16", branches=br)
        pos = [m["Position"] for m in sp["mto"]]
        self.assertIn("Rohr DN80", pos)
        self.assertIn("Rohr DN150", pos)
        self.assertTrue(any(p.startswith("Vorschweissflansch DN80") for p in pos))
        abz = [c for c in sp["cut_rows"] if c["Herkunft"] == "Abzweig"][0]
        self.assertEqual((abz["DN"], abz["Saegelaenge (mm)"]), (80, 1200))

    def test_spool_abzweig_ohne_richtung_warnt(self):
        z = self._z
        parts = [z("Rohr", 1000), z("T-Stueck"), z("Rohr", 1000)]
        br = [{"An Bauteil": 2, "Art": "Fertig-T", "DN": 80,
               "Rohrlaenge (mm)": 1200, "Ende": "offenes Ende"}]
        sp = self.calc.build_spool(parts, 150, "PN 16", branches=br)
        self.assertTrue(any("Richtung fehlt" in w for w in sp["warnings"]))

    def test_spool_abzweig_auf_falschem_bauteil_warnt(self):
        z = self._z
        parts = [z("Rohr", 1000), z("Bogen 90", r="N"), z("Rohr", 1000)]
        br = [{"An Bauteil": 2, "Art": "Fertig-T", "Richtung": "Hoch",
               "DN": 80, "Rohrlaenge (mm)": 1200, "Ende": "offenes Ende"}]
        sp = self.calc.build_spool(parts, 150, "PN 16", branches=br)
        self.assertTrue(any("T-Stueck" in w for w in sp["warnings"]))

    def test_spool_reduzierung_wechselt_dn(self):
        z = self._z
        parts = [z("Rohr", 1000), z("Reduzierung", d=100), z("Rohr", 1000)]
        sp = self.calc.build_spool(parts, 150, "PN 16")
        dns = [c["DN"] for c in sp["cut_rows"]]
        self.assertEqual(dns, [150, 100])

    def test_spool_bogen_ohne_richtung_warnt(self):
        z = self._z
        sp = self.calc.build_spool([self._z("Rohr", 500), self._z("Bogen 90")],
                                   100, "PN 16")
        self.assertTrue(any("Richtung fehlt" in w for w in sp["warnings"]))



    def test_spool_achsmass_zieht_formteile_ab(self):
        """Achsmass Eckpunkt-zu-Eckpunkt: beide Bogenradien werden abgezogen."""
        z = self._z
        parts = [z("Rohr", 500), z("Bogen 90", r="N"),
                 dict(z("Rohr", 3000), **{"Massart": "Achsmass"}),
                 z("Bogen 90", r="Hoch"), z("Rohr", 500)]
        sp = self.calc.build_spool(parts, 150, "PN 16", dir_start="O")
        self.assertEqual(sp["warnings"], [])
        r = [c for c in sp["cut_rows"] if c["Nr"] == 3][0]
        self.assertEqual(r["Abzug (mm)"], 458)               # 2 x R(DN150)=229
        self.assertEqual(r["Saegelaenge (mm)"], 3000 - 458)

    def test_spool_achsmass_flansch_und_armatur(self):
        """Neben Flansch (M) und Armatur (FF) wird deren Baulaenge abgezogen."""
        z = self._z
        parts = [z("Vorschweissflansch"),
                 dict(z("Rohr", 2000), **{"Massart": "Achsmass"}),
                 z("Vorschweissflansch"), z("Armatur mit Flanschen", 300)]
        sp = self.calc.build_spool(parts, 100, "PN 16", dir_start="O")
        r = [c for c in sp["cut_rows"] if c["Nr"] == 2][0]
        self.assertEqual(r["Abzug (mm)"], 104)               # 2 x Flansch_b(DN100)=52
        self.assertEqual(r["Saegelaenge (mm)"], 1896)

    def test_spool_achsmass_zu_klein_warnt(self):
        z = self._z
        parts = [z("Rohr", 500), z("Bogen 90", r="N"),
                 dict(z("Rohr", 100), **{"Massart": "Achsmass"}),
                 z("Bogen 90", r="Hoch"), z("Rohr", 500)]
        sp = self.calc.build_spool(parts, 150, "PN 16", dir_start="O")
        self.assertTrue(any("kleiner als die Formteil-Abzuege" in w
                            for w in sp["warnings"]))

    def test_spool_achsmass_nur_bei_rohr(self):
        z = self._z
        parts = [z("Rohr", 500),
                 dict(z("Armatur geschweisst", 300), **{"Massart": "Achsmass"}),
                 z("Rohr", 500)]
        sp = self.calc.build_spool(parts, 100, "PN 16", dir_start="O")
        self.assertTrue(any("gilt nur fuer Rohr" in w for w in sp["warnings"]))

    def test_spool_stutzen_position(self):
        """Anschweissstutzen bei 800 mm ab Rohranfang."""
        z = self._z
        br = [{"An Bauteil": 1, "Art": "Anschweissstutzen", "Richtung": "Hoch",
               "DN": 50, "Abstand (mm)": 800, "Rohrlaenge (mm)": 600,
               "Ende": "Vorschweissflansch"}]
        sp = self.calc.build_spool([z("Rohr", 3000)], 400, "PN 16", branches=br)
        self.assertEqual(sp["warnings"], [])
        self.assertEqual(sp["branches"][0]["anriss"], 800.0)
        self.assertAlmostEqual(sp["branches"][0]["t"], 800 / 3000, places=6)
        self.assertIn("800", sp["cut_rows"][0]["Stutzen bei (mm)"])

    def test_spool_stutzen_ohne_abstand_ist_mitte(self):
        z = self._z
        br = [{"An Bauteil": 1, "Art": "Anschweissstutzen", "Richtung": "Hoch",
               "DN": 50, "Rohrlaenge (mm)": 600, "Ende": "offenes Ende"}]
        sp = self.calc.build_spool([z("Rohr", 3000)], 400, "PN 16", branches=br)
        self.assertEqual(sp["branches"][0]["anriss"], 1500.0)

    def test_spool_stutzen_ausserhalb_warnt(self):
        z = self._z
        br = [{"An Bauteil": 1, "Art": "Anschweissstutzen", "Richtung": "Hoch",
               "DN": 50, "Abstand (mm)": 4000, "Rohrlaenge (mm)": 600,
               "Ende": "offenes Ende"}]
        sp = self.calc.build_spool([z("Rohr", 3000)], 400, "PN 16", branches=br)
        self.assertTrue(any("liegt nicht auf dem Rohr" in w for w in sp["warnings"]))


class TestFieldCalc(unittest.TestCase):
    def test_right_triangle_345(self):
        r = FieldCalc.right_triangle(a=300, b=400)
        self.assertAlmostEqual(r['c'], 500.0, places=6)
        self.assertAlmostEqual(r['alpha'] + r['beta'], 90.0, places=6)
        self.assertAlmostEqual(r['area'], 0.5 * 300 * 400, places=3)

    def test_right_triangle_needs_two(self):
        self.assertIn("error", FieldCalc.right_triangle(a=300))

    def test_right_triangle_hypotenuse_check(self):
        self.assertIn("error", FieldCalc.right_triangle(a=500, c=300))

    def test_oblique_three_sides(self):
        r = FieldCalc.oblique_triangle(a=500, b=400, c=600)
        self.assertAlmostEqual(r['alpha'] + r['beta'] + r['gamma'], 180.0, places=3)

    def test_oblique_cosine(self):
        r = FieldCalc.oblique_triangle(a=500, b=400, gamma=60)
        self.assertAlmostEqual(r['c'], math.sqrt(500 ** 2 + 400 ** 2 - 2 * 500 * 400 * math.cos(math.radians(60))), places=3)

    def test_divide_circle_hex(self):
        d = FieldCalc.divide_circle(200, 6)
        self.assertAlmostEqual(d['chord'], 100.0, places=6)           # Sechseck: Sehne = R
        self.assertAlmostEqual(d['step_deg'], 60.0, places=6)
        self.assertEqual(len(d['points']), 6)


class TestHandbookCalculator(unittest.TestCase):
    def test_flange_thickness_c(self):
        self.assertEqual(HandbookCalculator.flange_thickness_c(100), 20.0)   # EN 1092-1 Typ 11
        self.assertEqual(HandbookCalculator.flange_thickness_c(300), 28.0)
        # Zwischengröße -> nächstkleinerer Tabellenwert
        self.assertEqual(HandbookCalculator.flange_thickness_c(90), 20.0)

    def test_bolt_length_dn100_hex_and_stud(self):
        # DN100 PN16, C=20, M16 – vgl. wermac: Sechskant ~M16x65, Stud ~M16x80
        hexL = HandbookCalculator.get_bolt_length(20, 20, "M16", washers=0, gasket=2.0)
        self.assertEqual(hexL, 65)
        studL = HandbookCalculator.get_bolt_length(20, 20, "M16", washers=0,
                                                   gasket=2.0, stud=True)
        self.assertIn(studL, (80, 85))
        self.assertGreater(studL, hexL)

    def test_bolt_length_rounds_and_scales(self):
        short = HandbookCalculator.get_bolt_length(20, 20, "M16", 0, 2.0)
        longer = HandbookCalculator.get_bolt_length(28, 28, "M24", 0, 3.0)   # DN300
        self.assertGreater(longer, short)
        self.assertEqual(longer % 5, 0)
        self.assertEqual(longer, 90)

    def test_bolt_length_washers_add_length(self):
        no_w = HandbookCalculator.get_bolt_length(20, 20, "M16", 0, 2.0)
        with_w = HandbookCalculator.get_bolt_length(20, 20, "M16", 2, 2.0)
        self.assertGreaterEqual(with_w, no_w)

    def test_bolt_length_bad_input(self):
        self.assertEqual(HandbookCalculator.get_bolt_length(20, 20, "junk"), 0)


class TestPipeRef(unittest.TestCase):
    def test_schedule_12in(self):
        sc = PipeRef.schedule_rows('12"')
        self.assertEqual(sc['dn'], 300)
        self.assertAlmostEqual(sc['od'], 323.85, places=2)
        std = next(r for r in sc['rows'] if r['Schedule'] == 'STD')
        self.assertAlmostEqual(std['Innen-Ø (mm)'], round(323.85 - 2 * 9.53, 1), places=1)

    def test_schedule_unknown(self):
        self.assertIsNone(PipeRef.schedule_rows('99"'))



if __name__ == '__main__':
    unittest.main()
