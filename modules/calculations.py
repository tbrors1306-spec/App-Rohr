import math
import re
import pandas as pd
from typing import Dict, List, Any

class PipeCalculator:
    PN_MAP = {
        "PN 16": "_16",
        "PN 10": "_10",
        "PN 6": "_10",
        "PN 25": "_16", 
        "PN 40": "_16" 
    }

    def __init__(self, df: pd.DataFrame): self.df = df
    
    def get_row(self, dn: int) -> pd.Series:
        row = self.df[self.df['DN'] == dn]
        return row.iloc[0] if not row.empty else self.df.iloc[0]
        
    def get_deduction(self, f_type: str, dn: int, pn: str, angle: float = 90.0) -> float:
        row = self.get_row(dn)
        suffix = self.PN_MAP.get(pn, "_10")
        
        if "Bogen 90°" in f_type: return float(row['Radius_BA3'])
        if "Bogen" in f_type or "Zuschnitt" in f_type:
            return float(row['Radius_BA3']) * math.tan(math.radians(angle / 2))
        if "Flansch" in f_type: return float(row[f'Flansch_b{suffix}'])
        if "T-Stück" in f_type: return float(row['T_Stueck_H'])
        if "Reduzierung" in f_type: return float(row['Red_Laenge_L'])
        return 0.0
        
    def calculate_bend_details(self, dn: int, angle: float) -> Dict[str, float]:
        row = self.get_row(dn)
        r = float(row['Radius_BA3'])
        da = float(row['D_Aussen'])
        rad = math.radians(angle)
        return {"vorbau": r * math.tan(rad / 2), "bogen_aussen": (r + da/2) * rad, "bogen_mitte": r * rad, "bogen_innen": (r - da/2) * rad}
        
    def calculate_branch_development(self, dn_haupt: int, dn_stutzen: int,
                                    num_stations: int = 24,
                                    beta_deg: float = 0.0,
                                    offset_e: float = 0.0) -> Dict[str, Any]:
        """Abwicklung (Sattelschnitt) für einen aufgesetzten Stutzen (Set-on) —
        Maße auf Basis der Außendurchmesser.

        Standardfall (beta_deg = 0, offset_e = 0): rechtwinklig und mittig.
        beta_deg : Anstellwinkel der Stutzenachse aus der Senkrechten (0..70°).
        offset_e : seitlicher Versatz der Stutzenachse zur Hauptrohrachse (mm).

        phi = 0 ist der Punkt am Rohrscheitel (in Richtung der Hauptrohrachse).
        Bedingung "Punkt liegt auf dem Hauptrohrmantel":
          (e + r*sin(phi))^2 + (zeta*cos(b) - r*cos(phi)*sin(b))^2 = R^2
          -> zeta(phi) = ( r*cos(phi)*sin(b)
                           + sqrt(R^2 - (e + r*sin(phi))^2) ) / cos(b)
        Fuer b = 0, e = 0:  zeta(phi) = sqrt(R^2 - (r*sin(phi))^2)   (Standardfall)

        Stutzen-Schablone (Massband um den Stutzen):
          Umfangsmass  s(phi) = r*phi                     (0 .. 2*pi*r)
          Abtrag       h(phi) = zeta_max - zeta(phi)      (ab Anreisslinie im
                                                           tiefsten Punkt / Scheitel)
        Ausschnitt Hauptrohr:
          Umfangsmass  u(phi) = R*asin((e + r*sin(phi)) / R)   (ab Rohrscheitel)
          Achsmass     a(phi) = r*cos(phi)
        """
        R = float(self.get_row(dn_haupt)['D_Aussen']) / 2.0
        r = float(self.get_row(dn_stutzen)['D_Aussen']) / 2.0
        e = float(offset_e)
        b = math.radians(max(0.0, min(70.0, beta_deg)))
        if abs(e) + r > R:
            return {"error": "Stutzen (+ Versatz) größer als Hauptrohr – kein Sattelschnitt möglich."}

        n = max(8, int(num_stations))
        branch_circ = 2 * math.pi * r
        cb = math.cos(b)

        def zeta(phi):
            disc = R ** 2 - (e + r * math.sin(phi)) ** 2
            if disc < 0:
                return None
            return (r * math.cos(phi) * math.sin(b) + math.sqrt(disc)) / cb

        # zeta_max über eine feine Abtastung
        zmax = max(v for v in (zeta(2 * math.pi * k / 360) for k in range(360)) if v is not None)

        dev_s, dev_h, hole_u, hole_a, stations = [], [], [], [], []
        for i in range(n + 1):                     # inkl. Schlusspunkt (= Start)
            phi = 2 * math.pi * i / n
            zt = zeta(phi)
            if zt is None:
                zt = 0.0
            s = r * phi
            h = zmax - zt
            y = e + r * math.sin(phi)
            u = R * math.asin(max(-1.0, min(1.0, y / R)))
            a = r * math.cos(phi)
            dev_s.append(s); dev_h.append(h)
            hole_u.append(u); hole_a.append(a)
            if i < n:
                stations.append({
                    "Nr": i,
                    "Winkel": f"{math.degrees(phi):.0f}°",
                    "Umfangsmaß s (mm)": round(s, 1),
                    "Abtrag h (mm)": round(h, 2),
                })

        h_max = max(dev_h)
        return {
            "R": R, "r": r, "branch_circ": branch_circ, "h_max": h_max,
            "beta_deg": math.degrees(b), "offset_e": e,
            "num_stations": n, "stations": stations,
            "dev_s": dev_s, "dev_h": dev_h, "hole_u": hole_u, "hole_a": hole_a,
        }

    # ---------------------------------------------- Rohr-Verschneidung -------
    def calculate_equal_pipe_miter(self, dn: int, axis_angle_deg: float,
                                   num_stations: int = 24,
                                   mode: str = "Abzweig / Lateral") -> Dict[str, Any]:
        """Verschneidung zweier Rohre mit GLEICHEM Durchmesser.
        Bei gleichem Ø liegt die Schnittkurve in der Winkelhalbierenden-Ebene –
        also ein ebener Gehrungsschnitt.

        axis_angle_deg : Winkel zwischen den Rohrachsen (90° = rechtwinkliger Abzweig).
        mode 'Abzweig / Lateral' : ein Rohr wird eingeschweißt, Gehrung = (180-α)/2.
        mode 'Y symmetrisch'     : beide Rohre gleich, je Gehrung = α/2 zur Mittelachse.
        """
        r = float(self.get_row(dn)['D_Aussen']) / 2.0
        a = float(axis_angle_deg)
        if not 1.0 < a < 179.0:
            return {"error": "Achswinkel muss zwischen 1° und 179° liegen."}

        if mode.startswith("Y"):
            miter = a / 2.0                     # je Rohr, zur Mittelachse
        else:
            miter = (180.0 - a) / 2.0           # Gehrung des eingeschweißten Rohrs

        # Ebener Schnitt: z(phi) = amp * cos(phi), amp = r / tan(gehrung von der Senkrechten)
        gamma = math.radians(90.0 - miter)     # Neigung der Schnittebene zur Rohrquerschnittsebene
        amp = r * math.tan(gamma)
        circ = 2 * math.pi * r
        n = max(8, int(num_stations))

        dev_s, dev_h, stations = [], [], []
        for i in range(n + 1):
            phi = 2 * math.pi * i / n
            s = r * phi
            h = amp * (1.0 - math.cos(phi))     # 0 an der Ferse, 2*amp an der Zunge
            dev_s.append(s); dev_h.append(h)
            if i < n:
                stations.append({
                    "Nr": i, "Winkel": f"{math.degrees(phi):.0f}°",
                    "Umfangsmaß s (mm)": round(s, 1), "Abtrag h (mm)": round(h, 2),
                })
        return {"r": r, "circ": circ, "miter_angle": miter,
                "h_peak": 2.0 * amp, "num_stations": n,
                "dev_s": dev_s, "dev_h": dev_h, "stations": stations, "mode": mode}

    # ---------------------------------------------- Passstück 3D ------------
    @staticmethod
    def calculate_spool_3d(dx: float, dy: float, dz: float,
                           elbow_deg: float = 45.0) -> Dict[str, Any]:
        """Passstück zwischen zwei im Raum vermessenen Anschlusspunkten.
        dx = Lauf (entlang der ersten Rohrachse), dy = Seite, dz = Höhe.

        Reiner Achsversatz (dy, dz) wird mit zwei gleichen Bögen (elbow_deg)
        überbrückt.  true_offset = sqrt(dy^2 + dz^2)
        """
        true_offset = math.sqrt(dy ** 2 + dz ** 2)
        space_diag = math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)
        roll = math.degrees(math.atan2(dy, dz)) if true_offset > 1e-9 else 0.0
        g = math.radians(elbow_deg)
        out = {"true_offset": true_offset, "space_diag": space_diag,
               "roll_angle": roll, "elbow_deg": elbow_deg}
        if true_offset < 1e-6:
            out["travel"] = dx
            out["run"] = dx
            out["straight"] = True
            return out
        if elbow_deg <= 0 or elbow_deg >= 90:
            out["error"] = "Bogenwinkel zwischen 1° und 89°."
            return out
        travel = true_offset / math.sin(g)          # Mitte-Mitte der zwei Bögen
        run = true_offset / math.tan(g)             # Baulänge in Laufrichtung
        out.update({"travel": travel, "run": run, "straight": False,
                    "run_vs_dx": dx - run})         # verbleibende gerade Länge auf der dx-Achse
        return out

    def calculate_2d_offset(self, dn: int, offset: float, angle: float) -> Dict[str, float]:
        row = self.get_row(dn)
        r = float(row['Radius_BA3'])
        rad = math.radians(angle)
        try:
            hypotenuse = offset / math.sin(rad)
            run = offset / math.tan(rad)
        except ZeroDivisionError: return {"error": "Winkel 0"}
        z_mass = r * math.tan(rad / 2)
        return {"hypotenuse": hypotenuse, "run": run, "z_mass_single": z_mass, "cut_length": hypotenuse - (2*z_mass), "offset": offset, "angle": angle}
        
    def calculate_segment_bend(self, dn: int, radius: float, num_segments: int, total_angle: float = 90.0) -> Dict[str, float]:
        """Segment-Bogen (Lobster Back).

        num_segments = Anzahl gerader Rohrstuecke im Bogen.
          -> Naehte        = num_segments - 1
          -> Knick je Naht = total_angle / (num_segments - 1)          (turn_per_weld)
          -> Saegeblatt-Neigung je Schnittflaeche = Knick / 2          (miter_angle)

        Ein Vollsegment (beidseitig geschnitten) ueberstreicht 'turn_per_weld',
        ein Endstueck (nur eine Seite geschnitten, andere gerade) die Haelfte davon.
        Alle Laengen sind Abwicklungsmasse an der Rohrkontur.
        """
        row = self.get_row(dn)
        od = float(row['D_Aussen'])
        if num_segments < 2:
            return {"error": "Mindestens 2 Segmente."}
        welds = num_segments - 1
        turn_per_weld = total_angle / welds
        miter_angle = turn_per_weld / 2.0
        t = math.tan(math.radians(miter_angle))
        return {
            "miter_angle": miter_angle, "turn_per_weld": turn_per_weld,
            "num_segments": int(num_segments), "num_welds": welds,
            "od": od, "radius": radius, "total_angle": total_angle,
            "mid_back": 2 * (radius + od / 2) * t,
            "mid_center": 2 * radius * t,
            "mid_belly": 2 * (radius - od / 2) * t,
            "end_back": (radius + od / 2) * t,
            "end_center": radius * t,
            "end_belly": (radius - od / 2) * t,
        }

    @staticmethod
    def apply_tolerance_stack(cut_length: float, num_welds: int, shrinkage_per_weld: float = 2.0) -> dict:
        """
        Adjusts cut length to compensate for weld shrinkage.
        """
        total_compensation = num_welds * shrinkage_per_weld
        adjusted_length = cut_length + total_compensation
        
        return {
            "original": cut_length,
            "adjusted": adjusted_length,
            "compensation": total_compensation,
            "num_welds": num_welds,
            "shrinkage_per_weld": shrinkage_per_weld
        }


    def calculate_wedge_gap(self, dn: int, gaps: Dict[str, float]) -> Dict[str, Any]:
        """
        Calculates angular misalignment (wedge gap) and cutback values.
        gaps: {'12': float, '3': float, '6': float, '9': float}
        """
        row = self.get_row(dn)
        od = float(row['D_Aussen'])
        
        g12, g3, g6, g9 = gaps.get('12', 0), gaps.get('3', 0), gaps.get('6', 0), gaps.get('9', 0)
        
        # Calculate Vectors
        delta_v = g12 - g6  # Positive if 12 is larger (gap opens top)
        delta_h = g3 - g9   # Positive if 3 is larger (gap opens right)
        
        # Max Gap and Orientation
        max_diff = math.sqrt(delta_v**2 + delta_h**2)
        
        if max_diff == 0:
            return {"angle": 0.0, "max_gap": 0.0, "orientation": "N/A", "cut_data": []}

        # Angle of the pipe face tilt
        # tan(alpha) = max_diff / OD
        # alpha = arctan(max_diff / OD)
        angle_rad = math.atan(max_diff / od)
        angle_deg = math.degrees(angle_rad)
        
        # Orientation of the largest gap (High point of the cut needed)
        # We want to identify WHERE the gap is widest.
        # Atan2(y, x) -> (delta_h, delta_v) relative to standard math coordinates (0 at 3 o'clock)?
        # Let's map clock to degrees: 12=90, 3=0, 6=-90, 9=180
        # Wait, let's stick to Clock Face: 12 is Top.
        # Vector D = (delta_h, delta_v). 
        # Angle from 12 o'clock (Y-axis): atan2(x, y) = atan2(delta_h, delta_v)
        orientation_rad = math.atan2(delta_h, delta_v)
        orientation_deg = math.degrees(orientation_rad)
        if orientation_deg < 0: orientation_deg += 360
        
        # Convert degrees to Clock position roughly
        # 0 -> 12:00, 90 -> 3:00, 180 -> 6:00, 270 -> 9:00
        hrs = (orientation_deg / 30) 
        if hrs == 0: hrs = 12
        orientation_str = f"{int(hrs)}:{int((hrs%1)*60):02d} Uhr ({int(orientation_deg)}°)"
        
        # Calculate Cut Data for 8 points (every 45 degrees / 1.5 hours)
        # Point 0 is 12 o'clock. 
        # Gap at angle theta: G(theta) ~ Avg + (MaxDiff/2) * cos(theta - theta_max)
        # Cut needed C(theta) = G(theta) - G_min
        # This simplifies to: C(theta) = (MaxDiff/OD) * R * (1 - cos(theta - theta_max)) ?
        # Actually simpler: The cut Plane is tilted.
        # Height to remove h = tan(alpha) * distance_from_hinge
        # Hinge is at (orientation + 180).
        
        cut_data = []
        clock_labels = ["12:00", "01:30", "03:00", "04:30", "06:00", "07:30", "09:00", "10:30"]
        radius = od / 2
        
        # theta_max is the angle where measurement is largest (orientation_rad)
        # We start at 12:00 (angle = 0 relative to measuring vertical)
        # Let's use standard math: 12=90deg, 3=0deg.
        # orientation_rad was calc using atan2(dx, dy), so 0 is up (12), positive is CW (3).
        # wait, atan2(dx, dy):
        # if dx=0, dy=1 (12 larger): atan2(0, 1) = 0. Correct.
        # if dx=1, dy=0 (3 larger): atan2(1, 0) = 1.57 (90 deg). Correct.
        
        for i, label in enumerate(clock_labels):
            # angle of this point from 12:00 CW
            phi = math.radians(i * 45) 
            
            # The 'height' of the gap at this point relative to the center
            # Project vector (sin(phi), cos(phi)) onto gap vector direction?
            # Or simply:
            # Cut amount is proportional to distance from the "touching point" (gap min).
            # Gap min is at orientation + 180.
            
            # Distance from min-gap point along the axis of measuring:
            # It follows a cosine curve.
            # Max cut at orientation. Min cut (0) at orientation + 180.
            # cut = MaxDiff/2 * (1 + cos(phi - orientation)) ?
            # Let's check: at phi = orientation, cos(0)=1 -> MaxDiff. Correct.
            # at phi = orientation+180, cos(180)=-1 -> 0. Correct.
            
            cut_val = (max_diff / 2) * (1 + math.cos(phi - orientation_rad))
            
            # BUT: We derived MaxDiff from max_diff = sqrt(dV^2 + dH^2). 
            # This MaxDiff is the difference between Measuring Points (Diameter), not Radius.
            # If we cut the FULL face, the amplitude is MaxDiff * (Radius/Diameter) ? No.
            # If gap at 12 is 10 and 6 is 0. Delta V = 10. MaxDiff = 10.
            # Cut at 12 should be 10. Cut at 6 should be 0.
            # Formula: (10/2) * (1 + cos(0)) = 5 * 2 = 10. Correct.
            
            # Arc Length (Maßband) from 12:00 (Point 0)
            # Circumference = OD * pi
            # Arc = (Angle / 360) * Circumference
            arc_len = (od * math.pi) * (i * 45 / 360)
            
            cut_data.append({
                "Pos": label,
                "Maßband (mm)": round(arc_len, 0),
                "Abtrag (mm)": round(cut_val, 1)
            })
            
        return {
            "angle": round(angle_deg, 2),
            "max_gap": round(max_diff, 1),
            "orientation": orientation_str,
            "cut_data": cut_data,
            "od": od
        }

    # ------------------------------------------- Spool / Bauteilkette ------
    ROUTE_DIRS = {
        "N": (0.0, 1.0, 0.0), "S": (0.0, -1.0, 0.0),
        "O": (1.0, 0.0, 0.0), "W": (-1.0, 0.0, 0.0),
        "Hoch": (0.0, 0.0, 1.0), "Runter": (0.0, 0.0, -1.0),
    }

    # Enden je Bauteil: "S" = Schweissende, "F" = Flanschende,
    # "X" = geschlossen (nur als letztes Bauteil zulaessig).
    #   input : Laenge muss eingegeben werden (sonst aus der DN-Tabelle)
    #   turn  : aendert die Laufrichtung (Bogen)
    PART_SPEC = {
        "Rohr":                  {"ends": ("S", "S"), "input": True,  "turn": False},
        "Bogen 90":              {"ends": ("S", "S"), "input": False, "turn": True},
        # Versprung/Versatz: zwei gleiche Boegen + schraeges Rohr dazwischen.
        # Die Laufrichtung bleibt danach dieselbe, die Achse ist nur versetzt.
        "Versprung":             {"ends": ("S", "S"), "input": False, "turn": False},
        "Vorschweissflansch":    {"ends": ("S", "F"), "input": False, "turn": False},
        "Blindflansch":          {"ends": ("F", "X"), "input": False, "turn": False},
        "Armatur geschweisst":   {"ends": ("S", "S"), "input": True,  "turn": False},
        "Armatur mit Flanschen": {"ends": ("F", "F"), "input": True,  "turn": False},
        "T-Stueck":              {"ends": ("S", "S"), "input": False, "turn": False},
        "Reduzierung":           {"ends": ("S", "S"), "input": False, "turn": False},
        "Montagestoss":          {"ends": ("S", "S"), "input": False, "turn": False},
    }
    SPOOL_PARTS = list(PART_SPEC.keys())
    # Wie das eingetragene Mass zu lesen ist (nur bei Rohr sinnvoll):
    #   Rohrlaenge = fertige Saegelaenge, nichts wird abgezogen
    #   Achsmass   = Bezugspunkt zu Bezugspunkt der Nachbarn, Formteile werden
    #                abgezogen (Bogen = Eckpunkt, Flansch = Dichtflaeche,
    #                Armatur = Aussenflaeche, T-Stueck = Rohrmitte)
    MASSARTEN = ["Rohrlaenge", "Achsmass"]
    # Bogenwinkel fuer den Versprung (zwei Boegen dieses Winkels)
    VERSPRUNG_WINKEL = [45, 30, 60, 22.5, 11.25]
    # Halterungen. Die Kuerzel sind die in der App voreingestellten - jedes
    # Projekt hat seine eigenen, darum kann man sie in der Tabelle ueberschreiben.
    HALTER_TYPEN = {
        "Festpunkt": "FP",
        "Gleitlager": "GL",
        "Fuehrungslager": "FL",
        "Loslager": "LL",
        "Axialstop": "AX",
        "Rohrschelle": "RS",
        "Rohrschuh": "SH",
        "Pendelhaenger": "PH",
        "Federhaenger": "FH",
        "Konstanthaenger": "KH",
    }
    HALTER_LAGE = ["unten", "oben", "seitlich"]
    BRANCH_ARTEN = ["Fertig-T", "Anschweissstutzen"]
    BRANCH_ENDS = ["offenes Ende", "Vorschweissflansch", "Blindflansch",
                   "Anschluss geschweisst"]
    _BRANCH_END_SPEC = {                       # (Ende zur Rohrseite, Laenge-Art)
        "offenes Ende": ("-", None),
        "Vorschweissflansch": ("S", "flansch"),
        "Blindflansch": ("S", None),           # Blindflansch braucht Gegenflansch
        "Anschluss geschweisst": ("S", None),
    }

    # ---- Hilfsmasse je Bauteil und DN --------------------------------------
    def part_length(self, part, dn, eingabe=0.0, suffix="_16"):
        """Baulaenge eines Bauteils in mm (Bogen: je Schenkel ab Eckpunkt)."""
        row = self.get_row(dn)
        R = float(row["Radius_BA3"])
        if part == "Rohr":
            return max(0.0, float(eingabe or 0.0))
        if part == "Bogen 90":
            return R
        if part == "Versprung":
            return 0.0                     # wird in build_spool gesondert gerechnet
        if part == "Vorschweissflansch":
            return float(row["Flansch_b%s" % suffix])
        if part == "Blindflansch":
            return HandbookCalculator.flange_thickness_c(int(dn))
        if part in ("Armatur geschweisst", "Armatur mit Flanschen"):
            return max(0.0, float(eingabe or 0.0))
        if part == "T-Stueck":
            return 2.0 * float(row["T_Stueck_H"])
        if part == "Reduzierung":
            return float(row["Red_Laenge_L"])
        return 0.0                                     # Montagestoss

    def _versprung(self, d, hoehe, seite, winkel_grad, dn):
        """Versprung/Versatz aus zwei gleichen Boegen und schraegem Rohr dazwischen.

        d      : aktuelle Laufrichtung (Einheitsvektor)
        hoehe  : Hoehenversprung in mm (+ = nach oben)
        seite  : Seitenversatz in mm (+ = nach links zur Laufrichtung)
        Liefert Rohrweg, Baulaenge in Laufrichtung, Verdrehung, Vorbau je Bogen,
        Saegelaenge des schraegen Rohrs und dessen Richtung.
        """
        if abs(d[2]) > 0.5:                          # senkrechter Lauf
            e_seite, e_hoehe = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)
        else:                                        # waagerechter Lauf
            e_seite = (-d[1], d[0], 0.0)             # z x d  -> nach links
            e_hoehe = (0.0, 0.0, 1.0)
        off = tuple(seite * e_seite[k] + hoehe * e_hoehe[k] for k in range(3))
        versatz = math.sqrt(sum(v * v for v in off))
        if versatz < 1e-6:
            return None
        g = math.radians(winkel_grad)
        travel = versatz / math.sin(g)               # Rohrweg Mitte-Mitte
        run = versatz / math.tan(g)                  # Baulaenge in Laufrichtung
        ou = tuple(v / versatz for v in off)
        d_diag = tuple(d[k] * math.cos(g) + ou[k] * math.sin(g) for k in range(3))
        R = float(self.get_row(dn)["Radius_BA3"])
        vorbau = R * math.tan(g / 2.0)
        return {"versatz": versatz, "travel": travel, "run": run,
                "roll": math.degrees(math.atan2(seite, hoehe)),
                "winkel": winkel_grad, "vorbau": vorbau,
                "saege": travel - 2.0 * vorbau, "d_diag": d_diag,
                "hoehe": hoehe, "seite": seite}

    def build_spool(self, parts, dn_start, pn="PN 16", dir_start="O",
                    el_start=0.0, stock_len=6000.0, olet_h=30.0, branches=None,
                    count_ends=True, x_start=0.0, y_start=0.0,
                    werkstoff="P235GH", schedule="STD", supports=None):
        """Bauteilkette -> Geometrie, Stueckliste, Saegeliste, Pruefungen.

        parts : [{"Bauteil", "Mass (mm)", "Richtung", "DN"}]
                 - Mass  nur bei Rohr / Armatur noetig, sonst aus der DN-Tabelle
                 - Richtung nur bei Bogen (neue Laufrichtung)
                 - DN nur bei Reduzierung (neue Nennweite ab hier)
        branches : [{"An Bauteil", "Art", "DN", "Rohrlaenge (mm)", "Ende"}]

        Naehte und Flanschverbindungen ergeben sich aus den Stoessen zwischen
        benachbarten Bauteilen - nicht aus Annahmen je Bauteil.
        """
        warnings = []
        suffix = self.PN_MAP.get(pn, "_16")
        stock = float(stock_len) if stock_len and stock_len > 0 else 0.0

        def _stoss(cut):
            return max(0, math.ceil(cut / stock) - 1) if stock and cut > 0 else 0

        d_cur = self.ROUTE_DIRS.get(str(dir_start).strip(), (1.0, 0.0, 0.0))
        dn_cur = int(dn_start)

        items = []          # ausgewertete Bauteilzeilen
        for i, p in enumerate((parts or [])[:60]):
            part = p.get("Bauteil")
            part = str(part).strip() if not pd.isna(part) else ""
            if part not in self.PART_SPEC:
                continue
            spec = self.PART_SPEC[part]
            raw = p.get("Mass (mm)")
            raw = 0.0 if pd.isna(raw) else float(raw)

            # DN-Wechsel (Reduzierung)
            dn_new = p.get("DN")
            dn_new = None if pd.isna(dn_new) else int(dn_new)
            dn_for_part = dn_cur
            if part == "Reduzierung":
                if dn_new is None:
                    warnings.append(
                        "Zeile %d: Reduzierung ohne Ziel-DN - DN bleibt %d."
                        % (i + 1, dn_cur))
                elif dn_new == dn_cur:
                    warnings.append("Zeile %d: Reduzierung auf dieselbe DN." % (i + 1))
            elif dn_new is not None and dn_new != dn_cur:
                warnings.append(
                    "Zeile %d: DN wird nur bei einer Reduzierung ausgewertet." % (i + 1))

            if spec["input"] and raw <= 0:
                warnings.append(
                    "Zeile %d (%s): Mass fehlt - Bauteil wird uebersprungen."
                    % (i + 1, part))
                continue

            L = self.part_length(part, dn_for_part, raw, suffix)

            d_new = None
            if spec["turn"]:
                rn = p.get("Richtung")
                rn = str(rn).strip() if not pd.isna(rn) else ""
                d_new = self.ROUTE_DIRS.get(rn)
                if d_new is None:
                    warnings.append(
                        "Zeile %d (%s): neue Richtung fehlt - Bogen uebersprungen."
                        % (i + 1, part))
                    continue
                if d_new == d_cur:
                    warnings.append(
                        "Zeile %d: Bogen auf dieselbe Richtung - kein Richtungswechsel."
                        % (i + 1))

            # --- Versprung: zwei Boegen + schraeges Rohr ---------------
            vers = None
            if part == "Versprung":
                hoehe = raw                      # Spalte "Mass (mm)" = Hoehe
                seite = p.get("Seite (mm)")
                seite = 0.0 if pd.isna(seite) else float(seite)
                wnk = p.get("Winkel")
                wnk = 45.0 if pd.isna(wnk) else float(wnk)
                if not 5.0 <= wnk <= 85.0:
                    warnings.append("Zeile %d: Versprung-Winkel muss zwischen 5 und "
                                    "85 Grad liegen - 45 Grad benutzt." % (i + 1))
                    wnk = 45.0
                vers = self._versprung(d_cur, hoehe, seite, wnk, dn_for_part)
                if vers is None:
                    warnings.append("Zeile %d: Versprung ohne Hoehe/Seite - "
                                    "uebersprungen." % (i + 1))
                    continue
                L = vers["vorbau"]             # Anteil je Seite bis zum Eckpunkt

            mart = p.get("Massart")
            mart = str(mart).strip() if not pd.isna(mart) else self.MASSARTEN[0]
            if mart not in self.MASSARTEN:
                mart = self.MASSARTEN[0]
            if mart == "Achsmass" and part != "Rohr":
                warnings.append(
                    "Zeile %d (%s): 'Achsmass' gilt nur fuer Rohr - als Baulaenge "
                    "gerechnet." % (i + 1, part))
                mart = self.MASSARTEN[0]

            items.append({"row": i + 1, "part": part, "len": L, "dn": dn_for_part,
                          "ends": spec["ends"], "turn": spec["turn"],
                          "d_in": d_cur, "d_out": d_new or d_cur,
                          "eingabe": raw, "massart": mart, "abzug": 0.0,
                          "vers": vers})
            if spec["turn"]:
                d_cur = d_new
            if part == "Reduzierung" and dn_new:
                dn_cur = dn_new

        if not items:
            return {"error": "Noch keine gueltigen Bauteile - Zeile anlegen "
                             "(Bauteil waehlen, bei Rohr/Armatur ein Mass eintragen)."}

        # ---- Achsmass -> Saegelaenge: Nachbar-Formteile abziehen ------------
        # Bezugspunkte: Bogen = Eckpunkt, Flansch = Dichtflaeche,
        # Armatur = Aussenflaeche, T-Stueck = Rohrmitte, Reduzierung = fernes Ende.
        # Was ein Nachbar zwischen seinem Bezugspunkt und dem Rohrende belegt:
        def _anteil(it):
            if it is None:
                return 0.0                       # Kettenende: Mass endet am Rohr
            if it["part"] == "T-Stueck":
                return it["len"] / 2.0           # Mitte -> Ende des Durchgangs
            if it["part"] == "Versprung":
                return it["vers"]["vorbau"]      # bis zum ersten Eckpunkt
            return it["len"]                     # Bogen R, Flansch M, Armatur FF
        for k, it in enumerate(items):
            if it["massart"] != "Achsmass":
                continue
            vor = items[k - 1] if k > 0 else None
            nach = items[k + 1] if k + 1 < len(items) else None
            ab = _anteil(vor) + _anteil(nach)
            it["abzug"] = ab
            it["len"] = it["eingabe"] - ab
            if it["len"] <= 0:
                warnings.append(
                    "Zeile %d: Achsmass %.0f mm ist kleiner als die Formteil-Abzuege "
                    "(%.0f mm) - so nicht baubar." % (it["row"], it["eingabe"], ab))
                it["len"] = 0.0

        # ---- Bauteile automatisch richtig herum einbauen -------------------
        # Ein Vorschweissflansch hat ein Schweiss- und ein Flanschende; je nach
        # Nachbarn muss er andersherum eingebaut werden. Beide Varianten fuer
        # das erste Bauteil durchrechnen und die mit weniger Fehlstoessen nehmen.
        def _orient(seq):
            fehl = 0
            for k in range(1, len(seq)):
                vor = seq[k - 1]["ends"][1]
                ea, eb = seq[k]["ends"]
                if ea != vor and eb == vor and "X" not in (ea, eb):
                    seq[k]["ends"] = (eb, ea)
                if seq[k]["ends"][0] != vor:
                    fehl += 1
            return fehl

        var_a = [dict(it) for it in items]
        fehl_a = _orient(var_a)
        var_b = [dict(it) for it in items]
        e0 = var_b[0]["ends"]
        if "X" not in e0 and e0[0] != e0[1]:
            var_b[0]["ends"] = (e0[1], e0[0])
        fehl_b = _orient(var_b)
        items = var_a if fehl_a <= fehl_b else var_b

        # ---- Stoesse pruefen und zaehlen ---------------------------------
        joints = []
        for a, b in zip(items, items[1:]):
            ea, eb = a["ends"][1], b["ends"][0]
            if ea == "X":
                warnings.append(
                    "Zeile %d: nach einem Blindflansch kann nichts mehr folgen."
                    % a["row"])
                joints.append(None)
            elif ea == eb == "S":
                joints.append("naht")
            elif ea == eb == "F":
                joints.append("flansch")
            else:
                warnings.append(
                    "Stoss Zeile %d/%d: %s trifft auf %s - dazwischen fehlt ein "
                    "Vorschweissflansch." % (a["row"], b["row"],
                                             "Schweissende" if ea == "S" else "Flanschende",
                                             "Schweissende" if eb == "S" else "Flanschende"))
                joints.append(None)

        # naehte wird weiter unten aus der Nahtliste abgeleitet - die Liste ist
        # die einzige Quelle, damit Summe und Liste nicht auseinanderlaufen.
        naehte = 0
        flanschverb = [(items[i]["dn"]) for i, j in enumerate(joints) if j == "flansch"]

        # freie Enden der Kette
        frei_a, frei_b = items[0]["ends"][0], items[-1]["ends"][1]
        offene = []
        if count_ends:
            if frei_a == "S":
                offene.append(("Anfang", "Anschlussnaht"))
            elif frei_a == "F":
                flanschverb.append(items[0]["dn"]); offene.append(("Anfang", "Flanschanschluss"))
            if frei_b == "S":
                offene.append(("Ende", "Anschlussnaht"))
            elif frei_b == "F":
                flanschverb.append(items[-1]["dn"]); offene.append(("Ende", "Flanschanschluss"))

        # ---- Geometrie: Segmente in Laufrichtung --------------------------
        segments = []
        seg_von, seg_bis = {}, {}          # Bauteil-Nr -> erster/letzter Segmentindex
        for it in items:
            seg_von[it["row"]] = len(segments)
            if it["part"] == "Versprung":
                v = it["vers"]
                for dd, ll in ((it["d_in"], v["vorbau"]),
                               (v["d_diag"], v["travel"]),
                               (it["d_in"], v["vorbau"])):
                    segments.append({"d": dd, "len": ll, "part": it["part"],
                                     "row": it["row"], "dn": it["dn"],
                                     "corner_after": False})
            elif it["turn"]:
                segments.append({"d": it["d_in"], "len": it["len"], "part": it["part"],
                                 "row": it["row"], "dn": it["dn"], "corner_after": True})
                segments.append({"d": it["d_out"], "len": it["len"], "part": it["part"],
                                 "row": it["row"], "dn": it["dn"], "corner_after": False})
            else:
                segments.append({"d": it["d_in"], "len": it["len"], "part": it["part"],
                                 "row": it["row"], "dn": it["dn"], "corner_after": False})
            seg_bis[it["row"]] = len(segments) - 1

        # ---- Wahre Lage im Raum (fuer Koordinaten und Nahtpositionen) -------
        pos = (float(x_start), float(y_start), float(el_start))
        for s in segments:
            s["p0"] = pos
            pos = tuple(pos[k] + s["d"][k] * s["len"] for k in range(3))
            s["p1"] = pos

        # ---- Abzweige ------------------------------------------------------
        by_row = {}
        for si, s in enumerate(segments):
            by_row.setdefault(s["row"], []).append(si)
        branch_out = []
        for b in (branches or [])[:20]:
            try:
                ref = int(b.get("An Bauteil"))
            except (TypeError, ValueError):
                continue
            L = b.get("Rohrlaenge (mm)")
            L = 0.0 if pd.isna(L) else float(L)
            dvn = str(b.get("Richtung", "")).strip()
            dv = self.ROUTE_DIRS.get(dvn)
            if ref not in by_row:
                warnings.append("Abzweig: Bauteil Nr. %s gibt es nicht." % b.get("An Bauteil"))
                continue
            if dv is None:
                warnings.append("Abzweig an Bauteil %d: Richtung fehlt." % ref)
                continue
            if L <= 0:
                warnings.append("Abzweig an Bauteil %d: Rohrlaenge fehlt." % ref)
                continue
            host = next(it for it in items if it["row"] == ref)
            art = str(b.get("Art", "")).strip()
            if art not in self.BRANCH_ARTEN:
                art = "Fertig-T"
            if art == "Fertig-T" and host["part"] != "T-Stueck":
                warnings.append(
                    "Abzweig an Bauteil %d: Fertig-T braucht ein T-Stueck in der Kette "
                    "(dort steht '%s')." % (ref, host["part"]))
            if art == "Anschweissstutzen" and host["part"] != "Rohr":
                warnings.append(
                    "Abzweig an Bauteil %d: Anschweissstutzen sitzt auf einem Rohr "
                    "(dort steht '%s')." % (ref, host["part"]))
            bdn = b.get("DN")
            bdn = host["dn"] if pd.isna(bdn) else int(bdn)
            if bdn > host["dn"]:
                warnings.append("Abzweig an Bauteil %d: DN %d ist groesser als das "
                                "Hauptrohr DN %d." % (ref, bdn, host["dn"]))
            end = str(b.get("Ende", "")).strip()
            if end not in self.BRANCH_ENDS:
                end = "offenes Ende"

            # Arm vom Anschlusspunkt bis zum Rohranfang des Abzweigs
            if art == "Fertig-T":
                arm = float(self.get_row(host["dn"])["T_Stueck_H"])
            else:
                arm = float(self.get_row(host["dn"])["D_Aussen"]) / 2.0 + max(0.0, olet_h)
            end_len = (self.part_length("Vorschweissflansch", bdn, 0.0, suffix)
                       if end == "Vorschweissflansch" else
                       self.part_length("Blindflansch", bdn, 0.0, suffix) if end == "Blindflansch" else 0.0)

            # Anrissmass: wie weit ab Rohranfang wird der Stutzen aufgeschweisst?
            # Nur beim Anschweissstutzen auf einem Rohr sinnvoll - beim Fertig-T
            # steht die Lage schon durch die Stelle in der Kette fest.
            abst = b.get("Abstand (mm)")
            abst = None if pd.isna(abst) else float(abst)
            anriss, t_pos = None, 0.5
            if abst is not None:
                if art != "Anschweissstutzen" or host["part"] != "Rohr":
                    warnings.append(
                        "Abzweig an Bauteil %d: 'Abstand' gilt nur fuer einen "
                        "Anschweissstutzen auf einem Rohr - Wert ignoriert." % ref)
                elif host["len"] <= 0:
                    pass
                elif not 0.0 <= abst <= host["len"]:
                    warnings.append(
                        "Abzweig an Bauteil %d: Abstand %.0f mm liegt nicht auf dem "
                        "Rohr (0 - %.0f mm)." % (ref, abst, host["len"]))
                else:
                    anriss, t_pos = abst, abst / host["len"]
            elif art == "Anschweissstutzen" and host["part"] == "Rohr" and host["len"] > 0:
                anriss = host["len"] / 2.0        # ohne Angabe: Rohrmitte

            branch_out.append({"host_row": ref, "seg": by_row[ref][0], "art": art,
                               "dn": bdn, "d": dv, "dir": dvn, "arm": arm,
                               "pipe": L, "end": end, "end_len": end_len,
                               "anriss": anriss, "t": t_pos})

        # Flansche der Abzweige (die Naehte kommen aus der Nahtliste)
        for br in branch_out:
            if br["end"] == "Vorschweissflansch":
                flanschverb.append(br["dn"])
            elif br["end"] == "Blindflansch":
                warnings.append("Abzweig an Bauteil %d: Blindflansch braucht einen "
                                "Vorschweissflansch davor." % br["host_row"])

        # ---- Halterungen ---------------------------------------------------
        # Eine Halterung sitzt auf einem Bauteil und verlaengert die Leitung
        # nicht - darum kein Kettenglied, sondern ein Anbau wie der Stutzen.
        halter, zaehler = [], {}
        for h in (supports or [])[:30]:
            try:
                ref = int(h.get("An Bauteil"))
            except (TypeError, ValueError):
                continue
            if ref not in by_row:
                warnings.append("Halterung: Bauteil Nr. %s gibt es nicht."
                                % h.get("An Bauteil"))
                continue
            host = next(it for it in items if it["row"] == ref)
            typ = str(h.get("Art", "")).strip()
            if typ not in self.HALTER_TYPEN:
                typ = "Gleitlager"
            kurz = str(h.get("Kuerzel", "") or "").strip() or self.HALTER_TYPEN[typ]
            lage = str(h.get("Lage", "")).strip()
            if lage not in self.HALTER_LAGE:
                lage = "unten"
            abst = h.get("Bei (mm)")
            abst = None if pd.isna(abst) else float(abst)
            t_pos = 0.5
            if abst is not None and host["len"] > 0:
                if not 0.0 <= abst <= host["len"]:
                    warnings.append(
                        "Halterung an Bauteil %d: %.0f mm liegt nicht auf dem "
                        "Bauteil (0 - %.0f mm)." % (ref, abst, host["len"]))
                    abst = None
                else:
                    t_pos = abst / host["len"]
            nr_h = h.get("Nummer")
            if pd.isna(nr_h) or not str(nr_h).strip():
                zaehler[kurz] = zaehler.get(kurz, 0) + 1
                nr_h = zaehler[kurz]
            else:
                nr_h = str(nr_h).strip()
            seg_i = seg_von[ref]
            s = segments[seg_i]
            ph = tuple(s["p0"][k] + (s["p1"][k] - s["p0"][k]) * t_pos
                       for k in range(3))
            halter.append({"host_row": ref, "seg": seg_i, "t": t_pos, "art": typ,
                           "kurz": kurz, "nr": "%s%s" % (kurz, nr_h), "lage": lage,
                           "bei": abst, "dn": host["dn"], "p": ph})

        # ---- Nahtliste: jede Naht mit Nummer, Lage und Art ----------------
        # Werkstatt- oder Baustellennaht: alles am Montagestoss und an den
        # freien Kettenenden gilt als Baustellennaht, der Rest als Werkstatt.
        nahtliste = []

        def _naht(seg_i, tt, art, dnw, feld, was, punkt=None, anker=None):
            """anker sagt der Zeichnung, wo die Naht sitzt:
            ("seg", Segmentindex, Anteil) oder ("br", Abzweigindex, mm ab Wurzel).
            Die Zeichnung ist gestaucht, darum reicht der wahre Punkt nicht."""
            if seg_i is None or not (0 <= seg_i < len(segments)):
                return
            if punkt is None:
                s = segments[seg_i]
                punkt = tuple(s["p0"][k] + (s["p1"][k] - s["p0"][k]) * tt
                              for k in range(3))
            nahtliste.append({"seg": seg_i, "t": tt, "art": art, "dn": dnw,
                              "feld": feld, "was": was, "p": punkt,
                              "anker": anker or ("seg", seg_i, tt)})

        montage_rows = {it["row"] for it in items if it["part"] == "Montagestoss"}
        if count_ends and frei_a in ("S", "F"):
            _naht(seg_von[items[0]["row"]], 0.0,
                  "Flanschverbindung" if frei_a == "F" else "Rundnaht",
                  items[0]["dn"], True, "Anschluss Anfang")
        for k, jt in enumerate(joints):
            if jt is None:
                continue
            a_it, b_it = items[k], items[k + 1]
            feld = a_it["row"] in montage_rows or b_it["row"] in montage_rows
            _naht(seg_bis[a_it["row"]], 1.0,
                  "Flanschverbindung" if jt == "flansch" else "Rundnaht",
                  a_it["dn"], feld, "%s / %s" % (a_it["part"], b_it["part"]))
        for it in items:
            if it["part"] == "Versprung":
                sd = seg_von[it["row"]] + 1          # das schraege Rohr
                _naht(sd, 0.0, "Rundnaht", it["dn"], False, "Bogen / Schraegrohr")
                _naht(sd, 1.0, "Rundnaht", it["dn"], False, "Schraegrohr / Bogen")
                for j in range(1, _stoss(it["vers"]["saege"]) + 1):
                    _naht(sd, j / (_stoss(it["vers"]["saege"]) + 1.0), "Rundnaht",
                          it["dn"], False, "Rohrstoss Schraegrohr")
            elif it["part"] == "Rohr" and stock and it["len"] > stock:
                n_st = _stoss(it["len"])
                for j in range(1, n_st + 1):
                    _naht(seg_von[it["row"]], j / (n_st + 1.0), "Rundnaht",
                          it["dn"], False, "Rohrstoss")
        for bi, br in enumerate(branch_out):
            s = segments[br["seg"]]
            tb = br.get("t", 0.5)
            def _bn(art_, dn_, feld_, was_, punkt_, mm_):
                _naht(br["seg"], tb, art_, dn_, feld_, was_, punkt_,
                      anker=("br", bi, mm_))
            wurzel = tuple(s["p0"][k] + (s["p1"][k] - s["p0"][k]) * tb
                           for k in range(3))
            if br["art"] == "Fertig-T":
                _bn("Rundnaht", s["dn"], False, "Fertig-T Durchgang 1", wurzel, 0.0)
                _bn("Rundnaht", s["dn"], False, "Fertig-T Durchgang 2", wurzel, 0.0)
            else:
                # Sattelnaht laeuft um das Abzweigrohr -> Abzweig-DN
                _bn("Rundnaht", br["dn"], False,
                    "Anschweissstutzen auf DN %s" % s["dn"], wurzel, 0.0)
            # Stutzen/T -> Abzweigrohr
            p_rohr = tuple(wurzel[k] + br["d"][k] * br["arm"] for k in range(3))
            _bn("Rundnaht", br["dn"], False, "Abzweigrohr angeschweisst",
                p_rohr, br["arm"])
            # Rohrstoesse im Abzweigrohr
            n_st = _stoss(br["pipe"])
            for j in range(1, n_st + 1):
                sj = br["arm"] + br["pipe"] * j / (n_st + 1.0)
                pj = tuple(wurzel[k] + br["d"][k] * sj for k in range(3))
                _bn("Rundnaht", br["dn"], False, "Rohrstoss Abzweig", pj, sj)
            s_end = br["arm"] + br["pipe"]
            p_ende = tuple(wurzel[k] + br["d"][k] * s_end for k in range(3))
            if br["end"] == "Vorschweissflansch":
                _bn("Rundnaht", br["dn"], False, "Abzweig / Vorschweissflansch",
                    p_ende, s_end)
                _bn("Flanschverbindung", br["dn"], True, "Abzweig Flanschanschluss",
                    tuple(wurzel[k] + br["d"][k] * (s_end + br["end_len"])
                          for k in range(3)), s_end + br["end_len"])
            elif br["end"] == "Anschluss geschweisst":
                _bn("Rundnaht", br["dn"], True, "Abzweig Anschluss", p_ende, s_end)
        if count_ends and frei_b in ("S", "F"):
            _naht(seg_bis[items[-1]["row"]], 1.0,
                  "Flanschverbindung" if frei_b == "F" else "Rundnaht",
                  items[-1]["dn"], True, "Anschluss Ende")
        # Nummern laufen der Leitung entlang, nicht in der Reihenfolge, in der
        # sie oben eingesammelt wurden. Abzweignaehte haengen sich hinter die
        # Stelle, an der der Abzweig sitzt.
        def _weg(n):
            art, _idx, wert = n["anker"]
            return (n["seg"], n["t"], 0.0 if art == "seg" else 1.0 + float(wert))

        nahtliste.sort(key=_weg)
        for i, n in enumerate(nahtliste, 1):
            n["nr"] = "WF%d" % i
        # Zaehlung ausschliesslich aus der Liste - so koennen Liste und Summe
        # nicht mehr auseinanderlaufen.
        naehte = sum(1 for n in nahtliste if n["art"] == "Rundnaht")

        # ---- Saegeliste: nur die Rohre ------------------------------------
        # Anrissmasse der Stutzen dem jeweiligen Rohr zuordnen
        anriss_je_rohr = {}
        for br in branch_out:
            if br["anriss"] is not None and br["art"] == "Anschweissstutzen":
                anriss_je_rohr.setdefault(br["host_row"], []).append(
                    "%.0f (DN%d)" % (br["anriss"], br["dn"]))

        cut_rows = []
        for it in items:
            if it["part"] == "Versprung":
                v = it["vers"]
                ns = _stoss(v["saege"])
                cut_rows.append({
                    "Nr": it["row"], "Herkunft": "Versprung", "DN": it["dn"],
                    "Eingabe (mm)": round(v["versatz"]),
                    "Massart": "Versatz %g Grad" % v["winkel"],
                    "Abzug (mm)": round(2 * v["vorbau"]),
                    "Saegelaenge (mm)": round(v["saege"]),
                    "Stutzen bei (mm)": "", "Rohrstoesse": ns})
                continue
            if it["part"] != "Rohr":
                continue
            ns = _stoss(it["len"])
            cut_rows.append({
                "Nr": it["row"], "Herkunft": "Kette", "DN": it["dn"],
                "Eingabe (mm)": round(it["eingabe"]),
                "Massart": it["massart"],
                "Abzug (mm)": round(it["abzug"]),
                "Saegelaenge (mm)": round(it["len"]),
                "Stutzen bei (mm)": " / ".join(anriss_je_rohr.get(it["row"], [])) or "",
                "Rohrstoesse": ns})
        for br in branch_out:
            ns = _stoss(br["pipe"])
            cut_rows.append({
                "Nr": br["host_row"], "Herkunft": "Abzweig", "DN": br["dn"],
                "Eingabe (mm)": round(br["pipe"]), "Massart": "Rohrlaenge",
                "Abzug (mm)": 0, "Saegelaenge (mm)": round(br["pipe"]),
                "Stutzen bei (mm)": "", "Rohrstoesse": ns})

        # ---- Stueckliste ---------------------------------------------------
        rohr_m = {}
        for it in items:
            if it["part"] == "Rohr":
                rohr_m[it["dn"]] = rohr_m.get(it["dn"], 0.0) + it["len"]
            elif it["part"] == "Versprung":
                rohr_m[it["dn"]] = rohr_m.get(it["dn"], 0.0) + it["vers"]["saege"]
        for br in branch_out:
            rohr_m[br["dn"]] = rohr_m.get(br["dn"], 0.0) + br["pipe"]

        stueck = {}
        for it in items:
            if it["part"] in ("Rohr", "Montagestoss"):
                continue
            if it["part"] == "Versprung":
                key = ("Bogen %g Grad" % it["vers"]["winkel"], it["dn"])
                stueck[key] = stueck.get(key, 0) + 2
                continue
            key = (it["part"], it["dn"])
            stueck[key] = stueck.get(key, 0) + 1
        for br in branch_out:
            key = ("T-Stueck (Abzweig)" if br["art"] == "Fertig-T" else "Anschweissstutzen",
                   br["dn"] if br["art"] == "Anschweissstutzen" else br["dn"])
            stueck[key] = stueck.get(key, 0) + 1
            if br["end"] in ("Vorschweissflansch", "Blindflansch"):
                k2 = (br["end"], br["dn"])
                stueck[k2] = stueck.get(k2, 0) + 1

        mto = []
        for d in sorted(rohr_m):
            mto.append({"Position": "Rohr DN%d" % d, "Menge": "%.2f m" % (rohr_m[d] / 1000.0)})
        for (part, d), n in sorted(stueck.items()):
            mto.append({"Position": "%s DN%d" % (part, d), "Menge": "%d St" % n})
        dicht = {}
        for d in flanschverb:
            dicht[d] = dicht.get(d, 0) + 1
        for d in sorted(dicht):
            r = self.get_row(d)
            mto.append({"Position": "Flanschdichtung DN%d %s" % (d, pn),
                        "Menge": "%d St" % dicht[d]})
            mto.append({"Position": "Schraubensatz %s (DN%d)" % (r["Schraube_M%s" % suffix], d),
                        "Menge": "%d St  (%d x %d)" % (dicht[d] * int(r["Lochzahl%s" % suffix]),
                                                       dicht[d], int(r["Lochzahl%s" % suffix]))})
        mto.append({"Position": "Rundnaehte gesamt (Richtwert)", "Menge": "%d St" % naehte})

        # ---- Positionsnummern + erweiterte Stueckliste ---------------------
        # Jede Bauteilart-DN-Kombination bekommt eine Positionsnummer. Die
        # Nummer haengt am Bauteil, damit die Skizze Ballons setzen kann.
        def _wand(d):
            nps = PipeRef.nps_for_dn(int(d))
            if not nps:
                return None
            return PipeRef.SCHEDULE[nps][2].get(schedule)

        NORM = {
            "Rohr": "EN 10216-2",
            "Bogen 90": "EN 10253-2",
            "T-Stueck": "EN 10253-2",
            "T-Stueck (Abzweig)": "EN 10253-2",
            "Reduzierung": "EN 10253-2",
            "Vorschweissflansch": "EN 1092-1 Typ 11",
            "Blindflansch": "EN 1092-1 Typ 05",
            "Anschweissstutzen": "MSS SP-97",
            "Armatur geschweisst": "EN 558",
            "Armatur mit Flanschen": "EN 558",
        }
        pos_rows, pos_von_key, nr_ = [], {}, 0

        # Wanddicke nur da, wo sie beim Bestellen wirklich zaehlt: Rohr,
        # Schweissformteile und der Vorschweissflansch (dessen Bohrung muss
        # zur Wand passen). Armatur, Blindflansch, Dichtung und Schrauben
        # haben keine.
        MIT_WAND = ("Rohr", "Bogen", "T-Stueck", "Reduzierung",
                    "Anschweissstutzen", "Vorschweissflansch")

        def _pos(key, benennung, menge, d, norm=None, werk=None):
            nonlocal nr_
            nr_ += 1
            pos_von_key[key] = nr_
            w = _wand(d) if (d and benennung.startswith(MIT_WAND)) else None
            pos_rows.append({
                "Pos": nr_, "Anzahl": menge, "Benennung": benennung,
                "DN": d if d else "",
                "Wand (mm)": ("%.2f" % w) if w else "",
                "Werkstoff": werk if werk is not None else werkstoff,
                "Norm": norm if norm is not None else (NORM.get(benennung, "")),
            })

        for d in sorted(rohr_m):
            _pos(("Rohr", d), "Rohr", "%.2f m" % (rohr_m[d] / 1000.0), d,
                 norm="EN 10216-2")
        for (part, d), n in sorted(stueck.items()):
            _pos((part, d), part, "%d St" % n, d,
                 norm=NORM.get(part, "EN 10253-2" if part.startswith("Bogen") else ""))
        for d in sorted(dicht):
            r = self.get_row(d)
            _pos(("Dichtung", d), "Flanschdichtung %s" % pn, "%d St" % dicht[d], d,
                 norm="EN 1514-1", werk="nach Spezifikation")
            _pos(("Schrauben", d), "Schraubensatz %s" % r["Schraube_M%s" % suffix],
                 "%d St" % (dicht[d] * int(r["Lochzahl%s" % suffix])), d,
                 norm="EN 1515-1", werk="nach Spezifikation")

        # Positionsnummer an die Bauteile haengen (fuer die Ballons)
        for it in items:
            if it["part"] == "Versprung":
                it["pos"] = pos_von_key.get(("Bogen %g Grad" % it["vers"]["winkel"],
                                             it["dn"]))
            elif it["part"] == "Montagestoss":
                it["pos"] = None
            else:
                it["pos"] = pos_von_key.get((it["part"], it["dn"]))
        for br in branch_out:
            br["pos"] = pos_von_key.get(
                ("T-Stueck (Abzweig)" if br["art"] == "Fertig-T"
                 else "Anschweissstutzen", br["dn"]))

        total = sum(s["len"] for s in segments) + sum(b["arm"] + b["pipe"] + b["end_len"]
                                                     for b in branch_out)
        naht_rows = [{"Naht": n["nr"], "Art": n["art"], "DN": n["dn"],
                      "Ort": n["was"],
                      "Werkstatt/Feld": "Baustelle" if n["feld"] else "Werkstatt",
                      "X (mm)": round(n["p"][0]), "Y (mm)": round(n["p"][1]),
                      "Z (mm)": round(n["p"][2])} for n in nahtliste]
        halter_rows = [{"Halterung": h["nr"], "Art": h["art"], "An Bauteil": h["host_row"],
                        "Bei (mm)": "" if h["bei"] is None else round(h["bei"]),
                        "Lage": h["lage"], "DN": h["dn"],
                        "X (mm)": round(h["p"][0]), "Y (mm)": round(h["p"][1]),
                        "Z (mm)": round(h["p"][2])} for h in halter]
        return {"halter": halter, "halter_rows": halter_rows,
                "nahtliste": nahtliste, "naht_rows": naht_rows,
                "pos_rows": pos_rows, "werkstoff": werkstoff, "schedule": schedule,
                "items": items, "segments": segments, "branches": branch_out,
                "joints": joints, "naehte": naehte,
                "flanschverbindungen": len(flanschverb), "offene_enden": offene,
                "el_start": float(el_start), "dir_start": dir_start,
                "total_axis": total, "mto": mto, "cut_rows": cut_rows,
                "warnings": warnings}

