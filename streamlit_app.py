import streamlit as st
import pandas as pd
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.path as mpath
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. DESIGN & EINSTELLUNGEN
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Rohrbau Profi", page_icon="🛠️", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #FFFFFF; color: #333333; }
    h1, h2, h3, h4, p, div, label, span, .stMarkdown { color: #000000 !important; }
    .stNumberInput label, .stSelectbox label, .stSlider label, .stTextInput label, .stRadio label { font-weight: bold; }
    .result-box { background-color: #F4F6F7; padding: 10px; border-radius: 4px; border-left: 5px solid #2980B9; margin-bottom: 5px; border: 1px solid #ccc; font-size: 0.95rem; }
    .highlight-box { background-color: #E9F7EF; padding: 15px; border-radius: 4px; border-left: 5px solid #27AE60; text-align: center; font-size: 1.2rem; font-weight: bold; margin-top: 15px; border: 1px solid #ccc; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .flansch-box { background-color: #FDEDEC; padding: 8px; border-radius: 4px; border-left: 5px solid #C0392B; font-size: 0.9rem; margin-bottom: 10px; border: 1px solid #ccc; }
    .info-box-blue { background-color: #D6EAF8; padding: 10px; border-radius: 4px; border-left: 5px solid #3498DB; font-size: 0.9rem; margin-top: 10px; color: #154360 !important; }
    .stDataFrame { border: 1px solid #000; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# SESSION STATE (Dein Speicher im Browser)
# -----------------------------------------------------------------------------
if 'rohrbuch' not in st.session_state:
    st.session_state.rohrbuch = []

# -----------------------------------------------------------------------------
# ZEICHNEN-FUNKTIONEN
# -----------------------------------------------------------------------------
def draw_pipe_curve(ax, p_start, p_corner, p_end, color='#2C3E50', lw=3):
    offset = 15 
    def get_point_on_line(p1, p2, dist_from_p2):
        dx = p1[0] - p2[0]
        dy = p1[1] - p2[1]
        length = math.hypot(dx, dy)
        if length == 0: return p2
        factor = dist_from_p2 / length
        return (p2[0] + dx*factor, p2[1] + dy*factor)

    arc_start = get_point_on_line(p_start, p_corner, offset)
    arc_end = get_point_on_line(p_end, p_corner, offset)
    
    ax.plot([p_start[0], arc_start[0]], [p_start[1], arc_start[1]], color=color, lw=lw, solid_capstyle='round')
    verts = [arc_start, p_corner, arc_end]
    codes = [mpath.Path.MOVETO, mpath.Path.CURVE3, mpath.Path.CURVE3]
    path = mpath.Path(verts, codes)
    patch = patches.PathPatch(path, facecolor='none', edgecolor=color, lw=lw, capstyle='round')
    ax.add_patch(patch)
    ax.plot([arc_end[0], p_end[0]], [arc_end[1], p_end[1]], color=color, lw=lw, solid_capstyle='round')
    ax.scatter([arc_start[0], arc_end[0]], [arc_start[1], arc_end[1]], color='white', edgecolors=color, s=15, zorder=5, lw=1)

def zeichne_iso_2d(h, l, winkel, passstueck):
    fig, ax = plt.subplots(figsize=(3.5, 2))
    iso_angle = math.radians(30)
    vx, vy = math.cos(iso_angle), math.sin(iso_angle)
    p1 = (0,0)
    p2 = (50*vx, 50*vy)
    p3 = (p2[0] + l*vx, p2[1] + l*vy + h)
    p4 = (p3[0] + 50*vx, p3[1] + 50*vy)
    
    draw_pipe_curve(ax, p1, p2, ((p2[0]+p3[0])/2, (p2[1]+p3[1])/2))
    draw_pipe_curve(ax, ((p2[0]+p3[0])/2, (p2[1]+p3[1])/2), p3, p4)
    
    corner = (p3[0], p3[1]-h)
    ax.plot([p2[0], corner[0]], [p2[1], corner[1]], 'k--', lw=0.5, color='grey')
    ax.plot([corner[0], p3[0]], [corner[1], p3[1]], 'k--', lw=0.5, color='grey')
    
    ax.text(corner[0]+3, p3[1]-h/2, f"H={h}", fontsize=7, color='#C0392B', fontweight='bold')
    ax.text((p2[0]+corner[0])/2, (p2[1]+corner[1])/2 - 12, f"L={l}", fontsize=7, color='#C0392B', fontweight='bold', ha='center')
    mid = ((p2[0]+p3[0])/2, (p2[1]+p3[1])/2)
    ax.text(mid[0]-5, mid[1]+5, f"Säge: {round(passstueck,1)}", fontsize=8, color='#27AE60', fontweight='bold', ha='right', bbox=dict(facecolor='white', alpha=0.9, edgecolor='none', pad=1))
    ax.set_aspect('equal'); ax.axis('off')
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    return fig

def zeichne_iso_raum(s, h, l, diag_raum, passstueck):
    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    angle = math.radians(30)
    cx, cy = math.cos(angle), math.sin(angle)
    max_val = max(s, h, l, 1)
    scale = 100 / max_val 
    S, H, L = s*scale, h*scale, l*scale
    p_run = (L * cx, L * cy)
    p_spread = (S * cx, -S * cy)
    p_end_floor = (p_run[0] + p_spread[0], p_run[1] + p_spread[1])
    
    ax.plot([0, p_run[0]], [0, p_run[1]], '--', color='#BDC3C7', lw=0.8)
    ax.plot([0, p_spread[0]], [0, p_spread[1]], '--', color='#BDC3C7', lw=0.8)
    ax.plot([p_run[0], p_end_floor[0]], [p_run[1], p_end_floor[1]], '--', color='#BDC3C7', lw=0.8)
    ax.plot([p_spread[0], p_end_floor[0]], [p_spread[1], p_end_floor[1]], '--', color='#BDC3C7', lw=0.8)
    ax.plot([0, 0], [0, H], '--', color='#BDC3C7', lw=0.8)
    ax.plot([p_end_floor[0], p_end_floor[0]], [p_end_floor[1], p_end_floor[1]+H], '--', color='#BDC3C7', lw=0.8)
    ax.plot([0, p_end_floor[0]], [H, p_end_floor[1]+H], '-', color='#BDC3C7', lw=0.5, alpha=0.5) 
    ax.plot([0, p_end_floor[0]], [0, p_end_floor[1]+H], color='#2C3E50', lw=3, solid_capstyle='round')
    ax.scatter([0, p_end_floor[0]], [0, p_end_floor[1]+H], color='white', edgecolors='#2C3E50', s=30, zorder=10)
    
    ax.text(p_run[0]/2, p_run[1]/2 + 5, f"L={l}", fontsize=7, color='grey', ha='right')
    ax.text(p_spread[0]/2, p_spread[1]/2 - 5, f"S={s}", fontsize=7, color='grey', ha='left')
    ax.text(-5, H/2, f"H={h}", fontsize=7, color='grey', ha='right')
    mid_x = p_end_floor[0] / 2
    mid_y = (p_end_floor[1] + H) / 2
    ax.text(mid_x, mid_y + 8, f"Säge: {round(passstueck,1)}", fontsize=8, color='#27AE60', fontweight='bold', ha='center', bbox=dict(facecolor='white', alpha=0.9, edgecolor='none', pad=1))
    ax.set_aspect('equal'); ax.axis('off')
    plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
    return fig

# -----------------------------------------------------------------------------
# 2. DATENBANK
# -----------------------------------------------------------------------------
data = {
    'DN':           [25, 32, 40, 50, 65, 80, 100, 125, 150, 200, 250, 300, 350, 400, 450, 500, 600, 700, 800, 900, 1000, 1200, 1400, 1600],
    'D_Aussen':     [33.7, 42.4, 48.3, 60.3, 76.1, 88.9, 114.3, 139.7, 168.3, 219.1, 273.0, 323.9, 355.6, 406.4, 457.0, 508.0, 610.0, 711.0, 813.0, 914.0, 1016.0, 1219.0, 1422.0, 1626.0],
    'Radius_BA3':   [38, 48, 57, 76, 95, 114, 152, 190, 229, 305, 381, 457, 533, 610, 686, 762, 914, 1067, 1219, 1372, 1524, 1829, 2134, 2438],
    'T_Stueck_H':   [25, 32, 38, 51, 64, 76, 105, 124, 143, 178, 216, 254, 279, 305, 343, 381, 432, 521, 597, 673, 749, 889, 1029, 1168],
    'Red_Laenge_L': [38, 50, 64, 76, 89, 89, 102, 127, 140, 152, 178, 203, 330, 356, 381, 508, 508, 610, 660, 711, 800, 900, 1000, 1100], 
    'Flansch_b_16': [38, 40, 42, 45, 45, 50, 52, 55, 55, 62, 70, 78, 82, 85, 85, 90, 95, 105, 115, 125, 135, 155, 175, 195],
    'LK_k_16':      [85, 100, 110, 125, 145, 160, 180, 210, 240, 295, 355, 410, 470, 525, 585, 650, 770, 840, 950, 1050, 1160, 1380, 1590, 1820],
    'Schraube_M_16':["M12", "M16", "M16", "M16", "M16", "M16", "M16", "M16", "M20", "M20", "M24", "M24", "M24", "M27", "M27", "M30", "M33", "M33", "M36", "M36", "M39", "M45", "M45", "M52"],
    'L_Fest_16':    [55, 60, 60, 65, 65, 70, 70, 75, 80, 85, 100, 110, 110, 120, 130, 130, 150, 160, 170, 180, 190, 220, 240, 260],
    'L_Los_16':     [60, 65, 65, 70, 70, 75, 80, 85, 90, 100, 115, 125, 130, 140, 150, 150, 170, 180, 190, 210, 220, 250, 280, 300],
    'Lochzahl_16':  [4, 4, 4, 4, 4, 8, 8, 8, 8, 12, 12, 12, 16, 16, 20, 20, 20, 24, 24, 28, 28, 32, 36, 40],
    'Flansch_b_10': [38, 40, 42, 45, 45, 50, 52, 55, 55, 62, 70, 78, 82, 85, 85, 90, 95, 105, 115, 125, 135, 155, 175, 195],
    'LK_k_10':      [85, 100, 110, 125, 145, 160, 180, 210, 240, 295, 350, 400, 460, 515, 565, 620, 725, 840, 950, 1050, 1160, 1380, 1590, 1820],
    'Schraube_M_10':["M12", "M16", "M16", "M16", "M16", "M16", "M16", "M16", "M20", "M20", "M20", "M20", "M20", "M24", "M24", "M24", "M27", "M27", "M30", "M30", "M33", "M36", "M39", "M45"],
    'L_Fest_10':    [55, 60, 60, 65, 65, 70, 70, 75, 80, 85, 90, 90, 90, 100, 110, 110, 120, 130, 140, 150, 160, 190, 210, 230],
    'L_Los_10':     [60, 65, 65, 70, 70, 75, 80, 85, 90, 100, 105, 105, 110, 120, 130, 130, 140, 150, 160, 170, 180, 210, 240, 260],
    'Lochzahl_10':  [4, 4, 4, 4, 4, 8, 8, 8, 8, 8, 12, 12, 16, 16, 20, 20, 20, 20, 24, 28, 28, 32, 36, 40]
}
df = pd.DataFrame(data)

# -----------------------------------------------------------------------------
# 3. SIDEBAR
# -----------------------------------------------------------------------------
st.sidebar.header("⚙️ Einstellungen")
selected_dn = st.sidebar.selectbox("Nennweite (DN)", df['DN'], index=8) 
selected_pn = st.sidebar.radio("Druckstufe", ["PN 16", "PN 10"], index=0)

row = df[df['DN'] == selected_dn].iloc[0]
standard_radius = float(row['Radius_BA3'])
suffix = "_16" if selected_pn == "PN 16" else "_10"
flansch_len = row[f'Flansch_b{suffix}'] 

# -----------------------------------------------------------------------------
# 4. HAUPTBEREICH
# -----------------------------------------------------------------------------
st.markdown("""<div class="small-info">ℹ️ Menü öffnen (Pfeil oben links) zum Ändern von DN/PN.</div>""", unsafe_allow_html=True)
st.title(f"Rohrbau Profi (DN {selected_dn})")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📋 Maße", "🔄 Bogen", "📏 Säge", "🔥 Stutzen", "📐 Etagen Berechnung", "📝 Rohrbuch"])

# --- TAB 1: DATENBLATT ---
with tab1:
    c1, c2 = st.columns(2)
    with c1:
        st.caption("Rohr & Formstücke")
        st.markdown(f"<div class='result-box'>Außen-Ø: <b>{row['D_Aussen']} mm</b></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='result-box'>Radius (3D): <b>{standard_radius} mm</b></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='result-box'>T-Stück (H): <b>{row['T_Stueck_H']} mm</b></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='result-box'>Reduzierung (L): <b>{row['Red_Laenge_L']} mm</b></div>", unsafe_allow_html=True)
    with c2:
        st.caption("Flansch")
        st.markdown(f"<div class='flansch-box'>Länge Flansch (H): <b>{flansch_len} mm</b></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='result-box'>Lochkreis: <b>{row[f'LK_k{suffix}']} mm</b></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='result-box'>Schrauben: <b>{row[f'Lochzahl{suffix}']}x {row[f'Schraube_M{suffix}']}</b></div>", unsafe_allow_html=True)
        
        # Normale Schraubenlängen (ohne Zusatz)
        l_fest = row[f'L_Fest{suffix}']
        l_los = row[f'L_Los{suffix}']
        
        st.markdown(f"<div class='result-box' style='font-size:0.9rem;'>Länge Fest-Fest: <b>{l_fest} mm</b></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='result-box' style='font-size:0.9rem; border-color: #8E44AD;'>Länge Fest-Los: <b>{l_los} mm</b></div>", unsafe_allow_html=True)

# --- TAB 2: BOGEN ---
with tab2:
    st.caption("Bogenberechnung (Radius 3D)")
    angle = st.slider("Winkel (°)", 0, 90, 45, 1, key="bogen_winkel")
    da = row['D_Aussen']
    aussen = round((standard_radius + (da/2)) * angle * (math.pi/180), 1)
    innen = round((standard_radius - (da/2)) * angle * (math.pi/180), 1)
    vorbau = round(standard_radius * math.tan(math.radians(angle/2)), 1)
    
    c1, c2 = st.columns(2)
    c1.markdown(f"<div class='result-box'>Rücken (Außen):<br><b>{aussen} mm</b></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='result-box'>Bauch (Innen):<br><b>{innen} mm</b></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='highlight-box'>Vorbau: {vorbau} mm</div>", unsafe_allow_html=True)

# --- TAB 3: SÄGE ---
with tab3:
    st.caption("Einfaches Passstück")
    iso_mass = st.number_input("Gesamtmaß (Iso)", value=1000)
    spalt = st.number_input("Wurzelspalt (Gesamt)", value=6)
    
    # Text-Input für Abzüge mit Addier-Funktion
    abz_str = st.text_input("Abzüge (z.B. 52+30)", value="0", help="Du kannst mehrere Werte mit '+' eingeben")
    try:
        clean_str = abz_str.replace(',', '.')
        abz_parts = [float(x) for x in clean_str.split('+') if x.strip() != ""]
        abz = sum(abz_parts)
    except:
        abz = 0
        st.error("Bitte nur Zahlen!")

    aktueller_winkel = st.session_state.get("bogen_winkel", 45)
    abzug_90 = int(standard_radius)
    abzug_custom = int(round(standard_radius * math.tan(math.radians(aktueller_winkel/2)), 0))
    
    st.markdown(f"""
    <div class='info-box-blue'>
        <b>Infos für Abzüge:</b><br>
        • Flansch Bauhöhe: <b>{flansch_len} mm</b><br>
        • Bogen 90° (Vorbau): <b>{abzug_90} mm</b><br>
        • Bogen {aktueller_winkel}° (Vorbau aus Tab Bogen): <b>{abzug_custom} mm</b>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"<div class='highlight-box'>Sägelänge: {iso_mass - abz - spalt} mm</div>", unsafe_allow_html=True)

# --- TAB 4: STUTZEN ---
with tab4:
    st.caption("Stutzen Schablone (16er Teilung)")
    dn_stutzen = st.selectbox("DN Stutzen", df['DN'], index=6)
    dn_haupt = st.selectbox("DN Hauptrohr", df['DN'], index=9)
    if dn_stutzen > dn_haupt:
        st.error("Stutzen zu groß!")
    else:
        r_k = df[df['DN']==dn_stutzen].iloc[0]['D_Aussen']/2
        R_g = df[df['DN']==dn_haupt].iloc[0]['D_Aussen']/2
        res = []
        for a in [0, 22.5, 45, 67.5, 90, 112.5, 135, 157.5, 180]:
            umfang = round(r_k*2*math.pi*(a/360), 1)
            tiefe = round(R_g - math.sqrt(R_g**2 - (r_k*math.sin(math.radians(a)))**2), 1)
            res.append([f"{a}°", f"{umfang}", f"{tiefe}"])
        st.table(pd.DataFrame(res, columns=["Winkel", "Umfang", "Tiefe"]))

# --- TAB 5: ETAGEN BERECHNUNG ---
with tab5:
    iso_mode = st.radio("Berechnungsart wählen:", 
             ["2D Einfache Etage", "3D Raum-Etage (Kastenmaß)", "3D Raum-Etage (Fix-Winkel)"], 
             horizontal=True)
    
    st.markdown("---")
    spalt_iso = st.number_input("Wurzelspalt (Gesamt)", value=6, key="sp_iso")

    if iso_mode == "2D Einfache Etage":
        c1, c2 = st.columns(2)
        h = c1.number_input("Höhe H (Versatz)", value=300)
        l = c2.number_input("Länge L (Gerade)", value=400)
        
        if l > 0:
            winkel = math.degrees(math.atan(h/l))
            diag = math.sqrt(h**2 + l**2)
            abzug = 2 * (standard_radius * math.tan(math.radians(winkel/2)))
            saege = diag - abzug - spalt_iso
            
            st.info(f"Winkel: {round(winkel,1)}° | Mitte-Mitte: {round(diag,1)} mm")
            try: st.pyplot(zeichne_iso_2d(h, l, winkel, saege), use_container_width=False)
            except: pass
            st.markdown(f"<div class='highlight-box'>Sägelänge: {round(saege,1)} mm</div>", unsafe_allow_html=True)

    elif iso_mode == "3D Raum-Etage (Kastenmaß)":
        c1, c2, c3 = st.columns(3)
        s = c1.number_input("Seite (Spread)", value=200)
        h = c2.number_input("Höhe (Rise)", value=300)
        l = c3.number_input("Länge (Roll)", value=400)
        
        diag_raum = math.sqrt(s**2 + h**2 + l**2)
        versatz_total = math.sqrt(s**2 + h**2)
        if l > 0:
            winkel_raum = math.degrees(math.atan(versatz_total / l))
        else:
            winkel_raum = 90
            
        abzug = 2 * (standard_radius * math.tan(math.radians(winkel_raum/2)))
        saege = diag_raum - abzug - spalt_iso
        
        st.info(f"Benötigter Bogen: {round(winkel_raum,1)}° | Diagonale: {round(diag_raum,1)} mm")
        try: st.pyplot(zeichne_iso_raum(s, h, l, diag_raum, saege), use_container_width=False)
        except: pass
        st.markdown(f"<div class='highlight-box'>Sägelänge: {round(saege,1)} mm</div>", unsafe_allow_html=True)

    elif iso_mode == "3D Raum-Etage (Fix-Winkel)":
        c1, c2 = st.columns(2)
        s = c1.number_input("Seite (Spread)", value=200)
        h = c2.number_input("Höhe (Rise)", value=300)
        fix_winkel = st.selectbox("Gewünschter Bogen", [30, 45, 60], index=1)
        
        versatz_total = math.sqrt(s**2 + h**2)
        calc_l = versatz_total / math.tan(math.radians(fix_winkel))
        diag_raum = math.sqrt(s**2 + h**2 + calc_l**2)
        
        abzug = 2 * (standard_radius * math.tan(math.radians(fix_winkel/2)))
        saege = diag_raum - abzug - spalt_iso
        
        st.write(f"Erforderliche Länge (Roll): **{round(calc_l,1)} mm**")
        st.info(f"Bogen: {fix_winkel}° | Diagonale: {round(diag_raum,1)} mm")
        try: st.pyplot(zeichne_iso_raum(s, h, calc_l, diag_raum, saege), use_container_width=False)
        except: pass
        st.markdown(f"<div class='highlight-box'>Sägelänge: {round(saege,1)} mm</div>", unsafe_allow_html=True)

# --- TAB 6: ROHRBUCH (LOKAL) ---
with tab6:
    st.subheader("Digitales Rohrbuch (Lokal)")
    st.caption("Erfasse Nähte und Material für die Dokumentation.")
    
    # EINGABE FORMULAR
    with st.form("rohrbuch_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        iso_nr = c1.text_input("ISO-Nummer")
        naht_nr = c2.text_input("Naht-Nr.")
        schweisser = c3.text_input("Schweißer (Kürzel)")
        
        c4, c5, c6 = st.columns(3)
        bauteil = c4.text_input("Bauteil / Spool", value="Rohr")
        charge = c5.text_input("Charge / APZ-Nr.")
        laenge_input = c6.number_input("Länge (mm)", value=0)
        
        submitted = st.form_submit_button("Eintrag hinzufügen")
        
        if submitted:
            eintrag = {
                "Zeit": datetime.now().strftime("%H:%M"),
                "ISO": iso_nr,
                "Naht": naht_nr,
                "DN": selected_dn,
                "Bauteil": bauteil,
                "Länge": laenge_input,
                "Charge_APZ": charge,
                "Schweißer": schweisser
            }
            st.session_state.rohrbuch.append(eintrag)
            st.success("Gespeichert!")

    # TABELLE ANZEIGEN & LÖSCHEN
    if len(st.session_state.rohrbuch) > 0:
        st.markdown("---")
        
        with st.expander("Einträge verwalten / löschen"):
            df_log = pd.DataFrame(st.session_state.rohrbuch)
            delete_indices = st.multiselect(
                "Wähle Einträge zum Löschen:",
                options=df_log.index,
                format_func=lambda i: f"Zeile {i+1}: Naht {df_log.iloc[i]['Naht']} (ISO {df_log.iloc[i]['ISO']})"
            )
            
            if st.button("Ausgewählte löschen 🗑️"):
                for i in sorted(delete_indices, reverse=True):
                    del st.session_state.rohrbuch[i]
                st.rerun()

        if len(st.session_state.rohrbuch) > 0:
            df_show = pd.DataFrame(st.session_state.rohrbuch)
            st.dataframe(df_show, use_container_width=True)
            
            csv = df_show.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="💾 Liste als CSV herunterladen",
                data=csv,
                file_name=f'rohrbuch_{datetime.now().strftime("%Y-%m-%d")}.csv',
                mime='text/csv',
            )
    else:
        st.info("Noch keine Einträge heute.")
