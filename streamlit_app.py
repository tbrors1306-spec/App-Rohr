import streamlit as st
import pandas as pd
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import sqlite3
from datetime import datetime
from io import BytesIO

# -----------------------------------------------------------------------------
# 1. DESIGN & CONFIG
# -----------------------------------------------------------------------------
st.set_page_config(page_title="PipeCraft V15.3", page_icon="🏗️", layout="wide")

st.markdown("""
<style>
    /* Globaler Look */
    .stApp { background-color: #f8f9fa; color: #0f172a; }
    h1 { font-family: 'Helvetica Neue', sans-serif; color: #1e293b !important; font-weight: 800; letter-spacing: -1px; }
    
    /* Metriken */
    div[data-testid="stMetric"] {
        background-color: #ffffff; border: 1px solid #e2e8f0; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Blaue Info-Karte */
    .result-card-blue {
        background-color: #eff6ff; padding: 20px; border-radius: 12px; border-left: 6px solid #3b82f6;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 15px; color: #1e3a8a; font-size: 1rem;
    }
    
    /* Grüne Ergebnis-Karte */
    .result-card-green {
        background: linear-gradient(to right, #f0fdf4, #ffffff); padding: 25px; border-radius: 12px; border-left: 8px solid #22c55e;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08); margin-bottom: 15px; text-align: center; font-size: 1.8rem; font-weight: 800; color: #14532d;
    }
    
    /* Detail Boxen */
    .detail-box {
        background-color: #f1f5f9; border: 1px solid #cbd5e1; padding: 10px; border-radius: 6px; 
        text-align: center; font-size: 0.9rem; color: #334155; height: 100%; display: flex; flex-direction: column; justify-content: center;
    }
    .detail-value { font-weight: 700; color: #0f172a; font-size: 1.1rem; margin-top: 4px; }
    
    .crew-hint {
        background-color: #fff7ed; border: 1px solid #ffedd5; color: #9a3412; padding: 10px; border-radius: 8px; font-size: 0.9rem; margin-top: 5px; margin-bottom: 15px;
    }

    div.stButton > button { width: 100%; border-radius: 8px; font-weight: 600; border: 1px solid #cbd5e1; transition: 0.2s; }
    div.stButton > button:hover { border-color: #3b82f6; color: #3b82f6; }
    .stNumberInput input, .stSelectbox div[data-baseweb="select"], .stTextInput input { border-radius: 8px; border: 1px solid #cbd5e1; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. DATENBANK LOGIK
# -----------------------------------------------------------------------------
DB_NAME = "pipecraft.db"

def init_db():
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rohrbuch (id INTEGER PRIMARY KEY AUTOINCREMENT, iso TEXT, naht TEXT, datum TEXT, dimension TEXT, bauteil TEXT, laenge REAL, charge TEXT, schweisser TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS kalkulation (id INTEGER PRIMARY KEY AUTOINCREMENT, typ TEXT, info TEXT, menge REAL, zeit_min REAL, kosten REAL, mat_text TEXT)''')
    conn.commit(); conn.close()

def add_rohrbuch(iso, naht, datum, dim, bauteil, laenge, charge, schweisser):
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute('INSERT INTO rohrbuch (iso, naht, datum, dimension, bauteil, laenge, charge, schweisser) VALUES (?,?,?,?,?,?,?,?)', (iso, naht, datum, dim, bauteil, laenge, charge, schweisser))
    conn.commit(); conn.close()

def add_kalkulation(typ, info, menge, zeit, kosten, mat):
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute('INSERT INTO kalkulation (typ, info, menge, zeit_min, kosten, mat_text) VALUES (?,?,?,?,?,?)', (typ, info, menge, zeit, kosten, mat))
    conn.commit(); conn.close()

def get_rohrbuch_df():
    conn = sqlite3.connect(DB_NAME); df = pd.read_sql_query("SELECT * FROM rohrbuch", conn); conn.close(); return df

def get_kalk_df():
    conn = sqlite3.connect(DB_NAME); df = pd.read_sql_query("SELECT * FROM kalkulation", conn); conn.close(); return df

def delete_rohrbuch_id(entry_id):
    conn = sqlite3.connect(DB_NAME); c = conn.cursor(); c.execute("DELETE FROM rohrbuch WHERE id=?", (entry_id,)); conn.commit(); conn.close()

def delete_kalk_id(entry_id):
    conn = sqlite3.connect(DB_NAME); c = conn.cursor(); c.execute("DELETE FROM kalkulation WHERE id=?", (entry_id,)); conn.commit(); conn.close()

def delete_all(table):
    conn = sqlite3.connect(DB_NAME); c = conn.cursor(); c.execute(f"DELETE FROM {table}"); conn.commit(); conn.close()

init_db()

# -----------------------------------------------------------------------------
# 3. DATEN & HELPER
# -----------------------------------------------------------------------------
schrauben_db = { "M12": [18, 60], "M16": [24, 130], "M20": [30, 250], "M24": [36, 420], "M27": [41, 600], "M30": [46, 830], "M33": [50, 1100], "M36": [55, 1400], "M39": [60, 1800], "M45": [70, 2700], "M52": [80, 4200] }
ws_liste = [2.0, 2.3, 2.6, 2.9, 3.2, 3.6, 4.0, 4.5, 5.0, 5.6, 6.3, 7.1, 8.0, 8.8, 10.0, 11.0, 12.5, 14.2, 16.0]
wandstaerken_std = { 25: 3.2, 32: 3.6, 40: 3.6, 50: 3.9, 65: 5.2, 80: 5.5, 100: 6.0, 125: 6.6, 150: 7.1, 200: 8.2, 250: 9.3, 300: 9.5, 350: 9.5, 400: 9.5, 450: 9.5, 500: 9.5 }

def get_schrauben_info(gewinde): return schrauben_db.get(gewinde, ["?", "?"])
def parse_abzuege(text):
    try:
        clean_text = text.replace(",", ".").replace(" ", "")
        if not all(c in "0123456789.+-*/" for c in clean_text): return 0.0
        return float(pd.eval(clean_text))
    except: return 0.0

def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Kalkulation')
    return output.getvalue()

# --- ZEICHNEN ---
def zeichne_passstueck(iso_mass, abzug1, abzug2, saegelaenge):
    fig, ax = plt.subplots(figsize=(6, 1.8))
    rohr_farbe, abzug_farbe, fertig_farbe, linie_farbe = '#F1F5F9', '#EF4444', '#10B981', '#334155'
    y_mitte, rohr_hoehe = 50, 40
    ax.add_patch(patches.Rectangle((0, y_mitte - rohr_hoehe/2), iso_mass, rohr_hoehe, facecolor=rohr_farbe, edgecolor=linie_farbe, hatch='///', alpha=0.3))
    if abzug1 > 0:
        ax.add_patch(patches.Rectangle((0, y_mitte - rohr_hoehe/2), abzug1, rohr_hoehe, facecolor=abzug_farbe, alpha=0.5))
    if abzug2 > 0:
        start_abzug2 = iso_mass - abzug2
        ax.add_patch(patches.Rectangle((start_abzug2, y_mitte - rohr_hoehe/2), abzug2, rohr_hoehe, facecolor=abzug_farbe, alpha=0.5))
    start_saege = abzug1
    ax.add_patch(patches.Rectangle((start_saege, y_mitte - rohr_hoehe/2), saegelaenge, saegelaenge, facecolor=fertig_farbe, edgecolor=linie_farbe, linewidth=2))
    ax.set_xlim(-50, iso_mass + 50); ax.set_ylim(0, 100); ax.axis('off')
    return fig

def zeichne_iso_raum(s, h, l, diag_raum, passstueck, winkel_raum):
    fig, ax = plt.subplots(figsize=(5, 3.5))
    angle = math.radians(30); cx, cy = math.cos(angle), math.sin(angle)
    scale = 100 / max(s, h, l, 1)
    S, H, L = s*scale, h*scale, l*scale
    p_l = (L * cx, L * cy); p_ls = (p_l[0] + S * cx, p_l[1] - S * cy); p_end = (p_ls[0], p_ls[1] + H)
    ax.plot([0, p_l[0]], [0, p_l[1]], '--', color='#94a3b8', lw=1); ax.text(p_l[0]/2, p_l[1]/2+2, f"Roll: {l}", fontsize=8, color='#64748b')
    ax.plot([p_l[0], p_ls[0]], [p_l[1], p_ls[1]], '--', color='#94a3b8', lw=1); ax.text((p_l[0]+p_ls[0])/2, (p_l[1]+p_ls[1])/2-5, f"Spread: {s}", fontsize=8, color='#64748b')
    ax.plot([p_ls[0], p_end[0]], [p_ls[1], p_end[1]], '--', color='#94a3b8', lw=1); ax.text(p_end[0]+2, (p_ls[1]+p_end[1])/2, f"Rise: {h}", fontsize=8, color='#64748b')
    ax.plot([0, p_end[0]], [0, p_end[1]], color='#0f172a', lw=3, solid_capstyle='round')
    ax.scatter([0, p_end[0]], [0, p_end[1]], color='white', edgecolor='#0f172a', s=50, zorder=5)
    info_text = (f"Säge: {round(passstueck,1)} mm\nRaum-Winkel: {round(winkel_raum,1)}°")
    ax.text(p_end[0]/2, p_end[1]/2 + 15, info_text, color='#17202A', ha='center', fontsize=8, bbox=dict(facecolor='#f1f5f9', alpha=0.95, edgecolor='#cbd5e1', boxstyle='round,pad=0.5'))
    ax.set_aspect('equal'); ax.axis('off')
    return fig

def zeichne_iso_2d(h, l, winkel, passstueck):
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.plot([0, l], [0, h], color='#0f172a', linewidth=3, solid_capstyle='round')
    ax.plot([l, l], [0, h], color='#ef4444', linestyle='--', linewidth=1); ax.plot([0, l], [0, 0], color='#ef4444', linestyle='--', linewidth=1)
    ax.text(l + 5, h/2, f"H={h}", color='#ef4444', fontweight='bold', fontsize=9)
    ax.text(l/2, -20, f"L={l}", color='#ef4444', fontweight='bold', ha='center', fontsize=9)
    ax.text(l/2, h/2 + 20, f"Säge: {round(passstueck, 1)}", color='#16a34a', fontweight='bold', ha='right', fontsize=10)
    ax.set_aspect('equal'); ax.axis('off'); return fig

def zeichne_stutzen_abwicklung(df_coords):
    fig, ax = plt.subplots(figsize=(4.0, 2.0)); ax.plot(df_coords['Winkel_Raw'], df_coords['Tiefe (mm)'], color='#3b82f6', lw=2); ax.fill_between(df_coords['Winkel_Raw'], df_coords['Tiefe (mm)'], color='#eff6ff'); ax.axis('off'); return fig

# -----------------------------------------------------------------------------
# DATEN
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

st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2942/2942544.png", width=50) 
st.sidebar.markdown("### Menü")
selected_dn_global = st.sidebar.selectbox("Nennweite (Global)", df['DN'], index=8, key="global_dn") 
selected_pn = st.sidebar.radio("Druckstufe", ["PN 16", "PN 10"], index=0, key="global_pn") 

with st.sidebar.expander("💶 Preis-Datenbank (Editieren)", expanded=False):
    p_lohn = st.number_input("Stundensatz Lohn (€/h)", value=60.0, step=5.0, key="p_lohn")
    p_stahl_disc = st.number_input("Stahl-Scheibe (€/Stk)", value=2.50, step=0.5, key="p_stahl")
    p_dia_disc = st.number_input("Diamant-Scheibe (€/Stk)", value=45.00, step=5.0, key="p_dia")
    p_cel = st.number_input("Elektrode CEL 70 (€/Stk)", value=0.40, step=0.05, key="p_cel")
    p_draht = st.number_input("MAG/WIG Draht (€/kg)", value=15.00, step=1.0, key="p_draht")
    p_gas = st.number_input("Schweißgas (€/Liter)", value=0.05, step=0.01, key="p_gas")
    p_wks = st.number_input("WKS Manschette (€/Stk)", value=25.00, step=5.0, key="p_wks")
    p_kebu_in = st.number_input("Kebu 1.2 H (€/Rolle)", value=15.00, step=1.0, key="p_kebu1")
    p_kebu_out = st.number_input("Kebu PE 0.50 (€/Rolle)", value=12.00, step=1.0, key="p_kebu2")
    p_primer = st.number_input("Voranstrich K3 (€/Liter)", value=12.00, step=1.0, key="p_primer")

row = df[df['DN'] == selected_dn_global].iloc[0]
standard_radius = float(row['Radius_BA3'])
suffix = "_16" if selected_pn == "PN 16" else "_10"

st.title("PipeCraft")
st.caption(f"🔧 Aktive Konfiguration: DN {selected_dn_global} | {selected_pn} | Radius: {standard_radius} mm")

tab_buch, tab_werk, tab_proj, tab_info = st.tabs(["📘 Tabellenbuch", "📐 Werkstatt", "📝 Rohrbuch", "💰 Projekt"])

# -----------------------------------------------------------------------------
# TAB 1: TABELLENBUCH (Maße + Montage)
# -----------------------------------------------------------------------------
with tab_buch:
    st.subheader("Rohr & Formstücke")
    c1, c2 = st.columns(2)
    c1.markdown(f"<div class='result-card-blue'><b>Außen-Ø:</b> {row['D_Aussen']} mm</div>", unsafe_allow_html=True)
    c1.markdown(f"<div class='result-card-blue'><b>Radius (3D):</b> {standard_radius} mm</div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='result-card-blue'><b>T-Stück (H):</b> {row['T_Stueck_H']} mm</div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='result-card-blue'><b>Reduzierung (L):</b> {row['Red_Laenge_L']} mm</div>", unsafe_allow_html=True)
    
    st.divider()
    st.subheader(f"Flansch & Montage ({selected_pn})")
    
    schraube = row[f'Schraube_M{suffix}']
    sw, nm = get_schrauben_info(schraube)
    
    mc1, mc2 = st.columns(2)
    mc1.markdown(f"<div class='result-card-blue'><b>Blattstärke:</b> {row[f'Flansch_b{suffix}']} mm</div>", unsafe_allow_html=True)
    mc2.markdown(f"<div class='result-card-blue'><b>Schraube:</b> {row[f'Lochzahl{suffix}']}x {schraube}</div>", unsafe_allow_html=True)
    
    col_det1, col_det2 = st.columns(2)
    col_det1.markdown(f"<div class='detail-box'>Länge (Fest-Fest)<br><span class='detail-value'>{row[f'L_Fest{suffix}']} mm</span></div>", unsafe_allow_html=True)
    col_det2.markdown(f"<div class='detail-box'>Länge (Fest-Los)<br><span class='detail-value'>{row[f'L_Los{suffix}']} mm</span></div>", unsafe_allow_html=True)
    
    st.markdown(f"<div class='detail-box' style='margin-top:10px;'><b>Lochkreis:</b> {row[f'LK_k{suffix}']} mm | <b>SW:</b> {sw} mm | <b>{nm} Nm</b></div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TAB 2: WERKSTATT (Rechner-Kern)
# -----------------------------------------------------------------------------
with tab_werk:
    tool_mode = st.radio("Werkzeug wählen:", ["📏 Säge (Passstück)", "🔄 Bogen (Zuschnitt)", "🔥 Stutzen (Schablone)", "📐 Etage (Versatz)"], horizontal=True, label_visibility="collapsed", key="tool_mode_nav")
    st.divider()
    
    if "Säge" in tool_mode:
        st.subheader("Passstück Berechnung")
        c_s1, c_s2 = st.columns(2)
        iso_mass = c_s1.number_input("Gesamtmaß (Iso)", value=1000, step=10, key="saw_mass")
        spalt = c_s2.number_input("Wurzelspalt", value=4, key="saw_gap")
        abzug_input = st.text_input("Abzüge (z.B. 52+30)", value="0", key="saw_deduct")
        abzuege = parse_abzuege(abzug_input)
        
        saege_erg = iso_mass - spalt - abzuege
        st.markdown(f"<div class='result-card-green'>Sägelänge: {round(saege_erg, 1)} mm</div>", unsafe_allow_html=True)
        
        current_angle = st.session_state.get('bogen_winkel', 45)
        vorbau_custom = int(round(standard_radius * math.tan(math.radians(current_angle/2)), 0))
        
        with st.expander(f"ℹ️ Abzugsmaße (DN {selected_dn_global})", expanded=True):
            st.markdown(f"""
            * **Flansch:** {row[f'Flansch_b{suffix}']} mm
            * **Bogen 90°:** {standard_radius} mm
            * **Bogen {current_angle}° (Zuschnitt):** {vorbau_custom} mm
            * **T-Stück:** {row['T_Stueck_H']} mm
            * **Reduzierung:** {row['Red_Laenge_L']} mm
            """)

    elif "Bogen" in tool_mode:
        st.subheader("Bogen Zuschnitt")
        angle = st.slider("Winkel (°)", 0, 90, 45, key="bogen_winkel")
        vorbau = round(standard_radius * math.tan(math.radians(angle/2)), 1)
        aussen = round((standard_radius + (row['D_Aussen']/2)) * angle * (math.pi/180), 1)
        innen = round((standard_radius - (row['D_Aussen']/2)) * angle * (math.pi/180), 1)
        
        st.markdown(f"<div class='result-card-green'>Vorbau: {vorbau} mm</div>", unsafe_allow_html=True)
        b1, b2 = st.columns(2)
        b1.metric("Rücken (Außen)", f"{aussen} mm")
        b2.metric("Bauch (Innen)", f"{innen} mm")

    elif "Stutzen" in tool_mode:
        st.subheader("Stutzen Schablone")
        c_st1, c_st2 = st.columns(2)
        dn_stutzen = c_st1.selectbox("DN Stutzen", df['DN'], index=6, key="stutz_dn1")
        dn_haupt = c_st2.selectbox("DN Hauptrohr", df['DN'], index=9, key="stutz_dn2")
        if dn_stutzen > dn_haupt: st.error("Fehler: Stutzen > Hauptrohr")
        else:
            r_k = df[df['DN'] == dn_stutzen].iloc[0]['D_Aussen'] / 2
            r_g = df[df['DN'] == dn_haupt].iloc[0]['D_Aussen'] / 2
            plot_data = []; table_data = []
            for a in range(0, 361, 5): 
                t = r_g - math.sqrt(r_g**2 - (r_k * math.sin(math.radians(a)))**2); plot_data.append([a, t])
            for a in [0, 45, 90, 135, 180]:
                t = int(round(r_g - math.sqrt(r_g**2 - (r_k * math.sin(math.radians(a)))**2), 0))
                table_data.append([f"{a}°", t])
            c_res1, c_res2 = st.columns([1, 2])
            with c_res1: st.table(pd.DataFrame(table_data, columns=["Winkel", "Tiefe (mm)"]))
            with c_res2: st.pyplot(zeichne_stutzen_abwicklung(pd.DataFrame(plot_data, columns=["Winkel_Raw", "Tiefe (mm)"])))

    elif "Etage" in tool_mode:
        st.subheader("Etagen Berechnung")
        et_type = st.radio("Typ", ["2D (Einfach)", "3D (Kastenmaß)", "3D (Fix-Winkel)"], horizontal=True, key="et_type")
        spalt_et = st.number_input("Spalt", 4, key="et_gap")
        if "2D" in et_type:
            c1, c2 = st.columns(2); h = c1.number_input("Höhe H", 300, key="et2d_h"); l = c2.number_input("Länge L", 400, key="et2d_l")
            diag = math.sqrt(h**2 + l**2); winkel = math.degrees(math.atan(h/l)) if l>0 else 90
            abzug = 2 * (standard_radius * math.tan(math.radians(winkel/2)))
            st.markdown(f"<div class='result-card-green'>Säge: {round(diag - abzug - spalt_et, 1)} mm</div>", unsafe_allow_html=True)
            st.pyplot(zeichne_iso_2d(h, l, winkel, diag - abzug - spalt_et))
        elif "Kastenmaß" in et_type:
            c1, c2, c3 = st.columns(3); b = c1.number_input("Breite", 200, key="et3d_b"); h = c2.number_input("Höhe", 300, key="et3d_h"); l = c3.number_input("Länge", 400, key="et3d_l")
            diag = math.sqrt(h**2 + l**2 + b**2); spread = math.sqrt(b**2 + h**2)
            winkel = math.degrees(math.atan(spread/l)) if l>0 else 90
            abzug = 2 * (standard_radius * math.tan(math.radians(winkel/2)))
            st.markdown(f"<div class='result-card-green'>Säge: {round(diag - abzug - spalt_et, 1)} mm</div>", unsafe_allow_html=True)
            st.pyplot(zeichne_iso_raum(b, h, l, diag, diag - abzug - spalt_et, winkel))
        elif "Fix-Winkel" in et_type:
            c1, c2 = st.columns(2); b = c1.number_input("Breite", 200, key="etfix_b"); h = c2.number_input("Höhe", 300, key="etfix_h")
            fix_w = st.selectbox("Winkel", [15, 30, 45, 60, 90], index=2, key="etfix_w")
            spread = math.sqrt(b**2 + h**2); l_req = spread / math.tan(math.radians(fix_w))
            diag = math.sqrt(b**2 + h**2 + l_req**2); abzug = 2 * (standard_radius * math.tan(math.radians(fix_w/2)))
            st.info(f"Benötigte Länge L: {round(l_req, 1)} mm")
            st.markdown(f"<div class='result-card-green'>Säge: {round(diag - abzug - spalt_et, 1)} mm</div>", unsafe_allow_html=True)
            st.pyplot(zeichne_iso_raum(b, h, l_req, diag, diag - abzug - spalt_et, fix_w))

# -----------------------------------------------------------------------------
# TAB 3: ROHRBUCH (Dokumentation)
# -----------------------------------------------------------------------------
with tab_proj:
    st.subheader("Digitales Rohrbuch")
    with st.form("rb_form", clear_on_submit=False):
        c1, c2, c3 = st.columns(3)
        iso = c1.text_input("ISO")
        naht = c2.text_input("Naht")
        datum = c3.date_input("Datum")
        c4, c5, c6 = st.columns(3)
        dn_sel = c4.selectbox("Dimension", df['DN'], index=8, key="rb_dn_sel")
        bauteil = c5.selectbox("Bauteil", ["📏 Rohr", "⤵️ Bogen", "⭕ Flansch", "🔗 Muffe", "🔩 Nippel", "🪵 T-Stück", "🔻 Reduzierung"])
        laenge = c6.number_input("Länge", value=0)
        c7, c8 = st.columns(2)
        charge = c7.text_input("Charge")
        schweisser = c8.text_input("Schweißer")
        if st.form_submit_button("Speichern"):
            add_rohrbuch(iso, naht, datum.strftime("%d.%m.%Y"), f"DN {dn_sel}", bauteil, laenge, charge, schweisser)
            st.success("Gespeichert!")
    
    df_rb = get_rohrbuch_df()
    if not df_rb.empty:
        st.dataframe(df_rb, use_container_width=True)
        with st.expander("Zeile löschen"):
            opts = {f"ID {r['id']}: {r['iso']} {r['naht']}": r['id'] for i, r in df_rb.iterrows()}
            sel = st.selectbox("Wähle Eintrag:", list(opts.keys()), key="rb_del_sel")
            if st.button("Löschen", key="rb_del_btn"): delete_rohrbuch_id(opts[sel]); st.rerun()

# -----------------------------------------------------------------------------
# TAB 4: PROJEKT (Kalkulation + Summe)
# -----------------------------------------------------------------------------
with tab_info:
    st.subheader("Kosten & Zeit Management")
    calc_task = st.radio("Tätigkeit", ["Schweißen", "Schneiden", "Isolierung", "Regie"], horizontal=True, key="calc_mode")
    st.divider()
    
    if calc_task == "Schweißen":
        c1, c2, c3 = st.columns(3)
        k_dn = c1.selectbox("DN", df['DN'], index=8, key="kw_dn")
        k_ws = c2.selectbox("WS", ws_liste, index=6, key="kw_ws")
        k_verf = c3.selectbox("Verfahren", ["WIG", "E-Hand (CEL 70)", "WIG + E-Hand", "MAG"], key="kw_verf")
        
        c4, c5, c6 = st.columns(3)
        rec_pers = 2 if k_dn >= 300 else 1
        pers_count = c4.number_input("Schweißer", value=rec_pers, min_value=1, key="kw_pers")
        zma = c5.checkbox("Beton/ZMA", key="kw_zma")
        iso = c6.checkbox("Umhüllung", key="kw_iso")
        
        if k_dn < 100: team_text = "Empfehlung: 1 Schweißer (Alleinarbeit)"
        elif k_dn < 300: team_text = "Empfehlung: 1 Schweißer + 1 Vorrichter"
        else: team_text = "Empfehlung: 2 Schweißer + 1 Vorrichter (Simultan)"
        st.caption(f"ℹ️ {team_text}")

        zoll = k_dn / 25.0
        min_per_inch = 10.0 if k_verf == "WIG" else (3.5 if "CEL" in k_verf else 5.0)
        ws_factor = k_ws / 6.0 if k_ws > 6.0 else 1.0
        
        t_weld = zoll * min_per_inch * ws_factor
        t_fit = zoll * 2.5
        t_zma = zoll * 1.5 if zma else 0
        t_iso = zoll * 1.0 if iso else 0
        
        total_man_hours = t_weld + t_fit + t_zma + t_iso
        duration = total_man_hours / pers_count
        cost_time = (total_man_hours / 60) * p_lohn
        
        da = df[df['DN'] == k_dn].iloc[0]['D_Aussen']
        kg = (da * math.pi * k_ws**2 * 0.7 / 1000 * 7.85 / 1000) * 1.5
        cost_mat = 0; mat_text = ""
        
        if "CEL 70" in k_verf:
            st.markdown("##### ⚡ Elektroden")
            ec1, ec2, ec3 = st.columns(3)
            d_root = ec1.selectbox("Wurzel", ["2.5 mm", "3.2 mm", "4.0 mm"], index=1, key="cel_root")
            d_fill = ec2.selectbox("Füll", ["3.2 mm", "4.0 mm", "5.0 mm"], index=1, key="cel_fill")
            d_cap = ec3.selectbox("Deck", ["3.2 mm", "4.0 mm", "5.0 mm"], index=2, key="cel_cap")
            
            eff = {"2.5 mm": 0.008, "3.2 mm": 0.014, "4.0 mm": 0.025, "5.0 mm": 0.045}
            w_root = (da * math.pi * 15) / 1000 * 7.85 / 1000
            w_rest = max(0, kg - w_root)
            n_r = max(1, math.ceil(w_root/eff[d_root]))
            n_f = math.ceil((w_rest*0.65)/eff[d_fill])
            n_c = math.ceil((w_rest*0.35)/eff[d_cap])
            
            em1, em2, em3 = st.columns(3)
            em1.markdown(f"<div class='detail-box'>Wurzel<br><b>{n_r} Stk</b></div>", unsafe_allow_html=True)
            em2.markdown(f"<div class='detail-box'>Füll<br><b>{n_f} Stk</b></div>", unsafe_allow_html=True)
            em3.markdown(f"<div class='detail-box'>Deck<br><b>{n_c} Stk</b></div>", unsafe_allow_html=True)
            cost_mat = (n_r+n_f+n_c) * p_cel
            mat_text = f"CEL: {n_r}R/{n_f}F/{n_c}D"
        else:
            cost_mat = kg * p_draht + (total_man_hours/60 * 15 * p_gas)
            mat_text = f"{round(kg,1)} kg Draht"
            
        total_cost = cost_time + cost_mat
        
        st.markdown("---")
        m1, m2 = st.columns(2)
        m1.metric("⏱️ Dauer", f"{int(duration)} min")
        m2.metric("💰 Kosten", f"{round(total_cost, 2)} €")
        
        st.caption("Arbeitszeit Aufschlüsselung:")
        d1, d2, d3 = st.columns(3)
        d1.markdown(f"<div class='detail-box'>Vorrichten<br><b>{int(t_fit)} min</b></div>", unsafe_allow_html=True)
        d2.markdown(f"<div class='detail-box'>Schweißen<br><b>{int(t_weld)} min</b></div>", unsafe_allow_html=True)
        d3.markdown(f"<div class='detail-box'>Erschwernis<br><b>{int(t_zma + t_iso)} min</b></div>", unsafe_allow_html=True)
        st.markdown("---")
        
        col_anz, col_btn = st.columns([1, 2])
        anz = col_anz.number_input("Anzahl Nähte", 1, key="kw_anz")
        if col_btn.button("Hinzufügen", key="kw_add"):
            add_kalkulation("Schweißen", f"DN {k_dn} {k_verf}", anz, total_man_hours*anz, total_cost*anz, mat_text)
            st.success("Hinzugefügt!")
            st.rerun()

    elif calc_task == "Schneiden":
        c1, c2, c3, c4 = st.columns(4)
        c_dn = c1.selectbox("DN", df['DN'], index=8, key="cut_dn")
        c_ws = c2.selectbox("WS", ws_liste, index=6, key="cut_ws")
        disc = c3.selectbox("Scheibe", ["125mm", "180mm", "230mm"], key="cut_disc")
        zma = c4.checkbox("Beton?", key="cut_zma")
        
        zoll = c_dn / 25.0
        t_base = 0.5 if not zma else 1.5
        t_total = zoll * t_base
        t_cut = t_total * 0.7
        t_hand = t_total * 0.3
        
        da = df[df['DN']==c_dn].iloc[0]['D_Aussen']
        area = (math.pi*da) * c_ws
        cap = 3000 if "125" in disc else (6000 if "180" in disc else 10000)
        n_disc = math.ceil((area * (2.5 if zma else 1.0)) / cap)
        cost = (t_total/60 * p_lohn) + (n_disc * p_stahl_disc * (1 if "125" in disc else 2))
        
        cm1, cm2 = st.columns(2)
        cm1.metric("Zeit", f"{int(t_total)} min")
        cm2.metric("Kosten", f"{round(cost, 2)} €")
        
        st.caption("Details:")
        cd1, cd2, cd3 = st.columns(3)
        cd1.markdown(f"<div class='detail-box'>Sägen<br><b>{int(t_cut)} min</b></div>", unsafe_allow_html=True)
        cd2.markdown(f"<div class='detail-box'>Handling<br><b>{int(t_hand)} min</b></div>", unsafe_allow_html=True)
        cd3.markdown(f"<div class='detail-box'>Scheiben<br><b>{n_disc} Stk</b></div>", unsafe_allow_html=True)
        st.markdown("---")
        
        col_anz, col_btn = st.columns([1, 2])
        anz = col_anz.number_input("Anzahl", 1, label_visibility="collapsed", key="cut_anz")
        if col_btn.button("Hinzufügen", key="cut_add"):
            add_kalkulation("Schneiden", f"DN {c_dn} ({disc})", anz, t_total*anz, cost*anz, f"{n_disc}x Scheiben")
            st.rerun()

    elif calc_task == "Isolierung":
        sys = st.radio("System", ["WKS", "Zweiband", "Einband"], horizontal=True, key="iso_sys")
        c1, c2 = st.columns(2)
        i_dn = c1.selectbox("DN", df['DN'], index=8, key="iso_dn")
        i_anz = c2.number_input("Anzahl", 1, key="iso_anz")
        
        time = (20 + (i_dn * 0.07))
        t_prep = 20.0; t_app = i_dn * 0.07
        
        c_mat = 0; txt = ""
        if sys == "WKS": c_mat = p_wks; txt = f"1x WKS"
        else: 
            da = df[df['DN'] == i_dn].iloc[0]['D_Aussen']
            flaeche = (da * math.pi / 1000) * 0.5 
            if "Zweiband" in sys:
                r_in = math.ceil((flaeche * 2.2) / 1.0); r_out = math.ceil((flaeche * 2.2) / 1.5)
                c_mat = (r_in * p_kebu_in) + (r_out * p_kebu_out)
                txt = f"{r_in}x In / {r_out}x Out"
            else:
                roll = math.ceil((flaeche * 4.4) / 1.5)
                c_mat = roll * p_kebu_in
                txt = f"{roll}x Kebu"
            c_mat += (flaeche * 0.2 * p_primer)
        
        cost = (time/60 * p_lohn) + c_mat
        
        m1, m2 = st.columns(2)
        m1.metric("Zeit", f"{int(time)} min")
        m2.metric("Kosten", f"{round(cost, 2)} €")
        
        st.caption("Details:")
        id1, id2 = st.columns(2)
        id1.markdown(f"<div class='detail-box'>Vorbereitung<br><b>{int(t_prep)} min</b></div>", unsafe_allow_html=True)
        id2.markdown(f"<div class='detail-box'>Applikation<br><b>{int(t_app)} min</b></div>", unsafe_allow_html=True)
        st.markdown("---")
        
        if st.button("Hinzufügen", key="iso_add"):
            add_kalkulation("Iso", f"DN {i_dn} {sys}", i_anz, time*i_anz, cost*i_anz, txt); st.rerun()

    elif calc_task == "Regie":
        c1, c2 = st.columns(2)
        t = c1.number_input("Minuten", 60, key="reg_min")
        p = c2.number_input("Personen", 2, key="reg_pers")
        cost = (t/60 * p_lohn) * p
        st.metric("Kosten", f"{round(cost, 2)} €")
        st.caption(f"Arbeitszeit: {t} min")
        if st.button("Hinzufügen", key="reg_add"):
            add_kalkulation("Regie", f"{p} Pers.", 1, t, cost, "-"); st.rerun()

    # --- DAS DASHBOARD (SUMME) ---
    st.markdown("### 📊 Projekt Status")
    df_k = get_kalk_df()
    if not df_k.empty:
        sc1, sc2 = st.columns(2)
        sc1.metric("Gesamt-Kosten", f"{round(df_k['kosten'].sum(), 2)} €")
        sc2.metric("Gesamt-Stunden", f"{round(df_k['zeit_min'].sum()/60, 1)} h")
        
        st.dataframe(df_k, use_container_width=True)
        
        c_del, c_rst = st.columns(2)
        with c_del.expander("Zeile löschen"):
            opts = {f"ID {r['id']}: {r['typ']}": r['id'] for i, r in df_k.iterrows()}
            sel = st.selectbox("Wähle:", list(opts.keys()), key="kalk_del_sel")
            if st.button("Löschen", key="kalk_del_btn"): delete_kalk_id(opts[sel]); st.rerun()
            
        if c_rst.button("Alles Löschen", type="primary", key="kalk_reset"): delete_all("kalkulation"); st.rerun()
        
        # PROJEKT ABSCHLUSS MIT EXCEL
        st.markdown("---")
        st.subheader("🏁 Projektabschluss")
        xlsx_data = convert_df_to_excel(df_k)
        st.download_button(
            label="📥 Excel Exportieren",
            data=xlsx_data,
            file_name=f"PipeCraft_Projekt_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Projekt ist leer.")