class MaterialManager:
    @staticmethod
    def parse_dn(dim_str: str) -> int:
        if not dim_str: return 0
        try:
            match = re.search(r'\d+', str(dim_str))
            if match: return int(match.group())
            return 0
        except (KeyError, IndexError, ValueError): return 0
    @staticmethod
    def generate_mto(df_log: pd.DataFrame) -> pd.DataFrame:
        if df_log.empty: return pd.DataFrame()
        df = df_log.copy()
        df['dn_clean'] = df['dimension'].apply(MaterialManager.parse_dn)
        linear_items = ['Rohrstoß', 'Passstück', 'Rohr']
        df_linear = df[df['bauteil'].isin(linear_items)].copy()
        if not df_linear.empty:
            df_linear['menge'] = pd.to_numeric(df_linear['laenge'], errors='coerce').fillna(0) / 1000.0
            mto_linear = df_linear.groupby(['dn_clean', 'bauteil'])['menge'].sum().reset_index()
            mto_linear['Einheit'] = 'm'
        else:
            mto_linear = pd.DataFrame(columns=['dn_clean', 'bauteil', 'menge', 'Einheit'])
        df_count = df[~df['bauteil'].isin(linear_items)].copy()
        if not df_count.empty:
            mto_count = df_count.groupby(['dn_clean', 'bauteil']).size().reset_index(name='menge')
            mto_count['Einheit'] = 'Stk'
        else:
            mto_count = pd.DataFrame(columns=['dn_clean', 'bauteil', 'menge', 'Einheit'])
        mto_final = pd.concat([mto_linear, mto_count], ignore_index=True)
        mto_final['Dimension'] = mto_final['dn_clean'].apply(lambda x: f"DN {x}")
        mto_final = mto_final.rename(columns={'bauteil': 'Beschreibung', 'menge': 'Menge'})
        mto_final = mto_final[['Dimension', 'Beschreibung', 'Menge', 'Einheit']].sort_values(['Dimension', 'Beschreibung'])
        return mto_final

