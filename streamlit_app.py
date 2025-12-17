import streamlit as st
import pandas as pd
import numpy as np
import math

# --- KONFIGURATION & DATENBANK ---
st.set_page_config(page_title="Rohrbau Profi", layout="wide")

# Datenbank definieren (DN, Außen-Ø, Radius 90°, Festflansch-Länge, Losflansch-Länge)
# Werte für Flansche sind exemplarische Standardwerte (bitte ggf. anpassen)
data = {
    "DN": [25, 32, 40, 50, 65, 80, 100, 125, 150, 200, 250, 300, 350, 400, 450, 500, 600],
    "AD": [33.7, 42.4, 48.3, 60.3, 76.1, 88.9, 114.3, 139.7, 168.3, 219.1, 273.0, 323.9, 355.6, 406.4, 457.0, 508.0, 610.0],
    "Radius": [38, 48, 57, 76, 95, 114, 152, 190, 229, 305, 381, 457, 533, 610, 686, 762, 914],
    "Festflansch": [100, 105, 110, 120, 125, 140, 160, 180, 210, 250, 280, 310, 330, 350, 370, 400, 450],
    "Losflansch": [115, 120, 125, 135, 140, 155, 175, 195, 225, 270, 300, 335, 360, 380, 400, 430, 480]
}
df_db = pd.DataFrame(data)

def get_pipe_data(dn):
    row = df_db[df_db['DN'] == dn]
    if not row.empty:
        return row.iloc[0]
    return None

# --- UI ---
st.title("🛠️ Rohrbau Profi Rechner")
st.markdown("---")

# Tabs für die verschiedenen Funktionen
tab1, tab2, tab3 = st.tabs(["Stutzen (Sattel)", "Bogen schneiden", "Passstück"])

# --- TAB 1: STUTZEN / SATTEL ---
with tab1:
    st.header("Stutzen & Abwicklung")
    
    col1, col2 = st.columns(2)
    with col1:
        dn_stutzen = st.selectbox("DN Stutzen", df_db['DN'], index=6) # Default DN 100
    with col2:
        dn_main = st.selectbox("DN Hauptrohr", df_db['DN'], index=9) # Default DN 200

    if dn_stutzen > dn_main:
        st.error("⚠️ Der Stutzen darf nicht größer sein als das Hauptrohr!")
    else:
        # Daten holen
        stutzen_data = get_pipe_data(dn_stutzen)
        main_data = get_pipe_data(dn_main)
        
        # --- NEU: Flansch Informationen anzeigen ---
        st.info(f"ℹ️ **Flansch-Baulängen für DN {dn_stutzen}:**")
        f_col1, f_col2 = st.columns(2)
        f_col1.metric("Festflansch", f"{int(stutzen_data['Festflansch'])} mm")
        f_col2.metric("Losflansch (inkl. Bund)", f"{int(stutzen_data['Losflansch'])} mm")
        st.markdown("---")

        # Berechnung Abwicklung
        d1 = stutzen_data['AD']
        d2 = main_data['AD']
        
        winkel_steps = np.arange(0, 181, 15) # 0 bis 180 in 15er Schritten
        results = []
        
        for w in winkel_steps:
            w_rad = math.radians(w)
            
            # 1. Umfang (Abstand auf dem Rohr)
            umfang = (w / 360) * (d1 * math.pi)
            
            # 2. Tiefe (Schnittkurve)
            # Formel: R_main - sqrt(R_main^2 - (r_stutzen * sin(alpha))^2)
            r_main = d2 / 2
            r_stutzen = d1 / 2
            term = (r_stutzen * math.sin(w_rad))**2
            tiefe = r_main - math.sqrt(r_main**2 - term)
            
            results.append({
                "Winkel (Grad)": int(w),
                "Umfang (mm)": umfang,
                "Tiefe (mm)": tiefe
            })
            
        df_res = pd.DataFrame(results)
        
        # --- NEU: Runden auf Ganzzahlen ---
        df_res["Umfang (mm)"] = df_res["Umfang (mm)"].round(0).astype(int)
        df_res["Tiefe (mm)"] = df_res["Tiefe (mm)"].round(0).astype(int)

        st.subheader("Schablone / Werte")
        # Tabelle anzeigen, Index ausblenden für saubereren Look
        st.table(df_res.set_index("Winkel (Grad)"))


# --- TAB 2: BOGEN SCHNEIDEN ---
with tab2:
    st.header("Bogen Gradeinteilung")
    
    c1, c2 = st.columns(2)
    with c1:
        dn_bogen = st.selectbox("DN Bogen", df_db['DN'], key="dn_bogen")
    with c2:
        target_angle = st.number_input("Gewünschter Winkel (°)", min_value=1.0, max_value=90.0, value=45.0)

    bogen_data = get_pipe_data(dn_bogen)
    
    radius = bogen_data['Radius']
    ad = bogen_data['AD']
    
    # Berechnungen
    bogen_länge_aussen = ((radius + (ad/2)) * math.pi * target_angle) / 180
    bogen_länge_innen = ((radius - (ad/2)) * math.pi * target_angle) / 180
    stichmass = radius * math.tan(math.radians(target_angle) / 2)
    
    st.success(f"Ergebnisse für DN {dn_bogen} ({target_angle}°)")
    
    res_col1, res_col2, res_col3 = st.columns(3)
    res_col1.metric("Bogenlänge AUSSEN", f"{bogen_länge_aussen:.1f} mm")
    res_col2.metric("Bogenlänge INNEN", f"{bogen_länge_innen:.1f} mm")
    res_col3.metric("Stichmaß (Abschnitt)", f"{stichmass:.1f} mm")


# --- TAB 3: PASSSTÜCK ---
with tab3:
    st.header("Passstück Berechnung (Etage / Versatz)")
    
    st.write("Berechnung der Rohrlänge zwischen zwei Bögen.")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        dn_pass = st.selectbox("DN Rohrleitung", df_db['DN'], key="dn_pass")
        len_center = st.number_input("Länge Mitte-Mitte (mm)", value=1000.0)
    with col_p2:
        spalt = st.number_input("Schweißspalt gesamt (mm)", value=3.0)
    
    st.markdown("#### Bogen Konfiguration")
    cp1, cp2 = st.columns(2)
    with cp1:
        w1 = st.number_input("Winkel Bogen 1 (°)", value=90.0)
    with cp2:
        w2 = st.number_input("Winkel Bogen 2 (°)", value=90.0)
        
    p_data = get_pipe_data(dn_pass)
    radius_p = p_data['Radius']
    
    # Abzugsmaße berechnen (Tan(alpha/2) * R)
    abzug1 = radius_p * math.tan(math.radians(w1)/2)
    abzug2 = radius_p * math.tan(math.radians(w2)/2)
    
    rohr_schnitt = len_center - abzug1 - abzug2 - spalt
    
    st.divider()
    st.subheader(f"Zuschnittlänge: {rohr_schnitt:.1f} mm")
    
    with st.expander("Details anzeigen"):
        st.write(f"Radius (Bauart 3): {radius_p} mm")
        st.write(f"Abzug Bogen 1: {abzug1:.1f} mm")
        st.write(f"Abzug Bogen 2: {abzug2:.1f} mm")
        st.write(f"Abzug Schweißspalt: {spalt} mm")
