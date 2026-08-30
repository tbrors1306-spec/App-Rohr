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
    @staticmethod
    def get_bolt_length(t1, t2, bolt, washers=2, gasket=2.0):
        try:
            d = int(bolt.replace("M", ""))
            l = t1 + t2 + gasket + (washers*4) + (d*0.8) + max(6, d*0.4)
            rem = l % 5
            return int(l + (5-rem) if rem != 0 else l)
        except (KeyError, IndexError, ValueError): return 0


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