class HandbookCalculator:
    BOLT_DATA = {"M12": [19, 85, 55], "M16": [24, 210, 135], "M20": [30, 410, 265], "M24": [36, 710, 460], "M27": [41, 1050, 680], "M30": [46, 1420, 920], "M33": [50, 1930, 1250], "M36": [55, 2480, 1600], "M39": [60, 3200, 2080], "M45": [70, 5000, 3250], "M52": [80, 7700, 5000]}
    @staticmethod
    def calculate_weight(od, wall, length):
        if wall <= 0: return {"steel": 0, "water": 0, "total": 0}
        id_mm = od - (2*wall)
        vol_s = (math.pi*(od**2 - id_mm**2)/4)/1000000
        vol_w = (math.pi*(id_mm**2)/4)/1000000
        return {"kg_per_m_steel": vol_s*7850, "total_steel": vol_s*7850*(length/1000), "total_filled": (vol_s*7850 + vol_w*1000)*(length/1000), "volume_l": vol_w*(length/1000)*1000}
    # EN 1092-1 Typ 11: Flansch-BLATTDICKE C (mm, ohne Dichtleiste) - Richtwert.
    # PN 10 und PN 16 sind bis DN 150 gleich; darueber PN-16-Werte (leicht konservativ).
    FLANGE_THK_C = {
        15: 16, 20: 18, 25: 18, 32: 18, 40: 18, 50: 20, 65: 20, 80: 20, 100: 20,
        125: 22, 150: 22, 200: 24, 250: 26, 300: 28, 350: 30, 400: 32, 450: 36,
        500: 38, 600: 42, 700: 46, 800: 50, 900: 54, 1000: 58, 1200: 66,
        1400: 74, 1600: 82,
    }

    @classmethod
    def flange_thickness_c(cls, dn: int) -> float:
        """Flansch-Blattdicke C (mm) nach EN 1092-1 Typ 11 - Richtwert.
        Zwischen-/Uebergroessen: naechstkleinerer Tabellenwert."""
        keys = sorted(cls.FLANGE_THK_C)
        if dn in cls.FLANGE_THK_C:
            return float(cls.FLANGE_THK_C[dn])
        below = [k for k in keys if k <= dn]
        return float(cls.FLANGE_THK_C[below[-1] if below else keys[0]])

    # Regelsteigung metrisches ISO-Grobgewinde (mm)
    THREAD_PITCH = {12: 1.75, 16: 2.0, 20: 2.5, 24: 3.0, 27: 3.0, 30: 3.5,
                    33: 3.5, 36: 4.0, 39: 4.0, 45: 4.5, 52: 5.0}

    @classmethod
    def get_bolt_length(cls, t1: float, t2: float, bolt: str, washers: int = 0,
                        gasket: float = 2.0, stud: bool = False,
                        raised_face: float = 2.0, washer_thk: float = 0.0) -> int:
        """Schrauben-/Stiftschraubenlaenge fuer eine EN-1092-1-Flanschverbindung.

        Standard (EN-Praxis): Sechskantschraube + 1 Mutter, Laenge unter Kopf:
          L = C1 + C2 + 2*rf + g + n + s
        Stiftschraube (stud=True): zweite Mutter + zweiter Ueberstand:
          L = C1 + C2 + 2*rf + g + 2*(n + s)
        mit  C  = Flansch-Blattdicke je Seite (t1, t2)
             rf = Dichtleistenhoehe EN 1092-1 Form B1 = 2 mm je Seite
             n  = Mutternhoehe ~ 0,85*d  (DIN EN ISO 4032)
             s  = freies Gewinde je Ende = 2 volle Gaenge (2*Steigung), min. 3 mm
             g  = verpresste Dichtungsdicke
        Aufrundung auf 5 mm (uebliche Laengenstufe). Dadurch stehen real meist
        ~2-4 Gaenge ueber die Mutter (>= ASME PCC-1: 2 volle Gaenge).
        """
        try:
            d = int(str(bolt).replace("M", "").split("x")[0].strip())
        except (AttributeError, ValueError):
            return 0
        pitch = cls.THREAD_PITCH.get(d, max(1.5, d / 8.0))
        n = 0.85 * d                       # Mutternhoehe
        s = max(3.0, 2.0 * pitch)          # 2 volle Gewindegaenge je Ende
        wt = washer_thk if washer_thk > 0 else max(3.0, 0.18 * d)
        ends = 2 if stud else 1
        length = (t1 + t2 + 2.0 * raised_face + gasket
                  + ends * (n + s)
                  + max(0, washers) * wt)
        return int(math.ceil(length / 5.0) * 5)


