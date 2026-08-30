import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from io import BytesIO
from datetime import datetime

# Optional Imports
try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    PDF_AVAILABLE = False
    class FPDF: pass # Dummy

try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    PLOTLY_AVAILABLE = False

class Visualizer:
    @staticmethod
    def plot_branch_development(dev_s, dev_h, branch_circ, hole_u, hole_a):
        """Zwei 1:1-Schablonen: links Stutzen-Abwicklung (Abtrag h über Umfangsmaß s),
        rechts der zugehörige Ausschnitt im Hauptrohr."""
        fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))

        # --- Stutzen-Schablone: Sattelschnitt-Kurve ---
        ax = axes[0]
        h_top = max(dev_h) * 1.15 if max(dev_h) > 0 else 1.0
        ax.plot(dev_s, dev_h, color='#dc2626', lw=2)
        ax.fill_between(dev_s, dev_h, h_top, color='#fee2e2', alpha=0.7)
        ax.set_title("Stutzen-Schablone (Abwicklung)", fontsize=10, fontweight='bold')
        ax.set_xlabel("Umfangsmaß s ab Anreißlinie [mm]")
        ax.set_ylabel("Abtrag h [mm]")
        ax.set_xlim(0, branch_circ)
        ax.set_ylim(h_top, 0)  # 0 oben = Rohrende
        ax.grid(True, linestyle='--', alpha=0.4)

        # --- Ausschnitt Hauptrohr: geschlossene Anreißkurve ---
        ax = axes[1]
        ax.plot(hole_u, hole_a, color='#0ea5e9', lw=2)
        ax.fill(hole_u, hole_a, color='#e0f2fe', alpha=0.7)
        ax.axhline(0, color='#94a3b8', lw=0.8, ls='--')
        ax.axvline(0, color='#94a3b8', lw=0.8, ls='--')
        ax.set_title("Ausschnitt Hauptrohr", fontsize=10, fontweight='bold')
        ax.set_xlabel("Umfang ab Scheitel [mm]")
        ax.set_ylabel("Achsmaß [mm]")
        ax.set_aspect('equal', 'box')
        ax.grid(True, linestyle='--', alpha=0.4)

        plt.tight_layout()
        plt.close(fig)
        return fig

    @staticmethod
    def plot_bolt_circle(points, D):
        """Kreisteilung / Lochbild: Punkte auf dem Teilkreis, Nr. 1 am Scheitel."""
        R = D / 2.0
        fig, ax = plt.subplots(figsize=(4.2, 4.2))
        circle = plt.Circle((R, R), R, fill=False, color='#94a3b8', ls='--', lw=1)
        ax.add_patch(circle)
        xs = [p["X (mm)"] for p in points]
        ys = [p["Y (mm)"] for p in points]
        ax.scatter(xs, ys, s=60, color='#0ea5e9', zorder=3)
        for p in points:
            ax.annotate(str(p["Nr"]), (p["X (mm)"], p["Y (mm)"]),
                        textcoords="offset points", xytext=(6, 6),
                        fontsize=8, fontweight='bold', color='#0f172a')
        # Sehne zwischen Nr.1 und Nr.2 hervorheben
        if len(points) >= 2:
            ax.plot([xs[0], xs[1]], [ys[0], ys[1]], color='#dc2626', lw=2, zorder=2)
        ax.set_xlim(-R*0.25, D + R*0.25)
        ax.set_ylim(-R*0.25, D + R*0.25)
        ax.set_aspect('equal', 'box')
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.set_title("Lochbild (Nr. 1 = Scheitel)", fontsize=10, fontweight='bold')
        plt.tight_layout()
        plt.close(fig)
        return fig

    @staticmethod
    def plot_2d_offset(run: float, offset: float):
        fig, ax = plt.subplots(figsize=(6, 2.5))
        x = [0, run, run*1.5] 
        y = [0, offset, offset]
        ax.plot([0, run], [0, offset], color='#dc2626', linewidth=3, label='Rohrachse') 
        ax.plot([run, run*1.5], [offset, offset], color='black', linewidth=3) 
        ax.plot([-50, 0], [0, 0], color='black', linewidth=3) 
        ax.plot([0, run], [0, 0], linestyle='--', color='gray', alpha=0.7) 
        ax.plot([run, run], [0, offset], linestyle='--', color='gray', alpha=0.7) 
        ax.text(run/2, -offset*0.1 if offset!=0 else -10, f"Länge: {run:.0f}", ha='center', color='blue')
        ax.text(run + (run*0.05), offset/2, f"H: {offset:.0f}", va='center', color='blue')
        ax.set_aspect('equal')
        ax.axis('off')
        plt.tight_layout()
        plt.close(fig)
        return fig
    @staticmethod
    def plot_rolling_offset_3d_room(roll: float, run: float, set_val: float):
        fig = plt.figure(figsize=(7, 6))
        ax = fig.add_subplot(111, projection='3d')
        P0 = np.array([0, 0, 0])
        P1 = np.array([roll, run, set_val])
        max_dim = max(abs(roll), abs(run), abs(set_val), 100)
        xx, yy = np.meshgrid(np.linspace(-max_dim*0.2, roll*1.2, 2), np.linspace(-max_dim*0.2, run*1.2, 2))
        zz = np.zeros_like(xx)
        ax.plot_surface(xx, yy, zz, color='gray', alpha=0.1)
        ax.plot([0, 0], [-run*0.3, 0], [0, 0], color='gray', linewidth=4, alpha=0.6)
        ax.plot([P0[0], P1[0]], [P0[1], P1[1]], [P0[2], P1[2]], color='#dc2626', linewidth=5, label='Passstück')
        ax.plot([P1[0], P1[0]], [P1[1], P1[1]+run*0.3], [P1[2], P1[2]], color='gray', linewidth=4, alpha=0.6)
        ax.scatter([P0[0], P1[0]], [P0[1], P1[1]], [P0[2], P1[2]], color='#1e3a8a', s=100, label='Naht/Flansch')
        ax.plot([P1[0], P1[0]], [P1[1], P1[1]], [0, P1[2]], 'b--', linewidth=1, label='Höhe (Set)')
        ax.plot([0, P1[0]], [P1[1], P1[1]], [0, 0], 'g--', linewidth=1, label='Seite (Roll)')
        ax.set_xlabel('Seite (Roll)')
        ax.set_ylabel('Länge (Run)')
        ax.set_zlabel('Höhe (Set)')
        try: 
            ax.set_box_aspect([roll if roll>10 else 100, run if run>10 else 100, set_val if set_val>10 else 100])
        except Exception: 
            pass 
        ax.legend(loc='upper left', fontsize='small')
        plt.close(fig)
        return fig
    @staticmethod
    def plot_rotation_gauge(roll: float, set_val: float, rotation_angle: float):
        fig, ax = plt.subplots(figsize=(3, 3), subplot_kw={'projection': 'polar'})
        theta = math.radians(rotation_angle)
        ax.arrow(0, 0, theta, 0.9, head_width=0.1, head_length=0.1, fc='#ef4444', ec='#ef4444', length_includes_head=True)
        ax.set_theta_zero_location("N") 
        ax.set_theta_direction(-1)      
        ax.set_rticks([])               
        ax.set_rlim(0, 1)
        ax.grid(True, alpha=0.3)
        ax.set_title(f"Verdrehung: {rotation_angle:.1f}°", va='bottom', fontsize=10, fontweight='bold')
        ax.text(math.radians(90), 1.2, "R", ha='center', fontweight='bold')
        ax.text(math.radians(270), 1.2, "L", ha='center', fontweight='bold')
        plt.close(fig)
        return fig
    @staticmethod
    def plot_segment_bend(radius: float, od: float, num_segments: int,
                          total_angle: float):
        """Gesamtansicht des zusammengebauten Segment-Bogens: Achsbogen, die
        geraden Stuecke als Tangenten-Polygon, Ruecken (aussen) und Bauch (innen),
        die Schweissnaehte und der Knickwinkel je Naht."""
        n = max(2, min(int(num_segments), 14))
        T = math.radians(total_angle)
        tau = T / (n - 1)                       # Knick je Naht (rad)
        cut = tau / 2.0                         # Saegeblatt-Neigung je Flaeche

        def A(phi):                            # Punkt auf dem Achsbogen (Winkel ab Start)
            a = math.pi / 2 + T / 2 - phi
            return (radius * math.cos(a), radius * math.sin(a))

        def tang(phi):                        # Tangenten-Einheitsvektor (Laufrichtung)
            a = math.pi / 2 + T / 2 - phi
            return (math.sin(a), -math.cos(a))

        def outn(phi):                        # radiale Aussennormale
            a = math.pi / 2 + T / 2 - phi
            return (math.cos(a), math.sin(a))

        def inter(p1, d1, p2, d2):
            den = d1[0] * d2[1] - d1[1] * d2[0]
            if abs(den) < 1e-9:
                return p1
            s = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / den
            return (p1[0] + s * d1[0], p1[1] + s * d1[1])

        # Tangenten-(Beruehr-)Punkte: Endstuecke ueberstreichen tau/2, Vollsegmente tau
        tps = [tau / 4] + [i * tau for i in range(1, n - 1)] + [T - tau / 4]
        ext = radius * 0.45                   # Laenge der geraden Anschlussrohre

        fig, ax = plt.subplots(figsize=(6.4, 5.4))
        # Referenz-Achsbogen
        arc = [A(T * k / 200) for k in range(201)]
        ax.plot([p[0] for p in arc], [p[1] for p in arc], color='#cbd5e1', lw=1, ls=':')

        for off, col, name in ((od / 2, '#dc2626', 'Rücken'),
                               (-od / 2, '#2563eb', 'Bauch'),
                               (0.0, '#64748b', None)):
            pts = []
            lines = []
            for phi in tps:
                a = A(phi); nrm = outn(phi); d = tang(phi)
                p = (a[0] + off * nrm[0], a[1] + off * nrm[1])
                lines.append((p, d))
            # Anfangspunkt auf der geraden Zuleitung
            p0, d0 = lines[0]
            pts.append((p0[0] - d0[0] * ext, p0[1] - d0[1] * ext))
            for i in range(len(lines) - 1):   # Nahtpunkte = Schnitt benachbarter Segmentlinien
                pts.append(inter(*lines[i], *lines[i + 1]))
            pL, dL = lines[-1]
            pts.append((pL[0] + dL[0] * ext, pL[1] + dL[1] * ext))
            lw = 3.5 if name else 1.2
            ls = '-' if name else '--'
            ax.plot([p[0] for p in pts], [p[1] for p in pts], color=col, lw=lw, ls=ls,
                    label=name, solid_capstyle='round')
            if name is None:
                seam_pts = pts[1:-1]

        # Schweissnaehte quer einzeichnen + Knickwinkel an der ersten Naht
        for j, phi in enumerate([tau / 2 + k * tau for k in range(n - 1)]):
            a = A(phi); nrm = outn(phi)
            p_out = (a[0] + od / 2 * nrm[0], a[1] + od / 2 * nrm[1])
            p_in = (a[0] - od / 2 * nrm[0], a[1] - od / 2 * nrm[1])
            ax.plot([p_in[0], p_out[0]], [p_in[1], p_out[1]], color='#0f172a', lw=2)
        ax.annotate(f"Knick je Naht\n{math.degrees(tau):.1f}°",
                    xy=A(tau / 2), xytext=(A(tau / 2)[0] + radius * 0.15,
                                           A(tau / 2)[1] + od * 1.4),
                    fontsize=9, color='#0f172a',
                    arrowprops=dict(arrowstyle='->', color='#0f172a'))

        # Radius einzeichnen
        mid = A(T / 2)
        ax.plot([0, mid[0]], [0, mid[1]], color='#94a3b8', lw=1, ls='-.')
        ax.plot(0, 0, 'o', color='#94a3b8', ms=4)
        ax.text(mid[0] * 0.55, mid[1] * 0.55, f"R = {radius:.0f}", fontsize=9,
                color='#64748b', ha='center')

        ax.set_aspect('equal', 'box')
        ax.axis('off')
        ax.legend(fontsize=8, loc='lower left')
        ax.set_title(f"Segment-Bogen · {n} Segmente · {n - 1} Nähte · gesamt {total_angle:.0f}°",
                     fontsize=11, fontweight='bold')
        plt.tight_layout()
        plt.close(fig)
        return fig

    @staticmethod
    def plot_segment_schematic(mid_back: float, mid_belly: float, od: float, angle: float):
        fig, ax = plt.subplots(figsize=(6, 3))
        height = od
        top_len = mid_back
        bot_len = mid_belly
        x_top = [-top_len/2, top_len/2]
        x_bot = [-bot_len/2, bot_len/2]
        y_top = [height/2, height/2]
        y_bot = [-height/2, -height/2]
        ax.plot(x_top, y_top, 'r-', linewidth=3, label='Rücken')
        ax.plot(x_bot, y_bot, 'b-', linewidth=3, label='Bauch')
        ax.plot([x_top[0], x_bot[0]], [y_top[0], y_bot[0]], 'k--', linewidth=1)
        ax.plot([x_top[1], x_bot[1]], [y_top[1], y_bot[1]], 'k--', linewidth=1)
        ax.annotate(f"{top_len:.1f}", xy=(0, height/2 + height*0.1), ha='center', color='red', fontweight='bold')
        ax.annotate(f"{bot_len:.1f}", xy=(0, -height/2 - height*0.2), ha='center', color='blue', fontweight='bold')
        ax.set_title(f"Mittelstück ({angle:.1f}° Schnitt)", fontsize=10)
        ax.set_xlim(-top_len/2 - 50, top_len/2 + 50)
        ax.set_ylim(-height, height)
        ax.axis('off')
        plt.close(fig)
        return fig

    @staticmethod
    def plot_cutting_plan(bars):
        """
        Visualizes the cutting plan.
        bars: List of OptBar objects
        """
        if not bars: return None
        
        num_bars = len(bars)
        fig, ax = plt.subplots(figsize=(10, max(2, num_bars * 0.8)))
        
        y_pos = range(num_bars)
        bar_height = 0.6
        
        colors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#6366f1']
        
        for i, bar in enumerate(bars):
            # Base bar (faint outline for stock length)
            ax.barh(i, bar.length, height=bar_height, color='#f1f5f9', edgecolor='#cbd5e1', linewidth=1)
            
            x_start = 0
            for j, cut in enumerate(bar.cuts):
                color = colors[j % len(colors)]
                ax.barh(i, cut.length, height=bar_height, left=x_start, color=color, edgecolor='white', alpha=0.9)
                
                # Label if long enough
                if cut.length > bar.length * 0.05:
                   ax.text(x_start + cut.length/2, i, f"{cut.length:.0f}", ha='center', va='center', color='white', fontsize=8, fontweight='bold')
                else: 
                   # if very small, maybe don't label or label above?
                   pass
                   
                x_start += cut.length
                
                # Simulate small gap for saw width if needed, but visually we just stack them
                # In calculation we accounted for saw width, so x_start includes it effectively if we assume visualized length is purely material?
                # Optimization logic tracked raw usage. Let's assume passed cut.length is the component length.
                # Visualization of gap is nice but tricky. Let's stick to stacking.
            
            # Label remaining waste?
            if bar.waste > 0:
                 ax.text(bar.length, i, f"Rest: {bar.waste:.1f}", ha='right', va='center', color='#94a3b8', fontsize=8, alpha=0.8)

        ax.set_yticks(y_pos)
        ax.set_yticklabels([f"Stange {b.id}" for b in bars])
        ax.set_xlabel("Länge (mm)")
        ax.set_xlim(0, max(b.length for b in bars) * 1.05)
        ax.invert_yaxis()  # Top to bottom
        plt.tight_layout()
        plt.close(fig)
        return fig

    @staticmethod
    def plot_rolling_offset_interactive(roll, set_val, run_length, dn):
        """Creates interactive 3D plot using Plotly with explicit dimensions"""
        if not PLOTLY_AVAILABLE:
            return None
            
        # Coordinates
        # Start: (0, 0, 0)
        # End: (Roll, Run, Set)
        
        # Calculate travel length for title
        travel = (roll**2 + set_val**2 + run_length**2)**0.5
        
        fig = go.Figure()
        
        # 1. The Pipe (Diagonal Travel) - Red Thick Line
        fig.add_trace(go.Scatter3d(
            x=[0, roll], y=[0, run_length], z=[0, set_val],
            mode='lines+markers',
            line=dict(color='#dc2626', width=10),
            marker=dict(size=8, color='red'),
            name='Rohrweg (Hypotenuse)',
            hovertemplate='<b>Rohrweg</b><br>Länge: %{text:.1f}mm<extra></extra>',
            text=[0, travel]
        ))
        
        # 2. Wireframe Box (Dimensions)
        # Path: Origin -> Roll -> Run -> Set
        
        # Roll Component (X)
        fig.add_trace(go.Scatter3d(
            x=[0, roll], y=[0, 0], z=[0, 0],
            mode='lines+text',
            line=dict(color='blue', width=4, dash='solid'),
            text=['', f'Roll: {roll}mm'],
            textposition='top center',
            name='Roll (Seite)'
        ))
        
        # Run Component (Y)
        fig.add_trace(go.Scatter3d(
            x=[roll, roll], y=[0, run_length], z=[0, 0],
            mode='lines+text',
            line=dict(color='gray', width=4, dash='solid'),
            text=['', f'Run: {run_length:.1f}mm'],
            textposition='middle right',
            name='Run (Länge)'
        ))
        
        # Set Component (Z)
        fig.add_trace(go.Scatter3d(
            x=[roll, roll], y=[run_length, run_length], z=[0, set_val],
            mode='lines+text',
            line=dict(color='green', width=4, dash='solid'),
            text=['', f'Set: {set_val}mm'],
            textposition='middle left',
            name='Set (Höhe)'
        ))
        
        # Helper lines to complete the box
        # Vertical drop from end point to ground
        fig.add_trace(go.Scatter3d(
            x=[roll, roll], y=[run_length, run_length], z=[0, set_val],
            mode='lines',
            line=dict(color='lightgray', width=2, dash='dot'),
            showlegend=False,
            hoverinfo='skip'
        ))
        # Line from Roll end to projected end on ground
        fig.add_trace(go.Scatter3d(
            x=[roll, roll], y=[0, run_length], z=[set_val, set_val],
            mode='lines',
            line=dict(color='lightgray', width=2, dash='dot'),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Add floor grid
        max_dim = max(roll, run_length, set_val, 100) * 1.2
        
        fig.update_layout(
            title=dict(
                text=f'<b>3D Rolling Offset</b><br><sub>Travel: {travel:.1f}mm</sub>',
                x=0.5,
                xanchor='center'
            ),
            scene=dict(
                xaxis=dict(title='<b>Roll (Seite)</b>', range=[-10, max_dim]),
                yaxis=dict(title='<b>Run (Länge)</b>', range=[-10, max_dim]),
                zaxis=dict(title='<b>Set (Höhe)</b>', range=[-10, max_dim]),
                aspectmode='cube',
                camera=dict(eye=dict(x=1.6, y=1.6, z=1.2))
            ),
            margin=dict(l=0, r=0, b=0, t=50),
            height=600,
            showlegend=True,
            legend=dict(x=0.7, y=0.1)
        )

        return fig

    # ------------------------------------------------ Fallnaht / Stovepipe ---
    @staticmethod
    def plot_joint_prep(included_deg=60.0, land_mm=1.6, gap_mm=1.6, hilo_mm=0.0, wt_mm=8.0):
        """Querschnitt der V-Naht mit Öffnungswinkel, Steg (Land), Wurzelspalt, Hi-Lo."""
        half = math.radians(included_deg / 2.0)
        x_off = max(0.0, wt_mm - land_mm) * math.tan(half)   # horiz. Versatz oben je Seite
        g = gap_mm / 2.0
        body = max(x_off * 0.9, 6.0) + 6.0                   # Rohrkörper-Breite
        span = g + x_off + body
        h = hilo_mm

        fig, ax = plt.subplots(figsize=(6.8, 5.4))

        left = [(-g, 0), (-g, land_mm), (-g - x_off, wt_mm),
                (-span, wt_mm), (-span, 0)]
        right = [(g, h), (g, land_mm + h), (g + x_off, wt_mm + h),
                 (span, wt_mm + h), (span, h)]
        ax.add_patch(mpatches.Polygon(left, closed=True, facecolor='#dbeafe',
                                      edgecolor='#334155', lw=1.6, hatch='//'))
        ax.add_patch(mpatches.Polygon(right, closed=True, facecolor='#dbeafe',
                                      edgecolor='#334155', lw=1.6, hatch='\\\\'))

        # Wurzelspalt (unten)
        yb = -wt_mm * 0.30
        ax.plot([-g, -g], [0, yb], color='#dc2626', lw=0.7, ls=':')
        ax.plot([g, g], [0, yb], color='#dc2626', lw=0.7, ls=':')
        ax.annotate("", xy=(-g, yb), xytext=(g, yb),
                    arrowprops=dict(arrowstyle='<->', color='#dc2626', lw=1.5))
        ax.text(0, yb - wt_mm * 0.13, f"Wurzelspalt  {gap_mm:.1f} mm",
                ha='center', va='top', color='#dc2626', fontsize=11, fontweight='bold')

        # Steg / Land (links)
        xl = -span - body * 0.05
        ax.annotate("", xy=(xl, 0), xytext=(xl, land_mm),
                    arrowprops=dict(arrowstyle='<->', color='#0284c7', lw=1.6))
        ax.plot([-span, xl], [0, 0], color='#0284c7', lw=0.6, ls=':')
        ax.plot([-g, xl], [land_mm, land_mm], color='#0284c7', lw=0.6, ls=':')
        ax.text(xl - span * 0.04, land_mm / 2, f"Steg\n{land_mm:.1f} mm",
                ha='right', va='center', color='#0284c7', fontsize=10)

        # Wandstärke (rechts)
        xr = span + body * 0.05
        ax.annotate("", xy=(xr, h), xytext=(xr, wt_mm + h),
                    arrowprops=dict(arrowstyle='<->', color='#334155', lw=1.3))
        ax.text(xr + span * 0.04, wt_mm / 2 + h, f"Wand\n{wt_mm:.1f} mm",
                ha='left', va='center', color='#334155', fontsize=10)

        # Öffnungswinkel (Bogen an der Wurzel)
        arc = mpatches.Arc((0, land_mm), wt_mm * 1.0, wt_mm * 1.0, angle=0,
                           theta1=90 - included_deg / 2, theta2=90 + included_deg / 2,
                           color='#0f172a', lw=1.4)
        ax.add_patch(arc)
        ax.text(0, land_mm + wt_mm * 0.60, f"{included_deg:.0f}°",
                ha='center', color='#0f172a', fontsize=14, fontweight='bold')

        # Hi-Lo (rechts, innen)
        if hilo_mm > 0.05:
            xh = span - body * 0.45
            ax.annotate("", xy=(xh, 0), xytext=(xh, h),
                        arrowprops=dict(arrowstyle='<->', color='#f59e0b', lw=1.6))
            ax.plot([g, xh], [0, 0], color='#f59e0b', lw=0.6, ls=':')
            ax.text(xh, -wt_mm * 0.12, f"Hi-Lo {hilo_mm:.1f}", ha='center', va='top',
                    color='#f59e0b', fontsize=9)

        ax.set_xlim(-span * 1.30, span * 1.30)
        ax.set_ylim(yb - wt_mm * 0.34, wt_mm * 1.30)
        ax.set_aspect('equal', 'box')
        ax.axis('off')
        ax.set_title("Nahtvorbereitung – Querschnitt (V-Naht)", fontsize=12, fontweight='bold')
        plt.tight_layout()
        plt.close(fig)
        return fig

    @staticmethod
    def plot_electrode_angles(drag_deg=12.0, work_deg=6.0, band_lo=5.0, band_hi=15.0):
        """Interaktive Winkel-Ansicht: links Schleppwinkel (Seitenansicht),
        rechts Arbeitswinkel (Schnitt durch die Fuge). Der grüne Sektor ist der
        Richtwertbereich; die Elektrode wird rot, wenn sie ausserhalb liegt."""
        in_band = band_lo <= drag_deg <= band_hi
        ecol = '#16a34a' if in_band else '#dc2626'
        fig, (axL, axR) = plt.subplots(1, 2, figsize=(10.5, 4.8))
        R = 6.4

        # ---------- links: Schleppwinkel (Seitenansicht) ----------
        axL.plot([-7.5, 7.5], [0, 0], color='#334155', lw=5)
        axL.annotate("Laufrichtung  12 → 6",
                     xy=(6.8, -1.4), xytext=(-6.8, -1.4),
                     arrowprops=dict(arrowstyle='->', color='#0ea5e9', lw=2),
                     color='#0ea5e9', fontsize=9, va='center')
        # Richtwert-Sektor (von der Senkrechten, schleppend = nach links)
        axL.add_patch(mpatches.Wedge((0, 0), R, 90 + band_lo, 90 + band_hi,
                                     facecolor='#86efac', alpha=0.55, edgecolor='none'))
        axL.plot([0, 0], [0, R], color='#94a3b8', lw=1, ls='--')
        axL.text(0.2, R - 0.2, "senkrecht", fontsize=7, color='#94a3b8')
        a = math.radians(90 + drag_deg)
        ex, ey = R * math.cos(a), R * math.sin(a)
        axL.plot([0, ex], [0, ey], color=ecol, lw=7, solid_capstyle='round', zorder=4)
        axL.add_patch(mpatches.Circle((0, 0), 0.18, color=ecol, zorder=5))
        axL.add_patch(mpatches.Arc((0, 0), 4.4, 4.4, angle=0, theta1=90,
                                   theta2=90 + drag_deg, color=ecol, lw=1.6))
        axL.text(-1.7, 3.3, f"{drag_deg:.0f}°", color=ecol, fontsize=13, fontweight='bold')
        axL.text(ex, ey + 0.5, "Elektrode", color=ecol, fontsize=9, ha='center')
        axL.set_xlim(-8, 8); axL.set_ylim(-2, 7.2)
        axL.set_aspect('equal'); axL.axis('off')
        axL.set_title(f"Schleppwinkel  ·  Richtwert {band_lo:.0f}–{band_hi:.0f}°",
                      fontsize=10, fontweight='bold')

        # ---------- rechts: Arbeitswinkel (Schnitt durch die Fuge) ----------
        axR.plot([-4.2, -0.7], [6, 0], color='#334155', lw=3)
        axR.plot([4.2, 0.7], [6, 0], color='#334155', lw=3)
        axR.plot([-0.7, 0.7], [0, 0], color='#334155', lw=3)
        axR.plot([-6, -4.2], [6, 6], color='#334155', lw=3)
        axR.plot([4.2, 6], [6, 6], color='#334155', lw=3)
        axR.add_patch(mpatches.Wedge((0, 0), R, 90 - 12, 90, facecolor='#bae6fd',
                                     alpha=0.5, edgecolor='none'))
        axR.plot([0, 0], [0, R], color='#94a3b8', lw=1, ls='--')
        axR.text(-2.4, 6.3, "mittig (Winkel-\nhalbierende)", fontsize=7, color='#94a3b8', ha='center')
        aw = math.radians(90 - work_deg)     # Neigung zur bereits geschweissten Seite (rechts)
        wx, wy = R * math.cos(aw), R * math.sin(aw)
        axR.plot([0, wx], [0, wy], color='#0ea5e9', lw=7, solid_capstyle='round', zorder=4)
        axR.add_patch(mpatches.Circle((0, 0), 0.18, color='#0ea5e9', zorder=5))
        axR.add_patch(mpatches.Arc((0, 0), 4.4, 4.4, angle=0, theta1=90 - work_deg,
                                   theta2=90, color='#0ea5e9', lw=1.6))
        axR.text(1.5, 3.3, f"{work_deg:.0f}°", color='#0ea5e9', fontsize=13, fontweight='bold')
        axR.text(5.0, 5.4, "bereits\ngeschweisst", fontsize=7, color='#64748b', ha='center')
        axR.set_xlim(-6.5, 6.5); axR.set_ylim(-1, 7.2)
        axR.set_aspect('equal'); axR.axis('off')
        axR.set_title("Arbeitswinkel  ·  Schnitt durch die Fuge", fontsize=10, fontweight='bold')

        plt.tight_layout()
        plt.close(fig)
        return fig

    @staticmethod
    def plot_bead_sequence(wt_mm=8.0, n_fill=1, included_deg=60.0, land_mm=1.6):
        """V-Naht mit Lagenaufbau: Wurzel, Heisslage, Fuelllagen, Decklage."""
        half = math.radians(included_deg / 2.0)

        def hw(y):
            return 0.9 + max(0.0, y - land_mm) * math.tan(half)

        top = wt_mm
        fig, ax = plt.subplots(figsize=(6.0, 5.2))
        ax.plot([-hw(top) - 12, -hw(top)], [top, top], color='#334155', lw=2.5)
        ax.plot([hw(top), hw(top) + 12], [top, top], color='#334155', lw=2.5)
        ax.plot([-hw(top), -0.9, 0.9, hw(top)], [top, land_mm, land_mm, top],
                color='#334155', lw=2.5)

        seq = [("Wurzel", "#dc2626", 0.0), ("Heisslage", "#f97316", land_mm + 1.0)]
        usable = max(1.4, wt_mm - (land_mm + 2.4) - 1.6)
        step = usable / max(1, n_fill)
        y = land_mm + 2.2 + step * 0.35
        for i in range(int(n_fill)):
            seq.append((f"Fuelllage {i + 1}", "#0ea5e9", y))
            y += step
        seq.append(("Decklage", "#16a34a", wt_mm - 0.2))

        label_x = hw(top) + 4
        for name, col, yc in seq:
            proud = 1.8 if name == "Decklage" else 0.0
            w = hw(max(yc, land_mm)) + (2.0 if name == "Decklage" else 0.6)
            ax.add_patch(mpatches.Ellipse((0, yc + 0.7 + proud * 0.3),
                                          2 * w, 2.2 + proud, facecolor=col,
                                          edgecolor='white', lw=1.0, alpha=0.92, zorder=3))
            ax.annotate(name, xy=(w, yc + 0.7), xytext=(label_x, yc + 0.7),
                        fontsize=9, color=col, va='center', fontweight='bold',
                        arrowprops=dict(arrowstyle='-', color=col, lw=0.9))

        ax.set_xlim(-hw(top) - 14, hw(top) + 16)
        ax.set_ylim(-1.6, wt_mm + 5)
        ax.set_aspect('equal', 'box')
        ax.axis('off')
        ax.set_title(f"Lagenaufbau  ·  Wand {wt_mm:.0f} mm  ·  {int(n_fill)} Fülllage(n)",
                     fontsize=11, fontweight='bold')
        plt.tight_layout()
        plt.close(fig)
        return fig

    @staticmethod
    def plot_travel_patterns():
        """Elektroden-Führungsmuster (Raupenformen) für die Fallnaht – schematisch.
        Laufrichtung = fallend (von oben nach unten)."""
        import numpy as np
        fig, axes = plt.subplots(2, 3, figsize=(10.5, 6.4))
        col = '#dc2626'
        y = np.linspace(0, 10, 400)

        def frame(ax, title):
            ax.plot([-1, -1], [-0.4, 10.4], color='#94a3b8', lw=1.4)   # Fugenkanten
            ax.plot([1, 1], [-0.4, 10.4], color='#94a3b8', lw=1.4)
            ax.annotate("", xy=(-1.9, 9.6), xytext=(-1.9, 0.4),
                        arrowprops=dict(arrowstyle='->', color='#0ea5e9', lw=1.6))
            ax.text(-2.4, 5, "fallend", rotation=90, va='center', fontsize=7, color='#0ea5e9')
            ax.set_xlim(-3, 3); ax.set_ylim(-0.6, 10.6)
            ax.invert_yaxis(); ax.set_aspect('equal'); ax.axis('off')
            ax.set_title(title, fontsize=10, fontweight='bold')

        # 1 Strichraupe
        ax = axes[0][0]; frame(ax, "Strichraupe (Drag)")
        ax.plot(np.zeros_like(y), y, color=col, lw=2.5)
        ax.annotate("", xy=(0, 10.2), xytext=(0, 9.4),
                    arrowprops=dict(arrowstyle='-|>', color=col, lw=2))

        # 2 Whip / Schritt
        ax = axes[0][1]; frame(ax, "Whip / Schritttechnik")
        yw = np.linspace(0, 10, 22)
        xw = np.where(np.arange(22) % 2, 0.0, 0.0)
        path_y, path_x = [], []
        cy = 0.0
        while cy < 10:
            path_y += [cy, cy - 0.7, cy + 0.9]      # ins Bad, vor (nach oben), zurück
            path_x += [0, 0, 0]
            cy += 0.9
        ax.plot([0]*len(path_y), path_y, color=col, lw=1.0, alpha=0.3)
        for k in range(0, len(path_y) - 2, 3):
            ax.annotate("", xy=(0, path_y[k+1]), xytext=(0, path_y[k]),
                        arrowprops=dict(arrowstyle='->', color=col, lw=1.6))
            ax.plot(0, path_y[k+2], 'o', color=col, ms=3)
        ax.text(1.4, 5, "vor – Pause –\nzurück ins Bad", fontsize=7, color='#475569', va='center')

        # 3 Halbmond / Sichel
        ax = axes[0][2]; frame(ax, "Halbmond (Sichel)")
        yy = np.linspace(0, 10, 400)
        xx = 0.75 * np.sin(yy * 2.6)
        ax.plot(xx, yy, color=col, lw=2.2)

        # 4 Zickzack
        ax = axes[1][0]; frame(ax, "Zickzack (seitlich)")
        yy = np.linspace(0, 10, 9)
        xx = np.tile([-0.8, 0.8], 5)[:9]
        ax.plot(xx, yy, color=col, lw=2.2)
        for x0 in (-0.8, 0.8):
            ax.plot([x0, x0], [0, 10], color=col, lw=0.6, ls=':', alpha=0.4)
        ax.text(1.3, 5, "an den Kanten\nkurz stehen", fontsize=7, color='#475569', va='center')

        # 5 Kringel / Kreis
        ax = axes[1][1]; frame(ax, "Kringel (Kreise)")
        t = np.linspace(0, 8 * 2 * np.pi, 600)
        ax.plot(0.7 * np.sin(t), t / (8 * 2 * np.pi) * 10 - 0.35 * np.cos(t) + 0.4,
                color=col, lw=1.8)

        # 6 J-Technik
        ax = axes[1][2]; frame(ax, "J-Technik (Deckl.)")
        cy = 0.3
        while cy < 9.3:
            jy = np.linspace(0, 1, 40)
            ax.plot(0.0 + 0.0 * jy, cy + jy * 1.1, color=col, lw=2)
            hook = np.linspace(0, np.pi, 30)
            ax.plot(-0.45 + 0.45 * np.cos(hook - np.pi/2),
                    cy + 1.1 + 0.45 * np.sin(hook - np.pi/2), color=col, lw=2)
            cy += 1.4

        plt.tight_layout()
        plt.close(fig)
        return fig

    # ------------------------------------------------ Phase 3: Geometrie ----
    @staticmethod
    def plot_template_curve(dev_s, dev_h, circ, title="Abwicklung / Schablone"):
        """Einfache Schablonen-Kurve: Abtrag h über Umfangsmaß s."""
        fig, ax = plt.subplots(figsize=(7.4, 3.2))
        h_top = max(dev_h) * 1.15 if max(dev_h) > 0 else 1.0
        ax.plot(dev_s, dev_h, color='#dc2626', lw=2)
        ax.fill_between(dev_s, dev_h, h_top, color='#fee2e2', alpha=0.7)
        ax.set_xlim(0, circ)
        ax.set_ylim(h_top, 0)
        ax.set_xlabel("Umfangsmaß s ab Anreißlinie [mm]")
        ax.set_ylabel("Abtrag h [mm]")
        ax.set_title(title, fontsize=10, fontweight='bold')
        ax.grid(True, linestyle='--', alpha=0.4)
        plt.tight_layout()
        plt.close(fig)
        return fig

    @staticmethod
    def plot_cone_sector(r_out, r_in, sector_deg):
        """Abwicklung konzentrische Reduzierung als Kreisringsektor."""
        fig, ax = plt.subplots(figsize=(5.6, 5.0))
        t = [math.radians(sector_deg) * k / 120 for k in range(121)]
        ax.plot([r_out * math.cos(x) for x in t], [r_out * math.sin(x) for x in t],
                color='#0ea5e9', lw=2)
        ax.plot([r_in * math.cos(x) for x in t], [r_in * math.sin(x) for x in t],
                color='#0ea5e9', lw=2)
        for x in (t[0], t[-1]):
            ax.plot([r_in * math.cos(x), r_out * math.cos(x)],
                    [r_in * math.sin(x), r_out * math.sin(x)], color='#334155', lw=1.6)
        ax.fill(
            [r_out * math.cos(x) for x in t] + [r_in * math.cos(x) for x in reversed(t)],
            [r_out * math.sin(x) for x in t] + [r_in * math.sin(x) for x in reversed(t)],
            color='#e0f2fe', alpha=0.6)
        ax.text(r_out * math.cos(math.radians(sector_deg / 2)) * 1.05,
                r_out * math.sin(math.radians(sector_deg / 2)) * 1.05,
                f"{sector_deg:.1f}°", fontsize=11, fontweight='bold', color='#0f172a')
        ax.set_aspect('equal', 'box')
        ax.axis('off')
        ax.set_title("Abwicklung – konzentrische Reduzierung", fontsize=10, fontweight='bold')
        plt.tight_layout()
        plt.close(fig)
        return fig

    @staticmethod
    def plot_expansion_loop(shape, leg_mm):
        """Schema L- / Z- / U-Bogen mit Schenkellänge."""
        fig, ax = plt.subplots(figsize=(6.4, 3.4))
        Lg = 1.0
        if shape.startswith("L"):
            xs, ys = [0, 3, 3], [0, 0, Lg]
            ax.annotate(f"{leg_mm:.0f} mm", xy=(3.15, Lg / 2), fontsize=10, color='#dc2626')
        elif shape.startswith("Z"):
            xs, ys = [0, 2, 2, 4, 4, 6], [0, 0, Lg, Lg, 0, 0]
            ax.annotate(f"{leg_mm:.0f} mm", xy=(2.15, Lg / 2), fontsize=10, color='#dc2626')
        else:  # U
            xs, ys = [0, 2, 2, 4, 4, 6], [0, 0, Lg, Lg, 0, 0]
            xs = [0, 2.5, 2.5, 3.5, 3.5, 6]
            ax.annotate(f"{leg_mm:.0f} mm", xy=(2.65, Lg / 2), fontsize=10, color='#dc2626')
        ax.plot(xs, ys, color='#334155', lw=4, solid_capstyle='round')
        ax.plot([xs[0]], [ys[0]], 'o', color='#1e3a8a')
        ax.plot([xs[-1]], [ys[-1]], 'o', color='#1e3a8a')
        ax.text(xs[0], -0.25, "Festpunkt", fontsize=8, ha='center', color='#64748b')
        ax.text(xs[-1], -0.25, "Festpunkt", fontsize=8, ha='center', color='#64748b')
        ax.set_xlim(-0.6, 6.6); ax.set_ylim(-0.6, Lg + 0.6)
        ax.set_aspect('equal', 'box'); ax.axis('off')
        ax.set_title(f"{shape} – Prinzipskizze", fontsize=10, fontweight='bold')
        plt.tight_layout()
        plt.close(fig)
        return fig


class Exporter:
    @staticmethod
    def clean_text_for_pdf(text: str) -> str:
        if not isinstance(text, str): return str(text)
        replacements = {
            "€": "EUR", "–": "-", "—": "-", "„": '"', "“": '"', "”": '"', "’": "'", "‘": "'"
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        return text

    @staticmethod
    def to_excel(df):
        output = BytesIO()
        export_df = df.drop(columns=['✏️', 'Löschen', 'id', 'Auswahl', 'project_id', 'dn_clean', 'charge'], errors='ignore')
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            export_df.to_excel(writer, index=False, sheet_name='Daten')
        return output.getvalue()

    @staticmethod
    def to_pdf_report(title: str, inputs: dict, results: dict, note: str = "") -> bytes:
        """Generischer Ergebnis-Ausdruck fuer einen Rechner: Titel, Eingabe- und
        Ergebnistabelle, Hinweis, Datum. Gibt leere Bytes zurueck, wenn fpdf fehlt."""
        if not PDF_AVAILABLE:
            return b""
        C = Exporter.clean_text_for_pdf
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.add_page()
        pdf.set_font("Arial", 'B', 15)
        pdf.cell(0, 10, C(title), 0, 1, 'L')
        pdf.set_font("Arial", 'I', 9)
        pdf.cell(0, 6, C(f"PipeCraft - erstellt {datetime.now().strftime('%d.%m.%Y %H:%M')}"), 0, 1, 'L')
        pdf.ln(4)

        def table(head, data):
            pdf.set_font("Arial", 'B', 11)
            pdf.set_fill_color(225, 232, 240)
            pdf.cell(0, 8, C(head), 1, 1, 'L', fill=True)
            pdf.set_font("Arial", '', 10)
            for k, v in data.items():
                pdf.cell(75, 7, C(str(k)), 1)
                pdf.cell(0, 7, C(str(v)), 1, 1)
            pdf.ln(4)

        if inputs:
            table("Eingaben", inputs)
        if results:
            table("Ergebnis", results)
        if note:
            pdf.set_font("Arial", 'I', 9)
            pdf.multi_cell(0, 5, C(note))
        pdf.ln(6)
        pdf.set_font("Arial", '', 8)
        pdf.multi_cell(0, 5, C("Richtwerte - verbindlich sind die freigegebene WPS, "
                               "die einschlaegige Norm und die Projektspezifikation."))
        out = pdf.output(dest='S')
        return bytes(out) if isinstance(out, (bytes, bytearray)) else out.encode('latin-1')
