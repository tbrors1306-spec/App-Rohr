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

    # ------------------------------------------- Rohrfolge-Skizze ----------
    _C30 = math.cos(math.radians(30))
    _S30 = math.sin(math.radians(30))
    # Bauteile mit eigener Bemassung (kurze Teile werden nur bemasst, wenn
    # der Nutzer sie eingegeben hat)
    # Echte Masslinie nur fuer das, was gesaegt wird. Alle anderen Bauteile
    # bekommen ein schlichtes Label "Nr - Mass" am Symbol; das haelt die
    # Zeichnung ruhig und der Flansch hat trotzdem seine Zahl.
    _DIM_PARTS = ("Rohr",)
    # Flansche werden mit dem Rohr zusammen bemasst - sie sind daran geschweisst
    _FLANSCHE = ("Vorschweissflansch", "Blindflansch")
    # Bauteile, deren Symbol Platz laengs des Rohres braucht
    _SYMBOL_PARTS = ("Armatur geschweisst", "Armatur mit Flanschen",
                     "Klappe", "Demontagestueck",
                     "Vorschweissflansch", "Blindflansch", "T-Stueck",
                     "Reduzierung", "Montagestoss")

    @staticmethod
    def _iso(p):
        x, y, z = p
        return ((x - y) * Visualizer._C30, (x + y) * Visualizer._S30 + z)

    # Ansichten: eine Zeichnung kann nicht alles gleichzeitig zeigen. Je Modus
    # sind nur die zwei bis drei Beschriftungsarten drauf, die dieser Job
    # braucht - sonst erschlaegt sich alles gegenseitig.
    MODI = ["Aufmass & Saegen", "Schweissen", "Montage", "Alles"]

    @staticmethod
    def plot_spool(spool, title="", massstab=False, naht_nr=False, ballons=False,
                   ax=None, modus="Aufmass & Saegen", masse=True):
        """Bauteilkette als Iso-Skizze.

        Standardmaessig NICHT massstaeblich: die Zeichenlaengen werden
        gestaucht (L**0.32), damit kurze Teile sichtbar bleiben und lange
        Laeufe die Zeichnung nicht erdruecken - genau wie bei einer echten
        Rohrleitungsisometrie. Die wahren Masse stehen an den Masslinien.
        """
        iso = Visualizer._iso
        segs = spool["segments"]

        # ---- Zeichenlaengen bestimmen --------------------------------------
        real = [max(s["len"], 0.0) for s in segs] + \
               [b["arm"] + b["pipe"] + b["end_len"] for b in spool.get("branches", [])]
        real_pos = [v for v in real if v > 0]
        ref = max(real_pos) if real_pos else 1.0

        def dl(L, part=None):
            """Zeichenlaenge: gestaucht, mit sichtbarem Mindestmass.

            Bauteile mit einem echten Symbol (Armatur, Flansch, T-Stueck ...)
            brauchen mehr Platz als ein kurzes Rohrstueck - sonst wird das
            Symbol auf die Bauteillaenge gestaucht und ein Schieber sieht aus
            wie ein Punkt.
            """
            if L <= 0:
                return 0.0
            if massstab:
                return L / ref
            # Gestaucht, nicht linear: ein 50er Flansch neben einem 2,5-m-Rohr
            # bekommt so 17 % statt 2 % der Laenge und sein Symbol hat Platz.
            # Genau das macht eine echte Isometrie auch - die wahren Masse
            # stehen an den Masslinien, nicht in der Strichlaenge.
            # KEIN Aufschlag je Abschnitt - sonst wird ein Abzweig aus drei
            # Teilen laenger gezeichnet als ein laengeres Rohr.
            return max(0.05, (L / ref) ** 0.45)

        # Ein Flansch am Kettenende bekommt **keine Zeichenlaenge**. Sonst
        # steht dort ein schwarzer Rohrstummel mit einem roten Strich an der
        # Spitze - und das Rohrmass, das den Flansch mitzaehlt, endet ein
        # Stueck vor dem gezeichneten Ende. Mit Laenge 0 sitzt das rote
        # Flanschblatt genau am Rohrende und das Mass hoert dort auf, wo die
        # Linie aufhoert. Die wahre Laenge bleibt unveraendert - sie steht in
        # der Zahl, nicht im Strich.
        flach = set()
        for reihe in (range(len(segs)), range(len(segs) - 1, -1, -1)):
            for i in reihe:
                if segs[i].get("part") not in Visualizer._FLANSCHE:
                    break
                flach.add(i)

        # ---- Kette ablaufen: wahre Lage (mm) + Zeichenlage -----------------
        pt = (0.0, 0.0, 0.0)          # wahre Lage in mm
        pd_ = (0.0, 0.0, 0.0)         # Zeichenlage
        laid = []                     # je Segment: Zeichen-Start/-Ende + Info
        for i, s in enumerate(segs):
            d = s["d"]
            L = s["len"]
            nxt = tuple(pt[k] + d[k] * L for k in range(3))
            dL = 0.0 if i in flach else dl(L, s.get("part"))
            nxd = tuple(pd_[k] + d[k] * dL for k in range(3))
            laid.append({"a": pd_, "b": nxd, "a_true": pt, "b_true": nxt, **s})
            pt, pd_ = nxt, nxd

        # ---- Abzweige ------------------------------------------------------
        blaid = []
        for b in spool.get("branches", []):
            host = laid[b["seg"]]
            tt = b.get("t", 0.5)
            base = tuple(host["a"][k] + (host["b"][k] - host["a"][k]) * tt
                         for k in range(3))
            d = b["d"]
            # Abzweig in drei Abschnitte teilen: T-/Stutzen-Arm, Rohrstueck,
            # Endbauteil. Bemasst wird spaeter nur das Rohrstueck - sonst
            # sieht ein kurzes Rohr laenger aus, als die Zahl daneben sagt.
            la, lp = dl(b["arm"]), dl(b["pipe"])
            # Wie in der Hauptkette: ein Flansch am Abzweigende bekommt keine
            # Zeichenlaenge, sonst steht dort ein Rohrstummel mit rotem Strich
            # an der Spitze und das Abzweigmass endet davor.
            le = (0.0 if b["end"] in Visualizer._FLANSCHE
                  else dl(b["end_len"], b["end"]))
            # Die drei Abschnitte zusammen auf die Zeichenlaenge bringen, die
            # dem Gesamtmass zusteht - sonst wirkt ein kurzer Abzweig aus drei
            # Teilen laenger als ein laengeres Rohr aus einem Stueck.
            ziel = dl(b["arm"] + b["pipe"] + b["end_len"])
            if la + lp + le > 1e-9:
                sk = ziel / (la + lp + le)
                la, lp, le = la * sk, lp * sk, le * sk
            p1 = tuple(base[k] + d[k] * la for k in range(3))
            p2 = tuple(p1[k] + d[k] * lp for k in range(3))
            p3 = tuple(p2[k] + d[k] * le for k in range(3))
            blaid.append({"a": base, "b": p3, "rohr_a": p1, "rohr_b": p2,
                          "pos": b.get("pos"),
                          "len": b["arm"] + b["pipe"] + b["end_len"], **b})

        # ---- Bildausschnitt -------------------------------------------------
        # Nicht nur die Endpunkte: eine Masslinie soll auch das freiraeumen,
        # was quer durch ihre Bahn laeuft, ohne dort anzufangen oder zu enden.
        allp = []
        for A, B in ([(l["a"], l["b"]) for l in laid]
                     + [(b_["a"], b_["b"]) for b_ in blaid]):
            for k in range(9):
                f = k / 8.0
                allp.append(iso(tuple(A[j] + (B[j] - A[j]) * f
                                      for j in range(3))))
        xs = [p[0] for p in allp]
        ys = [p[1] for p in allp]
        bw = max(1e-6, max(xs) - min(xs))
        bh = max(1e-6, max(ys) - min(ys))
        span = max(bw, bh)
        ar = min(1.35, max(0.62, (bh + span * 0.30) / (bw + span * 0.30)))
        if ax is None:
            fig, ax = plt.subplots(figsize=(7.8, 7.8 * ar))
            eigen = True
        else:                       # in ein vorhandenes Blatt zeichnen
            fig, eigen = ax.figure, False

        off = span * 0.055          # Masslinien-Abstand
        sym = span * 0.021          # Symbolgroesse
        Visualizer._TEXT_SKALA = 1.0

        # ---- Rohrlinie ------------------------------------------------------
        for l in laid:
            a, b = iso(l["a"]), iso(l["b"])
            if math.hypot(b[0] - a[0], b[1] - a[1]) < 1e-9:
                continue          # Flansch am Kettenende: nur das rote Blatt
            ax.plot([a[0], b[0]], [a[1], b[1]], color='#1e293b', lw=3.2,
                    solid_capstyle='round', zorder=3)
        for b in blaid:
            a, e = iso(b["a"]), iso(b["b"])
            ax.plot([a[0], e[0]], [a[1], e[1]], color='#334155', lw=2.4,
                    solid_capstyle='round', zorder=2)

        # ---- Bauteile: Symbole + Bemassung ----------------------------------
        # Segmente eines Bauteils zusammenfassen (Bogen hat zwei)
        by_row = {}
        for l in laid:
            by_row.setdefault(l["row"], []).append(l)
        belegt = []       # Rechtecke aller gesetzten Beschriftungen
        # Die Kompassrose wird zwar zuletzt gezeichnet, ihre Lage steht aber
        # schon fest - vorab anmelden, sonst landet ein Mass auf dem "S".
        _cx, _cy, _rad = (min(xs) - span * 0.13, max(ys) + span * 0.13,
                          span * 0.070)
        for _v in ((0, 1, 0), (1, 0, 0), (0, -1, 0), (-1, 0, 0)):
            _q = iso(_v)
            belegt.append(Visualizer._txt_rect(
                (_cx + _q[0] * _rad * 1.42, _cy + _q[1] * _rad * 1.42),
                "W", 9.5, span))
        belegt.append(Visualizer._txt_rect((_cx, _cy + _rad * 1.15), "oben",
                                           7.5, span))
        # Schon gezogene Masslinien samt Hilfslinien. Zwei sich kreuzende
        # Masse liest niemand - jede neue weicht ihnen aus.
        mlinien = []
        dn_zuletzt = [None]   # DN nur beschriften, wo sie wechselt
        alles = modus == "Alles"
        # Bauteilnummern und Bemassung gehoeren beide zur Aufmass-Ansicht, sind
        # aber zwei Paar Schuhe: masse=False nimmt nur die Masslinien raus, die
        # Nummern bleiben - sonst steht auf dem Blatt nichts mehr, woran man
        # ein Teil festmachen kann.
        z_nummer = alles or modus == "Aufmass & Saegen"
        z_mass = masse and z_nummer
        z_naht = alles or modus == "Schweissen"
        z_mont = alles or modus == "Montage"
        # Jedes Rohr bekommt sein eigenes Mass - und zwar zuerst, damit die
        # Einzelmasse den Platz dicht am Rohr bekommen. Ein angeschweisster
        # Flansch gehoert dabei zum Rohrstueck: das Mass laeuft bis zur
        # Flanschflaeche, sonst bleibt zwischen Massende und Rohrende ein
        # ungemessenes Stueck stehen. Jeder Flansch zaehlt nur einmal - sitzt
        # er zwischen zwei Rohren, bekommt ihn das erste.
        if z_mass:
            vergeben = set()
            for k, l in enumerate(laid):
                if l["part"] != "Rohr" or l["len"] <= 1.0:
                    continue
                von, bis, L = k, k, l["len"]
                for nachbar in (k - 1, k + 1):
                    if not 0 <= nachbar < len(laid) or nachbar in vergeben:
                        continue
                    n = laid[nachbar]
                    if n["part"] in Visualizer._FLANSCHE and n["d"] == l["d"]:
                        vergeben.add(nachbar)
                        L += n["len"]
                        von, bis = min(von, nachbar), max(bis, nachbar)
                Visualizer._mass_linie(ax, iso(laid[von]["a"]),
                                       iso(laid[bis]["b"]), "%.0f" % L, span,
                                       belegt, linien=mlinien)

        # Gesamtmasse ueber einen ganzen Lauf gibt es **nicht** mehr: die
        # Summe der Einzelmasse rechnet sich jeder selbst aus, und auf dem
        # Blatt hat sie nur Platz weggenommen. Eine Ausnahme bleibt: ein Lauf
        # ganz ohne Rohr (nur Formteile aneinander) waere sonst voellig
        # unbemasst - den kann man dann nicht bauen.
        if z_mass:
            i0 = 0
            while i0 < len(laid):
                j0 = i0
                while j0 + 1 < len(laid) and laid[j0 + 1]["d"] == laid[i0]["d"]:
                    j0 += 1
                lauf_teile = [laid[k]["part"] for k in range(i0, j0 + 1)]
                at, bt = laid[i0]["a_true"], laid[j0]["b_true"]
                L = math.sqrt(sum((bt[k] - at[k]) ** 2 for k in range(3)))
                # Nur der rohrlose Lauf bekommt eines. Die Versprung-
                # Schraege nie: dort sind Hoehe, Seite und Lauf einzeln
                # bemasst.
                n_rohr = sum(1 for k in range(i0, j0 + 1)
                             if laid[k]["part"] == "Rohr")
                if (L > 1.0 and n_rohr == 0
                        and set(lauf_teile) != {"Versprung"}):
                    Visualizer._mass_linie(
                        ax, iso(laid[i0]["a"]), iso(laid[j0]["b"]),
                        "%.0f" % L, span, belegt, linien=mlinien)
                i0 = j0 + 1

        # Auch die Abzweigmasse vor die Bauteilnummern: ein Mass je Abzweig,
        # von der Rohrachse bis zum Ende - das Mass, das man am Rohr abgreift.
        if z_mass:
            for b_ in blaid:
                Visualizer._mass_linie(
                    ax, iso(b_["a"]), iso(b_["b"]),
                    "DN%d  %.0f" % (b_["dn"], b_["arm"] + b_["pipe"]
                                         + b_["end_len"]),
                    span, belegt, linien=mlinien)
            # Anrissmasse: wo genau sitzen die Stutzen auf ihrem Rohr?
            # Nicht als Einzelmasse - die stehen bei mehreren Stutzen
            # uebereinander und man sieht nicht mehr, welches wohin gehoert.
            # Stattdessen alle Messpunkte eines Rohres gemeinsam.
            je_rohr = {}
            for b_ in blaid:
                if b_.get("anriss") is not None:
                    je_rohr.setdefault(b_["seg"], []).append(b_)
            for seg_i, bs in je_rohr.items():
                rohr = laid[seg_i]
                bs.sort(key=lambda q: q["anriss"])
                pts = ([iso(rohr["a"])] + [iso(q["a"]) for q in bs]
                       + [iso(rohr["b"])])
                marken = [0.0] + [q["anriss"] for q in bs] + [rohr["len"]]
                texte = ["%.0f" % (marken[k + 1] - marken[k])
                         for k in range(len(marken) - 1)]
                Visualizer._kettenmass(ax, pts, texte, span, belegt,
                                       linien=mlinien)

        for it in spool["items"]:
            ls = by_row.get(it["row"])
            if not ls:
                continue
            a, b = iso(ls[0]["a"]), iso(ls[-1]["b"])
            dx, dy = b[0] - a[0], b[1] - a[1]
            n = math.hypot(dx, dy)
            if n < 1e-9:
                # Flansch am Kettenende: keine Zeichenlaenge, also auch keine
                # Richtung aus a->b. Die kommt dann aus der Bauteilachse,
                # sonst zeigt das Flanschblatt nirgendwohin und verschwindet.
                d3 = ls[0]["d"]
                q3 = iso(tuple(ls[0]["a"][k] + d3[k] * 1000.0
                               for k in range(3)))
                dx, dy = q3[0] - a[0], q3[1] - a[1]
            nn = math.hypot(dx, dy) or 1.0
            u = (dx / nn, dy / nn)
            p = (-u[1], u[0])
            # Beim Bogen liegt der Eckpunkt zwischen a und b - die Nummer
            # gehoert dorthin, nicht auf die Diagonale quer durch die Ecke.
            mid = (iso(ls[0]["b"]) if it["turn"]
                   else ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0))
            # Symbol darf schrumpfen, aber nicht unter zwei Drittel - darunter
            # erkennt man einen Schieber nicht mehr von einem Punkt.
            s_it = (sym if n < 1e-9
                    else max(sym * 0.55, min(sym, 0.40 * n)))
            Visualizer._part_symbol(ax, it["part"], a, b, mid, u, p, s_it, it["ends"])
            # Das Symbol belegt Flaeche: sonst landet eine Masszahl mitten in
            # einer Armatur, weil dort ja "kein Text" steht.
            belegt.append((mid[0] - s_it, mid[1] - s_it,
                           mid[0] + s_it, mid[1] + s_it))
            if it["part"] == "Versprung" and z_nummer:
                if z_mass:
                    segs_v = by_row[it["row"]]
                    Visualizer._versprung_bau(
                        ax, iso, segs_v[1] if len(segs_v) > 2 else segs_v[0],
                        segs_v[0]["d"], it["vers"], span, belegt, mlinien, off)
                Visualizer._label_frei(
                    ax, mid, p, off * 0.75,
                    "%d  Versprung %g°" % (it["row"], it["vers"]["winkel"]),
                    belegt, span)
            elif (it["part"] in Visualizer._DIM_PARTS and z_naht
                    and it["dn"] != dn_zuletzt[0]):
                dn_zuletzt[0] = it["dn"]
                Visualizer._label_frei(ax, mid, p, off * 0.75,
                                       "DN%d" % it["dn"], belegt, span)
            elif z_nummer:
                Visualizer._label_frei(ax, mid, p, off * 0.75,
                                       Visualizer._teil_label(it), belegt, span)
        # Flanschflaechen genau dort zeichnen, wo auch gezaehlt wird: am Stoss.
        # Ein Flanschstoss = zwei Flanschblaetter, ein freies F-Ende = eines.
        rows_in_order = [it["row"] for it in spool["items"]]
        for k, jt in enumerate(spool["joints"]):
            if jt != "flansch":
                continue
            ls = by_row.get(rows_in_order[k])
            if not ls:
                continue
            q = iso(ls[-1]["b"])
            nb = by_row.get(rows_in_order[k + 1])
            ref = iso(nb[-1]["b"]) if nb else iso(ls[0]["a"])
            dx, dy = ref[0] - q[0], ref[1] - q[1]
            n = math.hypot(dx, dy) or 1.0
            uu, pp = (dx / n, dy / n), (-dy / n, dx / n)
            l_prev = math.hypot(iso(ls[-1]["b"])[0] - iso(ls[0]["a"])[0],
                                iso(ls[-1]["b"])[1] - iso(ls[0]["a"])[1])
            l_next = math.hypot(iso(nb[-1]["b"])[0] - iso(nb[0]["a"])[0],
                                iso(nb[-1]["b"])[1] - iso(nb[0]["a"])[1]) if nb else l_prev
            s_j = max(sym * 0.66, min(sym, 0.30 * min(l_prev, l_next)))
            for k2 in (-0.40, 0.40):
                Visualizer._flange_bar(ax, q, uu, pp, s_j, k2)
        for pos_iso, uu, pp in Visualizer._free_flange_ends(spool, by_row, iso):
            Visualizer._flange_bar(ax, pos_iso, uu, pp, sym, 0.0)

        for b in blaid:
            a, e = iso(b["a"]), iso(b["b"])
            mk = 's' if b["art"] == "Fertig-T" else 'D'
            ax.plot(a[0], a[1], mk, color='#b91c1c', ms=7, zorder=6)
            # Endbauteil des Abzweigs zeichnen (fehlte bisher komplett)
            dx, dy = e[0] - a[0], e[1] - a[1]
            nb_ = math.hypot(dx, dy) or 1.0
            uu, pp = (dx / nb_, dy / nb_), (-dy / nb_, dx / nb_)
            s_b = max(sym * 0.66, min(sym, 0.30 * nb_))
            if b["end"] == "Vorschweissflansch":
                Visualizer._flange_bar(ax, e, uu, pp, s_b, 0.0)
            elif b["end"] == "Blindflansch":
                Visualizer._flange_bar(ax, e, uu, pp, s_b, -0.5)
                Visualizer._flange_bar(ax, e, uu, pp, s_b, 0.2, half=0.7, lw=4.0)
            elif b["end"] == "Anschluss geschweisst":
                Visualizer._flange_bar(ax, e, uu, pp, s_b, 0.0, half=1.4, lw=4.0)
            else:                                    # offenes Ende
                ax.plot(e[0], e[1], 'o', mfc='white', mec='#64748b', mew=1.5,
                        ms=6, zorder=6)

        # ---- Positionsballons ------------------------------------------------
        # Kreis mit der Positionsnummer aus der Stueckliste, per Fahne am
        # Bauteil - wie auf einer Fertigungsiso.
        if ballons and z_mont:
            ziele = []
            for it in spool["items"]:
                if not it.get("pos"):
                    continue
                ls = by_row.get(it["row"])
                if not ls:
                    continue
                q = (iso(ls[0]["b"]) if it["turn"] else
                     tuple((iso(ls[0]["a"])[k] + iso(ls[-1]["b"])[k]) / 2.0
                           for k in range(2)))
                ziele.append((q, it["pos"]))
            for b in blaid:
                if b.get("pos"):
                    ra, rb = iso(b["rohr_a"]), iso(b["rohr_b"])
                    ziele.append((((ra[0] + rb[0]) / 2.0, (ra[1] + rb[1]) / 2.0),
                                  b["pos"]))
            rb_ = span * 0.030
            richt = [(math.cos(math.radians(a_)), math.sin(math.radians(a_)))
                     for a_ in (135, 45, 225, 315, 90, 270, 180, 0,
                                112, 68, 202, 338)]
            for q, nr in ziele:
                # Der Ballon ist ein Kreis - als Text so breit wie sein
                # Durchmesser, damit die Flaechenpruefung stimmt.
                kand = Visualizer._platz(q, "OO", 8.0, span, belegt, richt,
                                         (0.062, 0.085, 0.110))
                dx, dy = q[0] - kand[0], q[1] - kand[1]
                nn = math.hypot(dx, dy) or 1.0
                ax.plot([kand[0] + dx / nn * rb_, q[0]],
                        [kand[1] + dy / nn * rb_, q[1]],
                        color='#7c3aed', lw=0.9, zorder=9)
                ax.add_patch(mpatches.Circle(kand, rb_, fc='white', ec='#7c3aed',
                                    lw=1.3, zorder=10))
                ax.text(kand[0], kand[1], str(nr), ha='center', va='center',
                        fontsize=7.2, color='#7c3aed', fontweight='bold', zorder=11)

        # ---- Naehte ---------------------------------------------------------
        # Werkstattnaht: gefuellter Punkt. Baustellennaht: Kreis mit Kreuz -
        # die auf der Baustelle geschweisste Naht muss sofort auffallen.
        naht_pos = []
        for n in (spool.get("nahtliste", []) if z_naht else []):
            art, idx, wert = n.get("anker", ("seg", n["seg"], n["t"]))
            if art == "seg":
                if not (0 <= idx < len(laid)):
                    continue
                l = laid[idx]
                q3 = tuple(l["a"][k] + (l["b"][k] - l["a"][k]) * wert
                           for k in range(3))
            else:                                   # Abzweig, mm ab Wurzel
                if not (0 <= idx < len(blaid)):
                    continue
                b = blaid[idx]
                rest, ecken = float(wert), ((b["a"], b["rohr_a"], b["arm"]),
                                            (b["rohr_a"], b["rohr_b"], b["pipe"]),
                                            (b["rohr_b"], b["b"], b["end_len"]))
                q3 = b["b"]
                for va, ve, ln in ecken:
                    if rest <= ln or ln <= 0:
                        f = (rest / ln) if ln > 0 else 0.0
                        q3 = tuple(va[k] + (ve[k] - va[k]) * max(0.0, min(1.0, f))
                                   for k in range(3))
                        break
                    rest -= ln
            naht_pos.append((iso(q3), n))
        for q, n in naht_pos:
            if n["art"] == "Flanschverbindung":
                continue                            # hat schon Flanschblaetter
            if n["feld"]:
                ax.plot(q[0], q[1], 'o', mfc='white', mec='#b91c1c', mew=1.7,
                        ms=8.0, zorder=8)
                ax.plot(q[0], q[1], 'x', color='#b91c1c', mew=1.7, ms=5.0,
                        zorder=9)
            else:
                ax.plot(q[0], q[1], 'o', color='#0f172a', ms=4.6, zorder=8)
        if naht_nr and z_naht:
            # Nummern mit Abstand und Fuehrungslinie - direkt am Rohr kleben sie
            # auf der Rohrlinie und man liest sie nicht mehr.
            richt = [(math.cos(math.radians(g)), math.sin(math.radians(g)))
                     for g in (60, 120, -60, -120, 90, -90, 20, 160, -20, -160)]
            for q, n in naht_pos:
                kand = Visualizer._platz(q, n["nr"], 6.8, span, belegt, richt,
                                         (0.055, 0.078, 0.102))
                farbe = '#b91c1c' if n["feld"] else '#0f172a'
                dx, dy = kand[0] - q[0], kand[1] - q[1]
                nn = math.hypot(dx, dy) or 1.0
                ax.plot([q[0] + dx / nn * span * 0.012,
                         kand[0] - dx / nn * span * 0.016],
                        [q[1] + dy / nn * span * 0.012,
                         kand[1] - dy / nn * span * 0.016],
                        color=farbe, lw=0.6, alpha=0.55, zorder=8)
                ax.annotate(n["nr"], kand, ha='center', va='center', fontsize=6.8,
                            color=farbe, fontweight='bold', zorder=9,
                            bbox=dict(boxstyle='round,pad=0.12', fc='white',
                                      ec='none', alpha=0.85))

        # ---- Kompassrose ----------------------------------------------------
        cx = min(xs) - span * 0.13
        cy = max(ys) + span * 0.13
        rad = span * 0.070
        for name, v in (("N", (0, 1, 0)), ("O", (1, 0, 0)),
                        ("S", (0, -1, 0)), ("W", (-1, 0, 0))):
            q = iso(v)
            tip = (cx + q[0] * rad, cy + q[1] * rad)
            ax.plot([cx, tip[0]], [cy, tip[1]], color='#64748b', lw=1.4,
                    solid_capstyle='round', zorder=7, clip_on=False)
            ax.plot(tip[0], tip[1], marker=(3, 0, math.degrees(math.atan2(q[1], q[0])) - 90),
                    color='#64748b', ms=6, zorder=7, clip_on=False)
            ax.text(cx + q[0] * rad * 1.42, cy + q[1] * rad * 1.42, name,
                    ha='center', va='center', fontsize=9.5, fontweight='bold',
                    color='#334155', zorder=7, clip_on=False)
        ax.plot([cx, cx], [cy, cy + rad * 0.85], color='#94a3b8', lw=1.1,
                zorder=7, clip_on=False)
        ax.plot(cx, cy + rad * 0.85, marker=(3, 0, 0), color='#94a3b8', ms=5,
                zorder=7, clip_on=False)
        # ueber die Spitze des Hochpfeils - links sitzt N, rechts O
        ax.text(cx, cy + rad * 1.02, "oben", ha='center', va='bottom',
                fontsize=7.5, color='#94a3b8', zorder=7, clip_on=False)

        ax.set_aspect('equal', 'box')
        ax.axis('off')
        ax.margins(0.13)
        if title:
            ax.set_title(title, fontsize=10, fontweight='bold', pad=8)
        if not massstab:
            ax.text(0.99, 0.01, "nicht massstaeblich", transform=ax.transAxes,
                    ha='right', va='bottom', fontsize=7.5, color='#94a3b8')
        if eigen:
            plt.tight_layout()
            plt.close(fig)
        return fig

    # Blattbreite in Zoll (A3 quer) - wird gebraucht, um zu schaetzen, wie
    # viele Zeichen in eine Tabellenspalte passen.
    _A3_B, _A3_H = 16.54, 11.69

    @staticmethod
    def _kurz(text, breite_anteil, fs):
        """Text auf die Spaltenbreite kuerzen - sonst laeuft er in die Nachbarspalte."""
        s = "" if text is None else str(text)
        platz = breite_anteil * Visualizer._A3_B * 72.0
        n = max(3, int(platz / (fs * 0.56)) - 1)
        return s if len(s) <= n else s[:n - 1] + "…"

    @staticmethod
    def _blatt_tabelle(ax, x, y, breite, spalten, zeilen, titel=None,
                       kopf_h=0.026, zeil_h=0.019, fs=5.6):
        """Tabelle in Blattkoordinaten (0..1). Gibt die Unterkante zurueck."""
        if titel:
            ax.text(x, y + 0.006, titel, fontsize=7.0, fontweight='bold',
                    color='#0f172a', va='bottom', ha='left')
        # Spalte = (Anzeige, Anteil) oder (Anzeige, Anteil, Schluessel im Datensatz)
        spalten = [(c[0], c[1], c[2] if len(c) > 2 else c[0]) for c in spalten]
        anteile = [c[1] for c in spalten]
        summe = sum(anteile) or 1.0
        kanten, acc = [x], x
        for a in anteile:
            acc += breite * a / summe
            kanten.append(acc)
        oben = y
        ax.add_patch(mpatches.Rectangle((x, oben - kopf_h), breite, kopf_h,
                                        fc='#e2e8f0', ec='#334155', lw=0.7))
        for i, (name, a, _k) in enumerate(spalten):
            ax.text(kanten[i] + 0.003, oben - kopf_h / 2.0,
                    Visualizer._kurz(name, breite * a / summe, fs),
                    fontsize=fs, fontweight='bold', va='center', ha='left',
                    color='#0f172a')
        yy = oben - kopf_h
        for r, zeile in enumerate(zeilen):
            ax.add_patch(mpatches.Rectangle((x, yy - zeil_h), breite, zeil_h,
                                            fc='white' if r % 2 else '#f8fafc',
                                            ec='#cbd5e1', lw=0.4))
            for i, (_name, a, k) in enumerate(spalten):
                ax.text(kanten[i] + 0.003, yy - zeil_h / 2.0,
                        Visualizer._kurz(zeile.get(k, ""), breite * a / summe, fs),
                        fontsize=fs, va='center', ha='left', color='#1e293b')
            yy -= zeil_h
        ax.add_patch(mpatches.Rectangle((x, yy), breite, oben - yy, fc='none',
                                        ec='#334155', lw=0.9))
        for k in kanten[1:-1]:
            ax.plot([k, k], [yy, oben], color='#334155', lw=0.5)
        return yy

    @staticmethod
    def plot_iso_blatt(spool, kopf=None, massstab=False, naht_nr=True,
                       ballons=True, modus="Alles", masse=True):
        """Druckfertiges A3-Querformat: Rahmen mit Rasterbezuegen, Skizze,
        Stueckliste, Nahtliste, Legende und Titelblock.

        Der Platz in der rechten Spalte wird ausgerechnet, nicht geraten: was
        nicht draufpasst, wird ehrlich abgeschnitten und angesagt. Die
        vollstaendigen Listen stehen im Excel-Export.

        Kein Ersatz fuer eine Fertigungsisometrie aus einem CAD-System - aber
        ein Blatt, das man mit auf die Baustelle nehmen kann.
        """
        kopf = kopf or {}
        fig = plt.figure(figsize=(Visualizer._A3_B, Visualizer._A3_H))
        blatt = fig.add_axes([0, 0, 1, 1])
        blatt.set_xlim(0, 1)
        blatt.set_ylim(0, 1)
        blatt.axis('off')
        blatt.add_patch(mpatches.Rectangle((0, 0), 1, 1, fc='white', ec='none',
                                           zorder=0))

        # ---- Rahmen mit Rasterbezuegen -------------------------------------
        m, mi = 0.016, 0.032            # Aussenrand / Innenrahmen
        blatt.add_patch(mpatches.Rectangle((m, m), 1 - 2 * m, 1 - 2 * m,
                                           fc='none', ec='#0f172a', lw=1.0))
        blatt.add_patch(mpatches.Rectangle((mi, mi), 1 - 2 * mi, 1 - 2 * mi,
                                           fc='none', ec='#0f172a', lw=1.6))
        n_sp, n_ze = 8, 6
        for i in range(n_sp):
            x0 = mi + (1 - 2 * mi) * i / n_sp
            x1 = mi + (1 - 2 * mi) * (i + 1) / n_sp
            for yy, unten in ((mi, True), (1 - mi, False)):
                blatt.text((x0 + x1) / 2.0, yy + (0.008 if unten else -0.008),
                           str(i + 1), ha='center', va='center', fontsize=7.0,
                           color='#475569')
                if i:
                    blatt.plot([x0, x0], [yy, yy + (0.011 if unten else -0.011)],
                               color='#0f172a', lw=0.8)
        for j in range(n_ze):
            y0 = mi + (1 - 2 * mi) * j / n_ze
            y1 = mi + (1 - 2 * mi) * (j + 1) / n_ze
            for xx in (mi, 1 - mi):
                links = xx == mi
                blatt.text(xx + (0.007 if links else -0.007), (y0 + y1) / 2.0,
                           "ABCDEF"[n_ze - 1 - j], ha='center', va='center',
                           fontsize=7.0, color='#475569')
                if j:
                    blatt.plot([xx, xx + (0.011 if links else -0.011)], [y0, y0],
                               color='#0f172a', lw=0.8)

        # ---- Aufteilung ------------------------------------------------------
        rx = 0.688                                  # linke Kante rechte Spalte
        rb = (1 - mi - 0.012) - rx                  # Breite rechte Spalte
        tb_h, tb_y = 0.146, mi + 0.016              # Titelblock unten rechts
        leg_n = 9
        leg_h = 0.016 + leg_n * 0.0165              # Legende darueber
        leg_y = tb_y + tb_h + 0.016 + leg_h         # Oberkante Legende
        top = 1 - mi - 0.030                        # unter den Rasterziffern
        boden = leg_y + 0.012                       # hier muessen Tabellen enden

        # ---- Zeichenflaeche --------------------------------------------------
        zx, zy = mi + 0.012, mi + 0.012
        zb, zh = rx - 0.026 - zx, 1 - mi - 0.012 - zy
        ax = fig.add_axes([zx, zy, zb, zh])
        Visualizer.plot_spool(spool, "", massstab=massstab, naht_nr=naht_nr,
                              ballons=ballons, ax=ax, modus=modus, masse=masse)
        blatt.plot([rx - 0.014, rx - 0.014], [mi, 1 - mi], color='#0f172a', lw=0.9)

        # ---- Zeilen auf den vorhandenen Platz verteilen ----------------------
        zeil_h, kopf_h = 0.019, 0.026
        tabellen = [
            ("Stueckliste", spool.get("pos_rows", []), "Positionen",
             [("Pos", 0.55), ("Anzahl", 1.05), ("Benennung", 2.7), ("DN", 0.5),
              ("Wand", 0.7, "Wand (mm)"), ("Werkstoff", 1.3), ("Norm", 1.6)]),
            ("Nahtliste", spool.get("naht_rows", []), "Naehte",
             [("Naht", 0.8), ("Art", 1.5), ("DN", 0.5), ("Ort", 3.0),
              ("Wo", 1.1, "Werkstatt/Feld")]),
        ]
        tabellen = [x for x in tabellen if x[1]]
        platz = top - boden
        fix = len(tabellen) * (kopf_h + 0.012 + 0.012) +             max(0, len(tabellen) - 1) * 0.022
        frei = max(0.0, platz - fix)
        moeglich = int(frei / zeil_h)
        gewuenscht = [len(x[1]) for x in tabellen]
        anzahl = list(gewuenscht)
        if sum(gewuenscht) > moeglich:              # anteilig kuerzen, min. 3
            rest, anzahl = moeglich, []
            for i, w in enumerate(gewuenscht):
                n = max(3, int(round(moeglich * w / float(sum(gewuenscht)))))
                anzahl.append(n)
            while sum(anzahl) > moeglich:           # Rundung wieder einfangen
                i = anzahl.index(max(anzahl))
                if anzahl[i] <= 3:
                    break
                anzahl[i] -= 1

        y = top
        for (titel, rows, wort, spalten), n in zip(tabellen, anzahl):
            y = Visualizer._blatt_tabelle(blatt, rx, y, rb, spalten, rows[:n],
                                          titel=titel, kopf_h=kopf_h,
                                          zeil_h=zeil_h)
            if len(rows) > n:
                blatt.text(rx, y - 0.010, "... %d weitere %s – siehe Excel"
                           % (len(rows) - n, wort), fontsize=5.4,
                           color='#b91c1c', va='top')
                y -= 0.012           # Platz fuer den Hinweis, sonst ueberschreibt
            y -= 0.034               # ihn die naechste Ueberschrift

        # ---- Legende ---------------------------------------------------------
        ly = leg_y
        blatt.text(rx, ly, "Legende", fontsize=7.0, fontweight='bold',
                   color='#0f172a', va='top')
        ly -= 0.018
        leg = [("naht_w", "Werkstattnaht"), ("naht_f", "Baustellennaht"),
               ("flansch", "Vorschweissflansch"), ("armatur", "Armatur"),
               ("klappe", "Klappe (Zwischenflansch)"),
               ("demo", "Demontagestueck"),
               ("tee", "Fertig-T"), ("stutzen", "Anschweissstutzen"),
               ("ballon", "Positionsnummer aus der Stueckliste")]
        for key, txt in leg:
            px = rx + 0.008
            if key == "naht_w":
                blatt.plot(px, ly, 'o', color='#0f172a', ms=4.0)
            elif key == "naht_f":
                blatt.plot(px, ly, 'o', mfc='white', mec='#b91c1c', mew=1.4, ms=6.5)
                blatt.plot(px, ly, 'x', color='#b91c1c', mew=1.4, ms=4.0)
            elif key == "flansch":
                blatt.plot([px, px], [ly - 0.005, ly + 0.005], color='#b91c1c', lw=2.2)
            elif key == "armatur":
                blatt.plot([px - 0.004, px + 0.004], [ly - 0.005, ly + 0.005],
                           color='#b91c1c', lw=1.4)
                blatt.plot([px - 0.004, px + 0.004], [ly + 0.005, ly - 0.005],
                           color='#b91c1c', lw=1.4)
            elif key == "klappe":
                blatt.plot([px - 0.006, px + 0.006], [ly - 0.005, ly + 0.005],
                           color='#b91c1c', lw=1.6)
                for vz in (-1, 1):
                    blatt.plot([px - 0.006, px + 0.006],
                               [ly + 0.005 * vz, ly + 0.005 * vz],
                               color='#b91c1c', lw=1.2)
            elif key == "demo":
                for vz in (-1, 1):
                    blatt.plot([px - 0.007, px + 0.007],
                               [ly + 0.005 * vz, ly + 0.005 * vz],
                               color='#b91c1c', lw=1.0)
                blatt.plot([px - 0.003, px + 0.003], [ly, ly],
                           color='#b91c1c', lw=2.4)
            elif key == "tee":
                blatt.plot(px, ly, 's', color='#b91c1c', ms=5.0)
            elif key == "stutzen":
                blatt.plot(px, ly, 'D', color='#b91c1c', ms=5.0)
            else:
                blatt.add_patch(mpatches.Circle((px, ly), 0.005, fc='white',
                                                ec='#7c3aed', lw=1.1))
            blatt.text(px + 0.013, ly, txt, fontsize=5.9, va='center',
                       color='#334155')
            ly -= 0.0165

        # ---- Titelblock ------------------------------------------------------
        tb_x, tb_b = rx - 0.014, rb + 0.026
        blatt.add_patch(mpatches.Rectangle((tb_x, tb_y), tb_b, tb_h, fc='white',
                                           ec='#0f172a', lw=1.4, zorder=5))
        felder = [
            ("Zeichnung", kopf.get("zeichnr", "")),
            ("Leitung", kopf.get("leitung", "")),
            ("Projekt / Anlage", kopf.get("projekt", "")),
            ("NPD", "DN %s" % kopf.get("dn", "")),
            ("Werkstoff", spool.get("werkstoff", "")),
            ("Schedule", spool.get("schedule", "")),
            ("Auslegungsdruck", kopf.get("druck", "")),
            ("Auslegungstemperatur", kopf.get("temp", "")),
            ("Isolierung", kopf.get("isol", "")),
            ("Rohr gesamt", "%.2f m" % (spool.get("total_axis", 0) / 1000.0)),
            ("Naehte / Flansche", "%d / %d" % (spool.get("naehte", 0),
                                               spool.get("flanschverbindungen", 0))),
            ("Baustellennaehte", "%d" % sum(1 for n in spool.get("nahtliste", [])
                                            if n.get("feld"))),
            ("Erstellt von", kopf.get("ersteller", "")),
            ("Datum / Ansicht", "%s  ·  %s" % (kopf.get("datum", "-"), modus)),
        ]
        k_h = 0.024
        zeil = (tb_h - k_h) / 7.0
        halb = tb_b / 2.0
        for i, (k, v) in enumerate(felder):
            sp_, ze_ = i % 2, i // 2
            fx = tb_x + 0.006 + sp_ * halb
            fy = tb_y + tb_h - k_h - ze_ * zeil
            blatt.text(fx, fy - 0.006, k, fontsize=5.2, color='#64748b',
                       va='center', zorder=6)
            blatt.text(fx, fy - 0.014,
                       Visualizer._kurz(v if v else "–", halb - 0.010, 7.0),
                       fontsize=7.0, color='#0f172a', fontweight='bold',
                       va='center', zorder=6)
        blatt.text(tb_x + halb, tb_y + tb_h - k_h / 2.0, "PipeCraft – Rohrfolge",
                   fontsize=9.0, fontweight='bold', ha='center', va='center',
                   color='#0f172a', zorder=6)
        blatt.plot([tb_x, tb_x + tb_b], [tb_y + tb_h - k_h] * 2,
                   color='#0f172a', lw=0.9, zorder=6)
        for i in range(1, 7):
            yy = tb_y + tb_h - k_h - i * zeil
            blatt.plot([tb_x, tb_x + tb_b], [yy, yy], color='#cbd5e1', lw=0.5,
                       zorder=6)
        blatt.plot([tb_x + halb, tb_x + halb], [tb_y, tb_y + tb_h - k_h],
                   color='#cbd5e1', lw=0.5, zorder=6)

        blatt.text(m + 0.004, m / 2.0,
                   "Richtwert – WPS, Norm und Projektspezifikation haben "
                   "Vorrang. Naeherung fuer Aufmass und Bestellung, keine "
                   "Fertigungsisometrie.", fontsize=6.0, color='#64748b',
                   va='center')
        plt.close(fig)
        return fig

    @staticmethod
    def _flange_bar(ax, q, u, p, s, along, half=0.85, lw=2.4):
        """Ein Flanschblatt: Querstrich im Abstand `along`*s laengs der Achse."""
        c = (q[0] + u[0] * along * s, q[1] + u[1] * along * s)
        ax.plot([c[0] - p[0] * half * s, c[0] + p[0] * half * s],
                [c[1] - p[1] * half * s, c[1] + p[1] * half * s],
                color='#b91c1c', lw=lw, zorder=6, solid_capstyle='round')

    @staticmethod
    def _free_flange_ends(spool, by_row, iso):
        """Freie Kettenenden mit Flanschende -> Position + Achsrichtung."""
        items = spool["items"]
        out = []
        for it, am_anfang in ((items[0], True), (items[-1], False)):
            if it["ends"][0 if am_anfang else 1] != "F":
                continue
            ls = by_row.get(it["row"])
            if not ls:
                continue
            q = iso(ls[0]["a"]) if am_anfang else iso(ls[-1]["b"])
            r = iso(ls[-1]["b"]) if am_anfang else iso(ls[0]["a"])
            dx, dy = r[0] - q[0], r[1] - q[1]
            if math.hypot(dx, dy) < 1e-9:
                # Flansch ohne Zeichenlaenge - Richtung aus der Bauteilachse
                d3 = ls[0]["d"]
                r = iso(tuple(ls[0]["a"][k] + d3[k] * 1000.0
                              for k in range(3)))
                dx, dy = r[0] - q[0], r[1] - q[1]
                if not am_anfang:
                    dx, dy = -dx, -dy
            n = math.hypot(dx, dy) or 1.0
            out.append((q, (dx / n, dy / n), (-dy / n, dx / n)))
        return out

    # ---------------------------------------------- Platzverwaltung --------
    # Beschriftungen duerfen sich nicht ueberschneiden. Punktabstaende reichen
    # dafuer nicht - ein langer Text ueberlappt einen Nachbarn, dessen Mitte
    # weit genug weg ist. Darum wird jede Beschriftung als Rechteck gefuehrt
    # und jede neue gegen alle bisherigen geprueft.

    # Wieviel groesser der fertige Bildausschnitt ist als die Rohrzeichnung
    # allein. Kommt unten noch ein Detail-Kasten dazu, schrumpft die Zeichnung
    # beim Einpassen - der Text bleibt gleich gross und deckt dann mehr
    # Datenbereich ab. Ohne diesen Faktor waere jede Flaechenschaetzung zu
    # klein und Beschriftungen wuerden sich wieder ueberschneiden.
    _TEXT_SKALA = 1.0

    @staticmethod
    def _txt_rect(pos, text, fs, span, rot=0.0):
        """Geschaetzte Textflaeche in Datenkoordinaten, um `rot` Grad gedreht.

        Gedrehter Text braucht eine andere Flaeche als waagerechter - ein
        senkrecht stehendes Mass ist schmal und hoch, nicht breit und flach.
        Die Schaetzung ist bewusst etwas grosszuegig: lieber etwas Luft zu
        viel als eine Ueberschneidung.
        """
        zeilen = str(text).split(chr(10))
        # Werte fuer fetten Text gemessen - lieber etwas zu breit schaetzen
        sp_ = span * Visualizer._TEXT_SKALA
        # Mindestbreite: eine einstellige Nummer belegt gerendert deutlich mehr
        # als ein Zeichen breit - ohne den Boden ueberschneiden sich kurze
        # Kennungen wie "5" und "WF6".
        n_z = max(3.0, max(len(z) for z in zeilen))
        b = n_z * sp_ * 0.0155 * (fs / 8.0)
        h = len(zeilen) * sp_ * 0.037 * (fs / 8.0)
        if rot:
            c = abs(math.cos(math.radians(rot)))
            s = abs(math.sin(math.radians(rot)))
            b, h = b * c + h * s, b * s + h * c
        return (pos[0] - b / 2.0, pos[1] - h / 2.0,
                pos[0] + b / 2.0, pos[1] + h / 2.0)

    @staticmethod
    def _weiter(r, d):
        """Rechteck ringsum um d aufweiten."""
        return (r[0] - d, r[1] - d, r[2] + d, r[3] + d)

    @staticmethod
    def _ueberlappung(r, belegt):
        """Wie viel Flaeche sich mit schon Gesetztem ueberschneidet."""
        s = 0.0
        for q in belegt:
            bx = min(r[2], q[2]) - max(r[0], q[0])
            by = min(r[3], q[3]) - max(r[1], q[1])
            if bx > 0 and by > 0:
                s += bx * by
        return s

    @staticmethod
    def _frei(r, belegt):
        for q in belegt:
            if r[0] < q[2] and r[2] > q[0] and r[1] < q[3] and r[3] > q[1]:
                return False
        return True

    @staticmethod
    def _platz(anker, text, fs, span, belegt, richtungen=None, radien=None):
        """Freie Stelle fuer eine Beschriftung suchen und belegen.

        Findet sich in den angebotenen Richtungen nichts, wird der Radius
        aufgedreht, bis es passt. Eine Ueberschneidung gibt es damit nicht -
        im schlimmsten Fall steht die Beschriftung weiter weg.
        """
        if richtungen is None:
            richtungen = [(math.cos(math.radians(g)), math.sin(math.radians(g)))
                          for g in range(0, 360, 30)]
        rad = list(radien or (0.045, 0.070, 0.100))
        frei_best = None
        for _runde in range(16):
            for r_ in rad:
                for wx, wy in richtungen:
                    pos = (anker[0] + span * r_ * wx, anker[1] + span * r_ * wy)
                    # Etwas Luft: die Schaetzung liegt sonst um Haaresbreite
                    # daneben und zwei Kennungen beruehren sich doch.
                    rect = Visualizer._weiter(
                        Visualizer._txt_rect(pos, text, fs, span), span * 0.005)
                    if Visualizer._frei(rect, belegt):
                        belegt.append(rect)
                        return pos
                    # Falls gar nichts frei ist: die Stelle merken, an der am
                    # wenigsten ueberlappt - blind irgendwo hinsetzen waere
                    # schlechter.
                    ueb = Visualizer._ueberlappung(rect, belegt)
                    if frei_best is None or ueb < frei_best[0]:
                        frei_best = (ueb, pos, rect)
            rad = [x * 1.35 for x in rad]
        _u, pos, rect = frei_best
        belegt.append(rect)
        return pos

    @staticmethod
    def _label_frei(ax, mid, p, off, text, belegt, span, farbe='#475569',
                    fs=7.5):
        """Beschriftung dicht neben das Bauteil setzen - **ohne** Fuehrungslinie.

        Ein Formteil soll als Formteil zu erkennen sein und nicht noch einen
        Strich mit sich herumtragen: aus einem Bogen mit Fuehrungslinie wird
        auf den ersten Blick ein Abzweig. Die Zuordnung macht die Naehe.

        Bevorzugt quer zum Rohr (Richtung p), weicht aber rundum aus, bis eine
        freie Flaeche gefunden ist.
        """
        richt = [(p[0], p[1]), (-p[0], -p[1])]
        richt += [(math.cos(math.radians(g)), math.sin(math.radians(g)))
                  for g in range(0, 360, 30)]
        nah = off / span
        q = Visualizer._platz(mid, text, fs, span, belegt, richt,
                              (nah * 0.62, nah, nah * 1.5, nah * 2.1))
        ax.annotate(text, q, ha='center', va='center', fontsize=fs,
                    color=farbe, fontweight='bold', zorder=7,
                    bbox=dict(boxstyle='round,pad=0.15', fc='white',
                              ec='#e2e8f0', lw=0.5))
        return q

    @staticmethod
    def _teil_label(it):
        """Kurzbeschriftung: die Bauteilnummer - und ein Wert nur dort, wo er
        Geometrie ist, die man der Zeichnung nicht ansieht (Bogenwinkel).

        Alle Laengen stehen an den Gesamtmassen und in den Listen. Ein Mass an
        jedem Flansch und jedem Bogen macht die Zeichnung unlesbar, ohne dass
        es jemand braucht.
        """
        nr, part = it["row"], it["part"]
        if part == "Versprung":
            return "%d  Versprung %g°" % (nr, it["vers"]["winkel"])
        if part == "Bogen 90":
            return "%d  90°" % nr
        return "%d" % nr

    # ------------------------------------------------ Bemassung -------------
    @staticmethod
    def _pfeil(ax, spitze, richtung, quer, gr, farbe):
        """Masspfeil: gefuellte Spitze, die auf den Messpunkt zeigt.

        Auf einer Rohrleitungsiso sind Schraegstriche ueblich - bei einem
        Kettenmass mit vielen kurzen Abschnitten kann man aber nicht mehr
        sehen, welcher Strich zu welchem Mass gehoert. Pfeile zeigen es.
        """
        b = gr * 0.42
        fuss = (spitze[0] - richtung[0] * gr, spitze[1] - richtung[1] * gr)
        ax.fill([spitze[0], fuss[0] + quer[0] * b, fuss[0] - quer[0] * b],
                [spitze[1], fuss[1] + quer[1] * b, fuss[1] - quer[1] * b],
                color=farbe, lw=0.0, zorder=5)

    @staticmethod
    def _mass_linie(ax, a, b, text, span, belegt, farbe='#334155', fs=8.0,
                    grund=0.042, stufen=5, linien=None, vorzug=0.0):
        """Masslinie wie auf einer Fertigungsisometrie.

        Duenne Linie parallel zum Rohr, **dicht daneben** - nicht in einer Bahn
        am Blattrand. Kurze Hilfslinien fuehren vom Rohr zur Masslinie,
        Schraegstriche begrenzen sie, und die Zahl sitzt mit weissem Grund
        mitten auf der Linie: dadurch wird die Linie von der Zahl unterbrochen
        und beides bleibt gut lesbar.

        Ist die erste Lage belegt, rueckt die Masslinie stufenweise ein Stueck
        weiter heraus oder auf die andere Rohrseite - aber immer nur so weit
        wie noetig.
        """
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy)
        if n < 1e-9:
            return
        u = (dx / n, dy / n)
        p = (-u[1], u[0])
        winkel = math.degrees(math.atan2(dy, dx))
        if winkel > 90:
            winkel -= 180
        elif winkel < -90:
            winkel += 180
        luft = span * 0.010          # Abstand Hilfslinie zum Rohr
        ueber = span * 0.012         # Ueberstand der Hilfslinie
        tick = span * 0.013          # halbe Laenge der Schraegstriche

        def _zeichnen(off):
            A = (a[0] + p[0] * off, a[1] + p[1] * off)
            B = (b[0] + p[0] * off, b[1] + p[1] * off)
            vz = 1.0 if off >= 0 else -1.0
            for P, Q in ((a, A), (b, B)):
                ax.plot([P[0] + p[0] * luft * vz, Q[0] + p[0] * ueber * vz],
                        [P[1] + p[1] * luft * vz, Q[1] + p[1] * ueber * vz],
                        color=farbe, lw=0.6, zorder=4)
            ax.plot([A[0], B[0]], [A[1], B[1]], color=farbe, lw=0.7, zorder=4)
            for P in (A, B):
                ax.plot([P[0] - (u[0] + p[0]) * tick,
                         P[0] + (u[0] + p[0]) * tick],
                        [P[1] - (u[1] + p[1]) * tick,
                         P[1] + (u[1] + p[1]) * tick],
                        color=farbe, lw=1.0, zorder=4)
            M = ((A[0] + B[0]) / 2.0, (A[1] + B[1]) / 2.0)
            ax.text(M[0], M[1], text, rotation=winkel, rotation_mode='anchor',
                    ha='center', va='center', fontsize=fs, color=farbe,
                    zorder=6,
                    bbox=dict(boxstyle='round,pad=0.14', fc='white', ec='none'))
            if linien is not None:
                # Auch die Hilfslinien merken - sie kreuzen genauso.
                linien.append((A, B))
                for P, Q in ((a, A), (b, B)):
                    linien.append(((P[0] + p[0] * luft * vz,
                                    P[1] + p[1] * luft * vz),
                                   (Q[0] + p[0] * ueber * vz,
                                    Q[1] + p[1] * ueber * vz)))

        # Bewertet wird beides: die Textflaeche und ob die Masslinie eine
        # schon gezogene kreuzt. Ein belegter Text wiegt schwerer - eine
        # unlesbare Zahl ist schlimmer als zwei sich kreuzende Linien.
        bestes = None
        for stufe in range(stufen):
            for seite in ((vorzug, -vorzug) if vorzug else (1.0, -1.0)):
                off = span * (grund + 0.034 * stufe) * seite
                A = (a[0] + p[0] * off, a[1] + p[1] * off)
                B = (b[0] + p[0] * off, b[1] + p[1] * off)
                M = ((A[0] + B[0]) / 2.0, (A[1] + B[1]) / 2.0)
                r = Visualizer._weiter(
                    Visualizer._txt_rect(M, text, fs, span, winkel),
                    span * 0.012)
                ueb = Visualizer._ueberlappung(r, belegt)
                vz = 1.0 if off >= 0 else -1.0
                pruef = [(A, B)]
                for P, Q in ((a, A), (b, B)):
                    pruef.append(((P[0] + p[0] * luft * vz,
                                   P[1] + p[1] * luft * vz),
                                  (Q[0] + p[0] * ueber * vz,
                                   Q[1] + p[1] * ueber * vz)))
                kreuze = sum(1 for n0, n1 in pruef for a0, a1 in (linien or [])
                             if Visualizer._schneidet(n0, n1, a0, a1))
                note = (1.0 if ueb > 0 else 0.0) * 1e6 + kreuze * 1e3 + ueb
                if note <= 0.0:
                    belegt.append(r)
                    _zeichnen(off)
                    return
                if bestes is None or note < bestes[0]:
                    bestes = (note, off, r)
        _n, off, r = bestes
        belegt.append(r)
        _zeichnen(off)

    @staticmethod
    def _kettenmass(ax, pts, texte, span, belegt, farbe='#334155', fs=7.4,
                    grund=0.042, stufen=6, linien=None):
        """Kettenmass: mehrere Messpunkte an einem Lauf auf **einer** Linie,
        Punkt an Punkt - so, wie man am Rohr abgreift: Anriss, Anriss, Rest.

        Einzelmasse waeren hier falsch: bei zwei Stutzen auf einem Rohr lagen
        sie uebereinander und man sah nicht mehr, welches wohin gehoert.

        Gemessen wird mit **Pfeilen** statt Schraegstrichen: bei kurzen
        Abschnitten sieht man sonst nicht, welcher Strich zu welchem Mass
        gehoert.
        """
        if len(pts) < 2 or len(texte) < 1:
            return
        dx, dy = pts[-1][0] - pts[0][0], pts[-1][1] - pts[0][1]
        n = math.hypot(dx, dy)
        if n < 1e-9:
            return
        u = (dx / n, dy / n)
        p_ = (-u[1], u[0])
        winkel = math.degrees(math.atan2(dy, dx))
        if winkel > 90:
            winkel -= 180
        elif winkel < -90:
            winkel += 180
        luft = span * 0.010
        ueber = span * 0.012
        gr = span * 0.020                    # Pfeillaenge

        def _lagen(off0):
            """Fuer jedes Mass: (Anfang, Ende, Text, Versatz)."""
            return [(pts[i], pts[i + 1], t, off0)
                    for i, t in enumerate(texte)]

        def _mitte(A0, B0, off):
            return ((A0[0] + B0[0]) / 2.0 + p_[0] * off,
                    (A0[1] + B0[1]) / 2.0 + p_[1] * off)

        def _zeichnen(lagen):
            vz = 1.0 if lagen[0][3] >= 0 else -1.0
            for A0, B0, t, off in lagen:
                A = (A0[0] + p_[0] * off, A0[1] + p_[1] * off)
                B = (B0[0] + p_[0] * off, B0[1] + p_[1] * off)
                for P, Q in ((A0, A), (B0, B)):
                    ax.plot([P[0] + p_[0] * luft * vz, Q[0] + p_[0] * ueber * vz],
                            [P[1] + p_[1] * luft * vz, Q[1] + p_[1] * ueber * vz],
                            color=farbe, lw=0.6, zorder=4)
                ax.plot([A[0], B[0]], [A[1], B[1]], color=farbe, lw=0.7,
                        zorder=4)
                Visualizer._pfeil(ax, A, (-u[0], -u[1]), p_, gr, farbe)
                Visualizer._pfeil(ax, B, u, p_, gr, farbe)
                M = _mitte(A0, B0, off)
                ax.text(M[0], M[1], t, rotation=winkel,
                        rotation_mode='anchor', ha='center', va='center',
                        fontsize=fs, color=farbe, zorder=6,
                        bbox=dict(boxstyle='round,pad=0.12', fc='white',
                                  ec='none'))
                belegt.append(Visualizer._txt_rect(M, t, fs, span, winkel))
                if linien is not None:
                    linien.append((A, B))

        # Die ganze Kette wird als Block bewertet: entweder passt sie, oder sie
        # rueckt gemeinsam weiter nach aussen. Einzeln verschoben waere es
        # keine Kette mehr.
        bestes = None
        for stufe in range(stufen):
            for seite in (1.0, -1.0):
                off0 = span * (grund + 0.034 * stufe) * seite
                lagen = _lagen(off0)
                ueb = 0.0
                for A0, B0, t, off in lagen:
                    r = Visualizer._weiter(
                        Visualizer._txt_rect(_mitte(A0, B0, off), t, fs, span,
                                             winkel), span * 0.010)
                    ueb += Visualizer._ueberlappung(r, belegt)
                if ueb <= 0.0:
                    _zeichnen(lagen)
                    return
                if bestes is None or ueb < bestes[0]:
                    bestes = (ueb, lagen)
        _zeichnen(bestes[1])

    @staticmethod
    def _schneidet(p1, p2, p3, p4):
        """Schneiden sich die Strecken p1p2 und p3p4 (echte Kreuzung)?"""
        def kreuz(o, a, b):
            return ((a[0] - o[0]) * (b[1] - o[1])
                    - (a[1] - o[1]) * (b[0] - o[0]))
        d1, d2 = kreuz(p3, p4, p1), kreuz(p3, p4, p2)
        d3, d4 = kreuz(p1, p2, p3), kreuz(p1, p2, p4)
        return ((d1 > 1e-12) != (d2 > 1e-12)) and ((d3 > 1e-12) != (d4 > 1e-12))

    @staticmethod
    def _rechter_winkel(ax, ecke, p1, p2, laenge, farbe='#64748b'):
        """Winkelzeichen an einer Ecke der Versatzfigur.

        In der Isometrie sieht ein rechter Winkel schief aus - deshalb wird er
        in der Iso-Darstellung eigens markiert (Bentley OpenPlant nennt das
        "right angle indicator"). Das Zeichen laeuft parallel zu den beiden
        Kanten, ist also selbst schief: genau so gehoert es sich.
        """
        def _e(q):
            dx, dy = q[0] - ecke[0], q[1] - ecke[1]
            n = math.hypot(dx, dy)
            return None if n < 1e-9 else (dx / n * laenge, dy / n * laenge)
        u1, u2 = _e(p1), _e(p2)
        if u1 is None or u2 is None:
            return
        pfad = [(ecke[0] + u1[0], ecke[1] + u1[1]),
                (ecke[0] + u1[0] + u2[0], ecke[1] + u1[1] + u2[1]),
                (ecke[0] + u2[0], ecke[1] + u2[1])]
        ax.plot([q[0] for q in pfad], [q[1] for q in pfad], color=farbe,
                lw=0.7, zorder=3)


    @staticmethod
    def _schraffur(ax, ecken, richtung, abstand, farbe='#7c8da3', lw=0.7):
        """Flaeche mit Linien **parallel zu einer Kante** schraffieren.

        Matplotlibs `hatch` legt die Linien bildschirmfest auf 45 Grad - in
        einer Isometrie liegt die Schraffur dann quer zur Ebene, die sie
        darstellen soll, und die Flaeche sieht falsch aus. Hier laufen die
        Linien in einer Richtung, die in der Ebene selbst liegt; dadurch
        bekommen die waagerechte und die senkrechte Teilflaeche von sich aus
        verschiedene Richtungen.
        """
        n = math.hypot(richtung[0], richtung[1])
        if n < 1e-9 or len(ecken) < 3:
            return
        u = (richtung[0] / n, richtung[1] / n)
        p = (-u[1], u[0])
        lagen = [q[0] * p[0] + q[1] * p[1] for q in ecken]
        t0, t1 = min(lagen), max(lagen)
        if t1 - t0 < abstand * 0.5:
            return                                   # zu schmal fuer Linien
        kanten = list(zip(ecken, ecken[1:] + ecken[:1]))
        t = t0 + abstand
        while t < t1 - 1e-9:
            treffer = []
            for A, B in kanten:
                ta = A[0] * p[0] + A[1] * p[1]
                tb = B[0] * p[0] + B[1] * p[1]
                if (ta - t) * (tb - t) > 0 or abs(tb - ta) < 1e-12:
                    continue                         # Kante schneidet nicht
                f = (t - ta) / (tb - ta)
                treffer.append((A[0] + (B[0] - A[0]) * f,
                                A[1] + (B[1] - A[1]) * f))
            if len(treffer) >= 2:
                treffer.sort(key=lambda q: q[0] * u[0] + q[1] * u[1])
                A, B = treffer[0], treffer[-1]
                ax.plot([A[0], B[0]], [A[1], B[1]], color=farbe, lw=lw,
                        zorder=1, solid_capstyle='butt')
            t += abstand

    @staticmethod
    def _versprung_bau(ax, iso, l_diag, d_lauf, vers, span, belegt, mlin, off):
        """Versatz als **zwei schraffierte Flaechen** - so, wie er auf einer
        Fertigungsisometrie steht.

        Recherchiert und an einer Zeichnung aus der Praxis nachgezogen
        (Bentley OpenPlant Isometrics Manager, "Rolling Offset Depiction"):

        * **liegende Flaeche** - das Rechteck aus Lauf und Seite. Seine
          Diagonale ist der Schatten des Rohres auf dem Boden.
        * **senkrechte Flaeche** - das Dreieck aus Hoehe, diesem Schatten und
          dem Rohr selbst als Hypotenuse.

        Beide werden schraffiert, jede **in ihrer eigenen Richtung**: die
        senkrechte laengs der Hoehe, die liegende laengs der Seite. Dadurch
        sind sie auf den ersten Blick auseinanderzuhalten.

        Keine geschlossene Box: das waere dieselbe Geometrie mit doppelt so
        vielen Strichen - auch den verdeckten hinten, die sich mit dem Rohr
        beissen. Ohne Seitenversatz faellt das Rechteck ohnehin zu einer Linie
        zusammen; dann bleibt das schraffierte Dreieck allein stehen, die
        uebliche 2D-Darstellung.

        Die drei Konstruktionsmasse liegen **aussen auf einem Rahmen** mit
        langen Hilfslinien - die Figur soll frei bleiben. Nur der Rohrweg
        laeuft dicht am Rohr, weil er dorthin gehoert. ("Nah ans Rohr" gilt
        fuer Rohrlaengen, nicht fuer die Versatzkonstruktion.)
        """
        P0, P1 = l_diag["a"], l_diag["b"]
        D = tuple(P1[k] - P0[k] for k in range(3))
        waag = (D[0], D[1], 0.0)
        r = d_lauf
        rl = math.sqrt(r[0] ** 2 + r[1] ** 2) or 1.0
        rn = (r[0] / rl, r[1] / rl, 0.0)
        skal = waag[0] * rn[0] + waag[1] * rn[1]
        lauf = (rn[0] * skal, rn[1] * skal, 0.0)
        seite = (waag[0] - lauf[0], waag[1] - lauf[1], 0.0)
        hoehe = (0.0, 0.0, D[2])

        def pkt(*teile):
            """Punkt aus P0 plus beliebigen Teilvektoren, gleich in Iso."""
            q = list(P0)
            for t in teile:
                for m in range(3):
                    q[m] += t[m]
            return iso(tuple(q))

        # **Zwei rechtwinklige Dreiecke**, nicht Dreieck und Rechteck: so wird
        # ein Versprung abgewickelt und so wird er auch gerechnet.
        #
        #   waagerecht:  Lauf und Seite      -> Hypotenuse ist der Schatten
        #   senkrecht:   Hoehe und Schatten  -> Hypotenuse ist das Rohr
        #
        # Ein Rechteck haette zwei Kanten mehr, die zu keinem Mass gehoeren.
        #
        # Das waagerechte Dreieck liegt immer auf der **unteren** Hoehe, damit
        # die Figur unter dem Rohr steht und nicht darueber schwebt:
        #
        #   Versatz faellt -> erst runter, dann laufen (Hoehe am Anfang)
        #   Versatz steigt -> erst laufen, dann hoch  (Hoehe am Ende)
        if D[2] < 0:
            C0, C1 = pkt(hoehe), pkt(hoehe, lauf)
            C2 = pkt(hoehe, lauf, seite)
            hoch = pkt()                    # oberes Rohrende = Anfang
            fuss, fuss_arm = C0, C2         # Fuss der Hoehenkante
            rohr = (hoch, C2)
        else:
            C0, C1 = pkt(), pkt(lauf)
            C2 = pkt(lauf, seite)
            hoch = pkt(lauf, seite, hoehe)  # oberes Rohrende = Ende
            fuss, fuss_arm = C2, C0
            rohr = (C0, hoch)

        hat_seite = bool(vers.get("seite"))
        umriss = '#64748b'
        abst = span * 0.016

        # Senkrechtes Dreieck: Hoehe, Schatten, Rohr. Schraffur laengs der Hoehe.
        Visualizer._schraffur(ax, [C0, C2, hoch],
                              (hoch[0] - fuss[0], hoch[1] - fuss[1]),
                              abst, lw=0.55)
        for X, Y in ((fuss, hoch), (C0, C2)):
            ax.plot([X[0], Y[0]], [X[1], Y[1]], color=umriss, lw=0.8, zorder=2)
        punkte = [C0, C2, hoch]
        kanten = [(fuss, hoch, "H  %.0f" % abs(vers["hoehe"]))]

        if hat_seite:
            # Waagerechtes Dreieck: Lauf, Seite, Schatten. Schraffur laengs der
            # Seite - also quer zur senkrechten Flaeche, damit man die beiden
            # nicht verwechselt.
            Visualizer._schraffur(ax, [C0, C1, C2],
                                  (C2[0] - C1[0], C2[1] - C1[1]), abst,
                                  lw=0.55)
            for X, Y in ((C0, C1), (C1, C2)):
                ax.plot([X[0], Y[0]], [X[1], Y[1]], color=umriss, lw=0.8,
                        zorder=2)
            punkte.append(C1)
            kanten.append((C0, C1, "L  %.0f" % vers["run"]))
            kanten.append((C1, C2, "S  %.0f" % abs(vers["seite"])))
            # Rechter Winkel auch im waagerechten Dreieck: Lauf gegen Seite.
            Visualizer._rechter_winkel(ax, C1, C0, C2, span * 0.014)
        else:
            kanten.append((C0, C2, "L  %.0f" % vers["run"]))

        # Rechter Winkel zwischen Hoehe und Schatten - in der Isometrie sieht
        # er schief aus, darum wird er markiert.
        Visualizer._rechter_winkel(ax, fuss, hoch, fuss_arm, span * 0.014)

        mx = sum(q[0] for q in punkte) / len(punkte)
        my = sum(q[1] for q in punkte) / len(punkte)

        def masz(X, Y, txt, grund, weg_von=None):
            """weg_von: Punkt, von dem das Mass wegzeigen soll. Fuer die
            Kanten ist das der Mittelpunkt der Figur; fuer den Rohrweg die
            freie Ecke - das Rohr hat die Figur auf einer Seite, und auf der
            anderen ist Platz."""
            dx, dy = Y[0] - X[0], Y[1] - X[1]
            n_ = math.hypot(dx, dy)
            if n_ < span * 0.02:
                return
            px, py = -dy / n_, dx / n_
            wx, wy = weg_von if weg_von is not None else (mx, my)
            aussen = (((X[0] + Y[0]) / 2.0 - wx) * px +
                      ((X[1] + Y[1]) / 2.0 - wy) * py)
            Visualizer._mass_linie(ax, X, Y, txt, span, belegt,
                                   farbe='#0369a1', fs=6.8, grund=grund,
                                   stufen=6, linien=mlin,
                                   vorzug=1.0 if aussen >= 0 else -1.0)

        for X, Y, txt in kanten:
            masz(X, Y, txt, 0.075)
        # Der Rohrweg gehoert ans Rohr, nicht auf den Rahmen.
        masz(rohr[0], rohr[1], "Rohrweg  %.0f" % vers["travel"], 0.026,
             weg_von=fuss)

    @staticmethod
    def _part_symbol(ax, part, a, b, mid, u, p, s, ends=None):
        """Formteilsymbol. a/b = Anfang/Ende des Bauteils, mid = Mitte,
        u = Richtung, p = quer dazu (alles in der Iso-Ebene)."""
        col = '#b91c1c'

        def pos(base, ai, bi):
            return (base[0] + u[0] * ai * s + p[0] * bi * s,
                    base[1] + u[1] * ai * s + p[1] * bi * s)

        def seg(base, a1, b1, a2, b2, lw=2.6, c=col):
            q1, q2 = pos(base, a1, b1), pos(base, a2, b2)
            ax.plot([q1[0], q2[0]], [q1[1], q2[1]], color=c, lw=lw,
                    zorder=6, solid_capstyle='round')

        def bar(base, ai, half=1.0, lw=2.6, c=col):
            seg(base, ai, -half, ai, half, lw, c)

        def spann(f, bi):
            """Punkt bei Anteil f der Bauteillaenge, bi quer (in s-Einheiten).

            Klappe und Demontagestueck werden ueber ihre **tatsaechliche**
            Laenge gezeichnet - ein Symbol fester Groesse schwebt sonst als
            Kloetzchen mitten im Bauteil. Ist das Bauteil aber kuerzer als das
            Symbol breit ist (eine Zwischenflanschklappe baut nur wenige
            Zentimeter), faellt die Zeichnung in sich zusammen; dann wird ab
            der Mitte auf die Symbolbreite aufgezogen.
            """
            lang = math.hypot(b[0] - a[0], b[1] - a[1])
            mind = s * 2.0
            if lang < mind:
                q = (mid[0] + u[0] * (f - 0.5) * mind,
                     mid[1] + u[1] * (f - 0.5) * mind)
                return (q[0] + p[0] * bi * s, q[1] + p[1] * bi * s)
            return (a[0] + (b[0] - a[0]) * f + p[0] * bi * s,
                    a[1] + (b[1] - a[1]) * f + p[1] * bi * s)

        def linie(q1, q2, lw=2.2, c=col):
            ax.plot([q1[0], q2[0]], [q1[1], q2[1]], color=c, lw=lw, zorder=6,
                    solid_capstyle='round')

        def tri(base, a_base, a_tip, half):
            b1, b2 = pos(base, a_base, -half), pos(base, a_base, half)
            tp = pos(base, a_tip, 0.0)
            ax.fill([b1[0], b2[0], tp[0]], [b1[1], b2[1], tp[1]],
                    facecolor='white', edgecolor=col, lw=1.8,
                    joinstyle='miter', zorder=6)

        if part == "Blindflansch":
            bar(mid, -0.35)
            bar(mid, 0.35, 0.75, 4.0)                    # geschlossener Ruecken
        elif part in ("Armatur geschweisst", "Armatur mit Flanschen"):
            tri(mid, -1.05, 0.0, 0.72)
            tri(mid, 1.05, 0.0, 0.72)
            seg(mid, 0.0, 0.0, 0.0, 1.6, lw=1.6)         # Spindel
            seg(mid, -0.5, 1.6, 0.5, 1.6, lw=2.2)        # Handrad
        elif part == "Klappe":
            # Klappensymbol aus den drei Teilen, ueber die sich die Quellen
            # einig sind: Gehaeusestrich, eine SCHRAEGE als Scheibe und ein
            # GEFUELLTER Kreis fuer die Welle. Bewusst ohne die beiden
            # Dreiecke des Schiebers - sonst sieht man auf dem Blatt nicht,
            # welche Armatur eingebaut wird. (Auf mancher Iso wird jede
            # Armatur als Doppeldreieck gezeichnet und die Art nur in der
            # Stueckliste genannt; hier soll man es an der Skizze sehen.)
            #
            # Das Symbol hat feste Groesse und sitzt in der Mitte. Zoege man es
            # ueber die wahre Baulaenge, waere die Scheibe fast laengs zum Rohr
            # und die Klappe nicht mehr zu erkennen - eine Zwischenflansch-
            # klappe ist im Verhaeltnis zum Rohr sehr kurz und sehr breit.
            bar(mid, -0.85, 0.95, lw=2.4)
            bar(mid, 0.85, 0.95, lw=2.4)
            seg(mid, -0.85, 0.90, 0.85, -0.90, lw=2.0)      # Scheibe
            q = pos(mid, 0.0, 0.0)
            ax.plot(q[0], q[1], 'o', color=col, ms=5.0, zorder=7)   # Welle
        elif part == "Demontagestueck":
            # Einbaustueck: Flanschblatt an beiden Enden, dazwischen die
            # Schiebemuffe, aussen die durchgehenden Zuganker.
            bar(a, 0.0, 1.1)
            bar(b, 0.0, 1.1)
            for vz in (-1.0, 1.0):
                linie(spann(0.0, 0.95 * vz), spann(1.0, 0.95 * vz), lw=1.2)
                linie(spann(0.30, 0.5 * vz), spann(0.75, 0.5 * vz), lw=2.4)
            linie(spann(0.30, -0.5), spann(0.30, 0.5), lw=1.6)
            linie(spann(0.75, -0.5), spann(0.75, 0.5), lw=1.6)
        elif part == "Montagestoss":
            ax.plot(mid[0], mid[1], 'o', mfc='white', mec=col, mew=2.0,
                    ms=7, zorder=6)
        elif part == "Reduzierung":
            for base, half in ((a, 1.0), (b, 0.55)):
                bar(base, 0.0, half, 2.0, '#64748b')
        # Bogen / Rohr / T-Stueck: kein eigenes Symbol


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