class FieldCalc:
    """Universelle Feld-Rechner: Trigonometrie, Gefälle, Rollnaht, Einheiten, Kreisteilung."""

    # ------------------------------------------------ Trigonometrie ----------
    @staticmethod
    def right_triangle(a=None, b=None, c=None, alpha=None) -> Dict[str, Any]:
        """Rechtwinkliges Dreieck. a = Ankathete zu alpha, b = Gegenkathete zu alpha,
        c = Hypotenuse, alpha in Grad. Genau zwei Groessen angeben."""
        if sum(v is not None for v in (a, b, c, alpha)) < 2:
            return {"error": "Mindestens zwei Werte angeben."}
        A = math.radians(alpha) if alpha is not None else None
        try:
            if a is not None and b is not None:
                c = math.hypot(a, b); A = math.atan2(b, a)
            elif a is not None and c is not None:
                if c <= a: return {"error": "Hypotenuse muss groesser als Kathete sein."}
                b = math.sqrt(c*c - a*a); A = math.acos(a / c)
            elif b is not None and c is not None:
                if c <= b: return {"error": "Hypotenuse muss groesser als Kathete sein."}
                a = math.sqrt(c*c - b*b); A = math.asin(b / c)
            elif a is not None and A is not None:
                b = a * math.tan(A); c = a / math.cos(A)
            elif b is not None and A is not None:
                a = b / math.tan(A); c = b / math.sin(A)
            elif c is not None and A is not None:
                a = c * math.cos(A); b = c * math.sin(A)
            else:
                return {"error": "Zwei Winkel ohne Seite reichen nicht."}
        except (ValueError, ZeroDivisionError):
            return {"error": "Ungueltige Eingabe."}
        alpha_deg = math.degrees(A)
        return {"a": a, "b": b, "c": c, "alpha": alpha_deg,
                "beta": 90.0 - alpha_deg, "area": 0.5 * a * b}

    @staticmethod
    def oblique_triangle(a=None, b=None, c=None, gamma=None) -> Dict[str, Any]:
        """Schraeges Dreieck (Kosinussatz).
        Fall 1: a, b, gamma (eingeschlossener Winkel) -> c + uebrige Winkel.
        Fall 2: a, b, c -> alle Winkel."""
        try:
            if a and b and gamma is not None:
                G = math.radians(gamma)
                c = math.sqrt(a*a + b*b - 2*a*b*math.cos(G))
            elif a and b and c:
                G = math.acos(max(-1.0, min(1.0, (a*a + b*b - c*c) / (2*a*b))))
            else:
                return {"error": "Entweder (a, b, gamma) oder (a, b, c) angeben."}
            alpha = math.acos(max(-1.0, min(1.0, (b*b + c*c - a*a) / (2*b*c))))
            beta = math.pi - alpha - G
            if beta <= 0:
                return {"error": "Kein gueltiges Dreieck mit diesen Werten."}
            s = (a + b + c) / 2.0
            area = math.sqrt(max(0.0, s*(s-a)*(s-b)*(s-c)))
            return {"a": a, "b": b, "c": c, "alpha": math.degrees(alpha),
                    "beta": math.degrees(beta), "gamma": math.degrees(G),
                    "area": area, "umfang": a + b + c}
        except (ValueError, ZeroDivisionError):
            return {"error": "Kein gueltiges Dreieck mit diesen Werten."}

    # ------------------------------------------------ Kreisteilung ---------
    @staticmethod
    def divide_circle(diameter: float, n: int, by: str = "Durchmesser") -> Dict[str, Any]:
        """Teilt einen Kreis in n gleiche Teile.
        by = 'Durchmesser' (Teil-/Lochkreis) oder 'Umfang' (gemessener Umfang)."""
        if n < 2:
            return {"error": "Mindestens 2 Teile."}
        if by == "Umfang":
            circ = diameter
            D = circ / math.pi
        else:
            D = diameter
            circ = math.pi * D
        R = D / 2.0
        step_deg = 360.0 / n
        chord = 2.0 * R * math.sin(math.pi / n)
        across = D if n % 2 == 0 else 2.0 * R * math.cos(math.pi / (2.0 * n))
        points = []
        for i in range(n):
            ang = math.radians(i * step_deg - 90.0)          # Start am Scheitel
            points.append({
                "Nr": i + 1,
                "Winkel": f"{i * step_deg:.1f} Grad",
                "X (mm)": round(R + R * math.cos(ang), 2),
                "Y (mm)": round(R + R * math.sin(ang), 2),
                "Sehne ab Nr.1 (mm)": round(2.0 * R * math.sin(math.pi * i / n), 2),
            })
        return {"D": D, "R": R, "circ": circ, "step_deg": step_deg,
                "arc": circ / n, "chord": chord, "across": across, "points": points}


class PipeRef:
    """Nachschlagewerte: Rohrmaße / Schedule (ASME B36.10M).
    Werte sind Richtwerte - im Zweifel gilt die Norm."""

    # ASME B36.10M: OD (mm) und Wanddicke (mm) je Schedule.
    # Spalte "STD" = Sch40 bis NPS 12, danach fest 9,53 mm (Sch40 weicht ab).
    # Spalte "XS"  = Sch80 bis NPS 8,  danach fest 12,7 mm.
    SCHEDULE = {
        # NPS: (DN, OD, {Sch10, STD, XS, Sch160, XXS})
        '1/2"':   (15,  21.34, {"Sch10": 2.11, "STD": 2.77, "XS": 3.73, "Sch160": 4.78,  "XXS": 7.47}),
        '3/4"':   (20,  26.67, {"Sch10": 2.11, "STD": 2.87, "XS": 3.91, "Sch160": 5.56,  "XXS": 7.82}),
        '1"':     (25,  33.40, {"Sch10": 2.77, "STD": 3.38, "XS": 4.55, "Sch160": 6.35,  "XXS": 9.09}),
        '1 1/4"': (32,  42.16, {"Sch10": 2.77, "STD": 3.56, "XS": 4.85, "Sch160": 6.35,  "XXS": 9.70}),
        '1 1/2"': (40,  48.26, {"Sch10": 2.77, "STD": 3.68, "XS": 5.08, "Sch160": 7.14,  "XXS": 10.16}),
        '2"':     (50,  60.33, {"Sch10": 2.77, "STD": 3.91, "XS": 5.54, "Sch160": 8.74,  "XXS": 11.07}),
        '2 1/2"': (65,  73.03, {"Sch10": 3.05, "STD": 5.16, "XS": 7.01, "Sch160": 9.53,  "XXS": 14.02}),
        '3"':     (80,  88.90, {"Sch10": 3.05, "STD": 5.49, "XS": 7.62, "Sch160": 11.13, "XXS": 15.24}),
        '4"':     (100, 114.30, {"Sch10": 3.05, "STD": 6.02, "XS": 8.56, "Sch160": 13.49, "XXS": 17.12}),
        '5"':     (125, 141.30, {"Sch10": 3.40, "STD": 6.55, "XS": 9.53, "Sch160": 15.88, "XXS": 19.05}),
        '6"':     (150, 168.28, {"Sch10": 3.40, "STD": 7.11, "XS": 10.97, "Sch160": 18.26, "XXS": 21.95}),
        '8"':     (200, 219.08, {"Sch10": 3.76, "STD": 8.18, "XS": 12.70, "Sch160": 23.01, "XXS": 22.23}),
        '10"':    (250, 273.05, {"Sch10": 4.19, "STD": 9.27, "XS": 12.70, "Sch160": 28.58, "XXS": 25.40}),
        '12"':    (300, 323.85, {"Sch10": 4.57, "STD": 9.53, "XS": 12.70, "Sch160": 33.32, "XXS": 25.40}),
        '14"':    (350, 355.60, {"Sch10": 6.35, "STD": 9.53, "XS": 12.70, "Sch160": 35.71, "XXS": None}),
        '16"':    (400, 406.40, {"Sch10": 6.35, "STD": 9.53, "XS": 12.70, "Sch160": 40.49, "XXS": None}),
        '18"':    (450, 457.20, {"Sch10": 6.35, "STD": 9.53, "XS": 12.70, "Sch160": 45.24, "XXS": None}),
        '20"':    (500, 508.00, {"Sch10": 6.35, "STD": 9.53, "XS": 12.70, "Sch160": 50.01, "XXS": None}),
        '24"':    (600, 609.60, {"Sch10": 6.35, "STD": 9.53, "XS": 12.70, "Sch160": 59.54, "XXS": None}),
    }

    @staticmethod
    def nps_for_dn(dn: int):
        """DN -> NPS-Schluessel der SCHEDULE-Tabelle (verbindet die beiden Datenquellen)."""
        for nps, (d, _od, _w) in PipeRef.SCHEDULE.items():
            if d == dn:
                return nps
        return None

    @staticmethod
    def schedule_rows(nps: str):
        """Tabelle Schedule -> Wand / Innendurchmesser fuer eine Nennweite."""
        if nps not in PipeRef.SCHEDULE:
            return None
        dn, od, walls = PipeRef.SCHEDULE[nps]
        rows = []
        for name, w in walls.items():
            if w is None:
                rows.append({"Schedule": name, "Wand (mm)": "-", "Innen-Ø (mm)": "-"})
            else:
                rows.append({"Schedule": name, "Wand (mm)": w,
                             "Innen-Ø (mm)": round(od - 2 * w, 1)})
        return {"dn": dn, "od": od, "rows": rows}
