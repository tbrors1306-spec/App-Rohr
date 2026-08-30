import json
import time
import math
from dataclasses import asdict
from datetime import datetime

import pandas as pd
import streamlit as st

from modules.models import FittingItem, SavedCut
from modules.calculations import (
    PipeCalculator, MaterialManager, HandbookCalculator,
    FieldCalc, WeldCalc, PipeRef,
)
from modules.utils import Visualizer, Exporter, PLOTLY_AVAILABLE
from modules.optimization import CuttingOptimizer, CutRequest
from modules.ui import init_app_state
from modules.help_texts import render_tool_help
from modules import welding_ref as wr

st.set_page_config(
    page_title="PipeCraft",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main .block-container { padding-top: 2rem; padding-bottom: 3rem; background-color: #f8fafc; }
    div[data-testid="stSidebar"] { min-width: 300px !important; }
    h1, h2, h3, h4, h5 { font-family: 'Segoe UI', sans-serif; font-weight: 600; color: #1e293b; }
    .machine-header-saw { border-bottom: 4px solid #f97316; color: #f97316; padding: 5px 0; font-weight: 700; font-size: 1.2rem; margin-bottom: 15px; text-transform: uppercase; }
    .machine-header-geo { border-bottom: 4px solid #0ea5e9; color: #0ea5e9; padding: 5px 0; font-weight: 700; font-size: 1.2rem; margin-bottom: 15px; text-transform: uppercase; }
    .machine-header-doc { border-bottom: 4px solid #64748b; color: #64748b; padding: 5px 0; font-weight: 700; font-size: 1.2rem; margin-bottom: 15px; text-transform: uppercase; }
    div[data-testid="stVerticalBlockBorderWrapper"] { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.5rem; }
    div[data-testid="stMetric"] { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 15px; }

    /* --- RESPONSIVE / MOBILE --- */
    @media (max-width: 1024px) {
        div[data-testid="stSidebar"] { min-width: 250px !important; }
        .main .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
        h1 { font-size: 1.8rem !important; }
    }
    @media (max-width: 768px) {
        div[data-testid="stSidebar"] { min-width: 100% !important; }
        .main .block-container { padding-left: 0.6rem !important; padding-right: 0.6rem !important; }

        /* alle st.columns-Reihen auf dem Handy untereinander stapeln */
        div[data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 0.5rem !important; }
        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"],
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            flex: 1 1 100% !important;
            width: 100% !important;
            min-width: 100% !important;
        }

        div[data-testid="stMetricValue"] { font-size: 1.35rem !important; }
        div[data-testid="stMetric"] { padding: 10px !important; }
        div[data-testid="stVerticalBlockBorderWrapper"] { padding: 1rem !important; }
        div[data-testid="stImage"] img, .stImage img { max-width: 100% !important; height: auto !important; }
        .machine-header-saw, .machine-header-geo, .machine-header-doc { font-size: 1.05rem !important; }

        /* Unter-Reiter umbrechen statt horizontal scrollen */
        div[data-testid="stTabs"] [role="tablist"] {
            flex-wrap: wrap !important;
            overflow-x: visible !important;
            row-gap: 4px !important;
        }
        div[data-testid="stTabs"] [role="tab"] {
            white-space: normal !important;
            height: auto !important;
        }
    }
</style>
""", unsafe_allow_html=True)

def render_smart_saw(calc: PipeCalculator, df: pd.DataFrame, current_dn: int, pn: str):
    st.markdown('<div class="machine-header-saw">🪚 SMARTE SÄGE</div>', unsafe_allow_html=True)
    proj_name = "PipeCraft"
    render_tool_help("saege")

    # Init saved cuts clean up
    if st.session_state.saved_cuts:
        try: _ = st.session_state.saved_cuts[0].fittings
        except AttributeError: st.session_state.saved_cuts = []

    # Transfer logic: Update the widget state directly if a transfer exists
    if 'transfer_cut_length' in st.session_state:
        new_val = st.session_state.pop('transfer_cut_length')
        st.session_state['saw_raw_input'] = float(new_val)
        st.toast("✅ Maß aus Geometrie übernommen!", icon="📏")
        
    c_calc, c_list = st.columns([1.3, 1.7])

    # --- LINKER BEREICH: RECHNER ---
    with c_calc:
        with st.container(border=True):
            
            # 1. DAS EINGABE-FORMULAR (Ganz oben)
            st.markdown("**1. Schnitt & Bauteile**")
            with st.form(key="combined_saw_form"):
                cut_name = st.text_input("Bezeichnung / Spool", placeholder="z.B. Strang A - 01")
                # Removed 'value=default_raw' and rely on key state or default 0.0
                raw_len = st.number_input("Schnittmaß (Roh) [mm]", min_value=0.0, step=10.0, format="%.1f", key="saw_raw_input")
                
                cg1, cg2, cg3 = st.columns(3)
                gap = cg1.number_input("Spalt (mm)", value=3.0, step=0.5)
                dicht_anz = cg2.number_input("Dichtungen", 0, 5, 0)
                dicht_thk = cg3.number_input("Dicke", 0.0, 5.0, 2.0)

                st.markdown("---")
                st.caption("Optional: Fitting hinzufügen")
                
                cf1, cf2 = st.columns([1.5, 1])
                f_type = cf1.selectbox("Typ", ["Bogen 90° (BA3)", "Bogen (Zuschnitt)", "Flansch (Vorschweiß)", "T-Stück", "Reduzierung"], label_visibility="collapsed")
                
                try: 
                    default_dn_idx = df['DN'].tolist().index(current_dn)
                except ValueError: 
                    default_dn_idx = 0
                f_dn = cf2.selectbox("DN", df['DN'], index=default_dn_idx, label_visibility="collapsed")
                
                cf3, cf4 = st.columns([1, 1])
                f_cnt = cf3.number_input("Anzahl", 1, 10, 1)
                f_ang = 90.0
                if "Zuschnitt" in f_type: 
                    f_ang = cf4.slider("Winkel", 0, 90, 45)
                else:
                    cf4.markdown("") # Spacer

                st.markdown("<br>", unsafe_allow_html=True)
                
                col_btn_add, col_btn_calc = st.columns(2)
                
                # Button A: Fügt Bauteil hinzu UND berechnet
                submitted_add = col_btn_add.form_submit_button("➕ Bauteil dazu", type="secondary", use_container_width=True)
                
                # Button B: Nur Berechnen
                submitted_calc = col_btn_calc.form_submit_button("🔄 Berechnen", type="primary", use_container_width=True)

            # --- LOGIK NACH DEM FORMULAR-SUBMIT ---
            
            # Fall A: Bauteil hinzufügen
            if submitted_add:
                deduct = calc.get_deduction(f_type, f_dn, pn, f_ang)
                uid = f"{len(st.session_state.fitting_list)}_{datetime.now().timestamp()}"
                nm = f"{f_type} DN{f_dn}" + (f" ({f_ang}°)" if "Zuschnitt" in f_type else "")
                st.session_state.fitting_list.append(FittingItem(uid, nm, f_cnt, deduct, f_dn))
                st.toast(f"✅ {nm} hinzugefügt!", icon="➕")

            # Fall B oder A: Berechnen
            if submitted_add or submitted_calc:
                sum_fit = sum(i.total_deduction for i in st.session_state.fitting_list)
                sum_gap = sum(i.count for i in st.session_state.fitting_list) * gap
                sum_gskt = dicht_anz * dicht_thk
                total = sum_fit + sum_gap + sum_gskt
                final = raw_len - total
                
                st.session_state.last_calc_result = {
                    "final": final, "raw": raw_len, "total_deduct": total,
                    "info": f"Teile -{sum_fit:.1f} | Spalte -{sum_gap:.1f} | Dicht. -{sum_gskt:.1f}"
                }

            # 2. LISTE DER BEREITS GEWÄHLTEN BAUTEILE (JETZT HIER UNTERHALB)
            if st.session_state.fitting_list:
                st.divider()
                st.markdown("###### 🛒 Enthaltene Teile:")
                for i, item in enumerate(st.session_state.fitting_list):
                    with st.container():
                        cr1, cr2, cr3 = st.columns([3, 1.5, 0.5])
                        cr1.text(f"{item.count}x {item.name}")
                        cr2.text(f"-{item.total_deduction:.1f}")
                        if cr3.button("🗑️", key=f"d_{item.id}", help="Entfernen"):
                            st.session_state.fitting_list.pop(i)
                            st.rerun()
                
                if st.button("Alle Teile entfernen", type="secondary", key="clear_fits"):
                    st.session_state.fitting_list = []
                    st.rerun()

            # 3. ERGEBNIS & SPEICHERN
            if 'last_calc_result' in st.session_state:
                res = st.session_state.last_calc_result
                st.divider()
                
                if res['final'] < 0:
                    st.error(f"⚠️ Negativmaß! ({res['final']:.1f} mm)")
                else:
                    st.metric("Sägelänge (Z)", f"{res['final']:.1f} mm")
                    st.caption(res['info'])
                    
                    # Tolerance Stack Calculator
                    with st.expander("⚠️ Schweißnaht-Schrumpfung berücksichtigen", expanded=False):
                        st.caption("Kompensiert die Schrumpfung durch Schweißnähte (typisch: 1-3mm pro Naht)")
                        tc1, tc2 = st.columns(2)
                        num_welds = tc1.number_input("Anzahl Nähte", min_value=1, max_value=10, value=2, step=1)
                        shrinkage = tc2.number_input("Schrumpfung/Naht (mm)", min_value=0.5, max_value=5.0, value=2.0, step=0.5)
                        
                        tol_result = calc.apply_tolerance_stack(res['final'], num_welds, shrinkage)
                        
                        st.divider()
                        tm1, tm2 = st.columns(2)
                        tm1.metric("Original", f"{tol_result['original']:.1f} mm")
                        tm2.metric("Korrigiert", f"{tol_result['adjusted']:.1f} mm", delta=f"+{tol_result['compensation']:.1f} mm")
                        st.caption(f"📏 Für {tol_result['num_welds']} Nähte à {tol_result['shrinkage_per_weld']}mm")
                    
                    if st.button("💾 IN LISTE SPEICHERN", type="primary", use_container_width=True):
                        final_name = cut_name if cut_name.strip() else f"Schnitt"
                        current_fittings_copy = list(st.session_state.fitting_list)
                        new_id = int(time.time() * 1000)
                        
                        new_cut = SavedCut(new_id, final_name, res['raw'], res['final'], 
                                         f"{len(current_fittings_copy)} Teile", 
                                         datetime.now().strftime("%H:%M"), 
                                         current_fittings_copy)
                        
                        st.session_state.saved_cuts.append(new_cut)
                        st.session_state.fitting_list = [] 
                        del st.session_state.last_calc_result
                        
                        st.toast("✅ Schnitt gespeichert!", icon="💾")
                        time.sleep(0.5)
                        st.rerun()

    # --- RECHTER BEREICH: LISTE ---
    with c_list:
        st.markdown("#### 📋 Schnittliste")
        action_bar = st.container()

        if not st.session_state.saved_cuts:
            st.info("Noch keine Schnitte vorhanden.")
            with action_bar:
                st.button("🗑️ Löschen", disabled=True, use_container_width=True)
        else:
            data = [asdict(c) for c in st.session_state.saved_cuts]
            df_s = pd.DataFrame(data)
            if 'Auswahl' not in df_s.columns: df_s['Auswahl'] = False
            
            df_display = df_s[['Auswahl', 'name', 'raw_length', 'cut_length', 'details', 'id']]
            
            edited_df = st.data_editor(
                df_display, 
                hide_index=True, 
                use_container_width=True,
                column_config={
                    "Auswahl": st.column_config.CheckboxColumn("☑️", width="small", default=False),
                    "name": st.column_config.TextColumn("Bez.", width="medium"), 
                    "raw_length": st.column_config.NumberColumn("Roh", format="%.0f"), 
                    "cut_length": st.column_config.NumberColumn("Säge", format="%.1f", width="medium"), 
                    "details": st.column_config.TextColumn("Info", width="small"), 
                    "id": None
                },
                disabled=["name", "raw_length", "cut_length", "details", "id"], 
                key="saw_editor_v4"
            )
            
            selected_rows = edited_df[edited_df['Auswahl'] == True]
            selected_ids = selected_rows['id'].tolist()
            num_sel = len(selected_ids)
            
            with action_bar:
                btns_disabled = (num_sel == 0)
                col_del, col_excel = st.columns([1, 1])

                if col_del.button(f"🗑️ Löschen ({num_sel})", disabled=btns_disabled, type="secondary", use_container_width=True):
                    st.session_state.saved_cuts = [c for c in st.session_state.saved_cuts if c.id not in selected_ids]
                    st.toast(f"🗑️ {num_sel} Einträge gelöscht!", icon="🗑️")
                    time.sleep(0.5)
                    st.rerun()

                fname_base = f"Saege_{proj_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}"
                excel_data = Exporter.to_excel(df_s)
                col_excel.download_button("📥 Excel (Alle)", excel_data, f"{fname_base}.xlsx", use_container_width=True)

            # --- OPTIMIZER BLOCK ---
            st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
            with st.expander("✂️ Schnitt-Optimierung (Verschnitt-Minimierung)", expanded=False):
                st.caption("Berechnet die optimale Aufteilung der gewählten Schnitte auf Stangen.")
                
                c_opt1, c_opt2 = st.columns(2)
                stock_len = c_opt1.number_input("Stangenlänge (mm)", value=6000.0, step=500.0)
                saw_width = c_opt2.number_input("Sägeblatt (mm)", value=3.0, step=0.5)
                
                if st.button("🚀 Optimierung starten", disabled=btns_disabled, use_container_width=True):
                    # Gather cuts
                    requests = []
                    for cut in st.session_state.saved_cuts:
                        if cut.id in selected_ids: 
                            requests.append(CutRequest(id=cut.name, length=cut.cut_length))
                    
                    if not requests:
                        st.error("Bitte Schnitte auswählen!")
                    else:
                        result_bars = CuttingOptimizer.solve_ffd(requests, stock_len, saw_width)
                        st.session_state.opt_results = result_bars
                        st.toast("Optimierung fertig!")

                if 'opt_results' in st.session_state and st.session_state.opt_results:
                    bars = st.session_state.opt_results
                    total_waste = sum(b.waste for b in bars)
                    
                    st.divider()
                    st.markdown("##### Ergebnis:")
                    m1, m2 = st.columns(2)
                    m1.metric("Benötigte Stangen", f"{len(bars)} Stk")
                    m2.metric("Gesamtabfall", f"{total_waste/1000:.2f} m")
                    
                    fig_opt = Visualizer.plot_cutting_plan(bars)
                    if fig_opt:
                        st.pyplot(fig_opt, use_container_width=True)
                    
                    with st.expander("Detailliste"):
                        for b in bars:
                            st.markdown(f"**Stange {b.id}** (Rest: {b.waste:.1f}mm)")
                            txts = [f"{c.length:.0f}" for c in b.cuts]
                            st.caption(" | ".join(txts))

            st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
            if st.button("Alles Reset (Liste leeren)", type="secondary"):
                st.session_state.saved_cuts = []
                st.rerun()

def render_tab_handbook(calc: PipeCalculator, dn: int, pn: str):
    st.markdown('<div class="machine-header-doc">📚 SMART DATA</div>', unsafe_allow_html=True)
    render_tool_help("smartdata")
    row = calc.get_row(dn)
    suffix = "_16" if pn == "PN 16" else "_10"
    st.markdown(f"**DN {dn} / {pn}**")

    od = float(row['D_Aussen'])
    flange_b = float(row[f'Flansch_b{suffix}'])
    lk = float(row[f'LK_k{suffix}'])
    bolt = row[f'Schraube_M{suffix}']
    n_holes = int(row[f'Lochzahl{suffix}'])
    

    sd_tabs = st.tabs([
        "🏗️ Flansch & Schrauben", "📏 Rohrmaße / Schedule",
        "🏗️ Hebezeug", "🔀 PN ↔ Class",
    ])

    with sd_tabs[0]:
        with st.container(border=True):
            st.markdown("##### 🏗️ Gewichte & Hydrotest")
            with st.form("handbook_weight_form"):
                c_in1, c_in2 = st.columns([1, 2])
                with c_in1:
                    wt_input = st.number_input("Wandstärke (mm)", value=6.3, min_value=1.0, step=0.1)
                    len_input = st.number_input("Rohrlänge (m)", value=6.0, step=0.5)
            
                submit_weight = st.form_submit_button("Berechnen")
        
            if submit_weight or True: # Initiale Berechnung erlauben
                w_data = HandbookCalculator.calculate_weight(od, wt_input, len_input * 1000)
                mc1, mc2, mc3 = st.columns(3)
                mc1.metric("Leergewicht (Stahl)", f"{w_data['total_steel']:.1f} kg", f"{w_data['kg_per_m_steel']:.1f} kg/m")
                mc2.metric("Gewicht Gefüllt", f"{w_data['total_filled']:.1f} kg", "für Hydrotest")
                mc3.metric("Füllvolumen", f"{w_data['volume_l']:.0f} Liter", "Wasserbedarf")

        c_geo1, c_geo2 = st.columns(2)
        with c_geo1:
            with st.container(border=True):
                st.markdown("##### 📐 Flansch")
                st.write(f"**Blatt:** {flange_b} mm | **Lochkreis:** {lk} mm")
                st.write(f"**Bohrung:** {n_holes} x {bolt}")
                progress_val = min(lk / (od + 100), 1.0)
                st.progress(progress_val, text="Lochkreis Verhältnis")

        with c_geo2:
            with st.container(border=True):
                st.markdown("##### 🔘 Dichtung (Check)")
                d_innen = od - (2*wt_input) 
                d_aussen = lk - (int(bolt.replace("M","")) * 1.5)
                st.info(f"ID: ~{d_innen:.0f} mm | AD: ~{d_aussen:.0f} mm | 2.0mm")

        st.divider()
    
        with st.container(border=True):
            st.markdown("#### 🔧 Montage & Drehmomente (8.8)")
        
            cb_col1, cb_col2 = st.columns([1, 2.5])
        
            with cb_col1:
                st.caption("Konfiguration")
                conn_type = st.radio("Typ", ["Fest-Fest", "Fest-Los", "Fest-Blind"], index=0, label_visibility="collapsed")
                use_washers = st.checkbox("2x U-Scheibe", value=True)
                is_lubed = st.toggle("Geschmiert (MoS2)", value=True)
                gasket_thk = st.number_input("Dichtung", value=2.0, step=0.5)
            
            with cb_col2:
                bolt_info = HandbookCalculator.BOLT_DATA.get(bolt, [0, 0, 0])
                sw, nm_dry, nm_lube = bolt_info
            
                t1 = flange_b
                t2 = flange_b 
                if "Los" in conn_type: t2 = flange_b + 5 
                elif "Blind" in conn_type: t2 = flange_b + (dn * 0.02)
                
                n_washers = 2 if use_washers else 0
                calc_len = HandbookCalculator.get_bolt_length(t1, t2, bolt, n_washers, gasket_thk)
                torque = nm_lube if is_lubed else nm_dry
            
                m1, m2, m3 = st.columns(3)
                m1.metric("Bolzen", f"{bolt} x {calc_len}", f"{n_holes} Stk.")
                m2.metric("Schlüsselweite", f"SW {sw} mm", "Nuss/Ring")
                m3.metric("Drehmoment", f"{torque} Nm", "Geschmiert" if is_lubed else "Trocken")

    # ---------------------------------------------- Rohrmaße / Schedule -----
    with sd_tabs[1]:
        render_tool_help("sd_schedule")
        by = st.radio("Auswahl über", ["NPS (Zoll)", "DN (aus App-Tabelle)"], horizontal=True, key="sd_by")
        if by.startswith("DN"):
            dn_sel = st.selectbox("DN", calc.df['DN'], index=8, key="sd_dn")
            nps = PipeRef.nps_for_dn(int(dn_sel)) or '12"'
            if PipeRef.nps_for_dn(int(dn_sel)) is None:
                st.info(f"Für DN {dn_sel} liegt keine ASME-Schedule-Zeile vor – zeige DN 300.")
        else:
            nps = st.selectbox("Nennweite (NPS)", list(PipeRef.SCHEDULE.keys()), index=11, key="sd_nps")
        sc = PipeRef.schedule_rows(nps)
        m1, m2 = st.columns(2)
        m1.metric("DN", f"DN {sc['dn']}")
        m2.metric("Außendurchmesser", _fmt_len(sc['od']),
                  f'{sc["od"]/25.4:.3f}"' if st.session_state.get("global_unit") != "Zoll" else f"{sc['od']:.1f} mm")
        _df_sched = pd.DataFrame(sc["rows"])
        if st.session_state.get("global_unit") == "Zoll":
            for col in ("Wand (mm)", "Innen-Ø (mm)"):
                _df_sched[col] = _df_sched[col].map(
                    lambda v: round(v / 25.4, 3) if isinstance(v, (int, float)) else v)
            _df_sched = _df_sched.rename(columns={"Wand (mm)": 'Wand (")', "Innen-Ø (mm)": 'Innen-Ø (")'})
        st.dataframe(_df_sched, hide_index=True, use_container_width=True)
        st.caption("ASME B36.10M · \"STD\" = Sch 40 bis NPS 12, darüber fest 9,53 mm · "
                   "\"XS\" = Sch 80 bis NPS 8, darüber fest 12,7 mm · XXS für NPS ≥ 14 nicht definiert. "
                   "Innen-Ø = OD − 2·Wand. Im Zweifel Norm / Werksbescheinigung.")

    # ---------------------------------------------- Hebezeug --------------
    with sd_tabs[2]:
        render_tool_help("sd_lifting")
        c_in, c_out = st.columns([1, 1.4])
        with c_in:
            with st.container(border=True):
                src = st.radio("Gewicht", ["aus Rohr (OD/Wand/Länge)", "direkt (kg)"], key="sdl_src")
                if src.startswith("aus"):
                    l_od = st.number_input("Außen-Ø (mm)", value=od, min_value=1.0, step=1.0, key="sdl_od")
                    l_w = st.number_input("Wandstärke (mm)", value=6.3, min_value=0.5, step=0.1, key="sdl_w")
                    l_len = st.number_input("Länge (m)", value=6.0, min_value=0.1, step=0.5, key="sdl_len")
                    wkg = HandbookCalculator.calculate_weight(l_od, l_w, l_len * 1000)["total_steel"]
                    st.caption(f"Rohrgewicht ≈ {wkg:.0f} kg")
                else:
                    wkg = st.number_input("Gesamtgewicht (kg)", value=500.0, min_value=1.0, step=10.0, key="sdl_kg")
                nlg = st.radio("Anzahl Stränge", [1, 2, 3, 4], index=1, horizontal=True, key="sdl_n")
                bet = st.slider("Neigungswinkel β (° zur Senkrechten)", 0, 75, 45, 5, key="sdl_b")
        r = PipeRef.sling_load(wkg, nlg, bet)
        with c_out:
            with st.container(border=True):
                m1, m2 = st.columns(2)
                m1.metric("Gesamtlast", f"{r['f_total_kn']:.1f} kN", f"{wkg:.0f} kg")
                m2.metric("Last je Strang", f"{r['f_leg_kn']:.1f} kN", f"≈ {r['f_leg_kg']:.0f} kg")
                m3, m4 = st.columns(2)
                m3.metric("Tragende Stränge", f"{r['n_eff']}", "≥3 → nur 2 gerechnet")
                m4.metric("Neigungsbeiwert", f"{r['factor']:.2f}", "1 / cos β")
                st.caption("Je Strang = m·g / (n_wirk · cos β). Bei 3-/4-Strang-Gehängen zählen "
                           "praktisch nur 2 Stränge als tragend (ungleiche Lastverteilung). "
                           "Anschlagmittel nach Tragfähigkeitstabelle für den Winkelbereich wählen.")
        st.caption("β = 0° senkrecht (Faktor 1,0) · 45° → 1,41 · 60° → 2,0 · über 60° vermeiden.")

    # ---------------------------------------------- PN <-> Class ----------
    with sd_tabs[3]:
        render_tool_help("sd_pnclass")
        st.markdown("**Grobe Druck-Äquivalenz PN ↔ ASME Class** (Stahl, ~20 °C)")
        st.dataframe(pd.DataFrame(PipeRef.PN_CLASS), hide_index=True, use_container_width=True)
        st.caption("Nur eine Orientierung. Der zulässige Druck sinkt mit steigender "
                   "Temperatur (Druck-Temperatur-Rating der jeweiligen Norm: EN 1092-1 "
                   "bzw. ASME B16.5). PN und Class sind **nicht** baugleich – Flansche "
                   "nicht mischen ohne Prüfung von Lochbild, Dichtfläche und Schrauben.")


def _od_from_dn(df: pd.DataFrame, dn: int, fallback: float = 0.0) -> float:
    try:
        row = df[df['DN'] == dn]
        if not row.empty:
            return float(row.iloc[0]['D_Aussen'])
    except (KeyError, IndexError, ValueError):
        pass
    return fallback


def _fmt_len(mm, digits=2):
    """Längenwert je nach globaler Anzeige-Einheit (mm oder Zoll) formatieren."""
    if not isinstance(mm, (int, float)):
        return mm
    if st.session_state.get("global_unit") == "Zoll":
        return f'{mm / 25.4:.{max(digits, 3)}f}"'
    return f"{mm:.{digits}f} mm"


def _pdf_button(title, inputs, results, note="", key=None):
    """Einheitlicher 'als PDF'-Download für einen Rechner."""
    try:
        data = Exporter.to_pdf_report(title, inputs, results, note)
    except Exception:
        data = b""
    if not data:
        return
    fname = f"{title.replace(' ', '_').replace('/', '-')}_{datetime.now():%Y%m%d}.pdf"
    st.download_button("📄 als PDF", data, fname, mime="application/pdf",
                       key=key or f"pdf_{title}")


def render_field_calc(calc: PipeCalculator, df: pd.DataFrame):
    st.markdown('<div class="machine-header-geo">🧮 FELD-RECHNER</div>', unsafe_allow_html=True)
    t_tri, t_circ = st.tabs(["📐 Trigonometrie", "⭕ Kreisteiler"])

    # ---------------------------------------------------------------- Trig ---
    with t_tri:
        render_tool_help("fc_tri")
        mode = st.radio("Dreieckstyp", ["Rechtwinklig", "Schräg (Kosinussatz)"],
                        horizontal=True, key="tri_mode")
        c_in, c_out = st.columns([1, 1.4])

        if mode == "Rechtwinklig":
            with c_in:
                with st.container(border=True):
                    st.markdown("**Zwei Werte eingeben, Rest wird berechnet**")
                    st.caption("a = Ankathete zu α · b = Gegenkathete zu α · c = Hypotenuse")
                    use_a = st.checkbox("a (mm)", value=True, key="rt_ua")
                    a = st.number_input("a", value=300.0, step=1.0, key="rt_a", disabled=not use_a, label_visibility="collapsed")
                    use_b = st.checkbox("b (mm)", value=True, key="rt_ub")
                    b = st.number_input("b", value=400.0, step=1.0, key="rt_b", disabled=not use_b, label_visibility="collapsed")
                    use_c = st.checkbox("c (mm)", value=False, key="rt_uc")
                    c = st.number_input("c", value=500.0, step=1.0, key="rt_c", disabled=not use_c, label_visibility="collapsed")
                    use_al = st.checkbox("α (Grad)", value=False, key="rt_ual")
                    al = st.number_input("α", value=45.0, step=0.5, key="rt_al", disabled=not use_al, label_visibility="collapsed")
            res = FieldCalc.right_triangle(
                a=a if use_a else None, b=b if use_b else None,
                c=c if use_c else None, alpha=al if use_al else None,
            )
            with c_out:
                if "error" in res:
                    st.warning(res["error"])
                else:
                    with st.container(border=True):
                        st.markdown("**Ergebnis**")
                        m1, m2, m3 = st.columns(3)
                        m1.metric("a", f"{res['a']:.1f} mm")
                        m2.metric("b", f"{res['b']:.1f} mm")
                        m3.metric("c", f"{res['c']:.1f} mm")
                        m4, m5, m6 = st.columns(3)
                        m4.metric("α", f"{res['alpha']:.2f}°")
                        m5.metric("β", f"{res['beta']:.2f}°")
                        m6.metric("Fläche", f"{res['area']/100:.1f} cm²")
        else:
            with c_in:
                with st.container(border=True):
                    st.markdown("**Kosinussatz**")
                    sub = st.radio("Bekannt", ["a, b, γ (eingeschl. Winkel)", "a, b, c (3 Seiten)"],
                                   key="ot_sub")
                    a = st.number_input("a (mm)", value=500.0, step=1.0, key="ot_a")
                    b = st.number_input("b (mm)", value=400.0, step=1.0, key="ot_b")
                    if sub.startswith("a, b, γ"):
                        g = st.number_input("γ (Grad)", value=60.0, min_value=0.1, max_value=179.9, step=0.5, key="ot_g")
                        res = FieldCalc.oblique_triangle(a=a, b=b, gamma=g)
                    else:
                        cc = st.number_input("c (mm)", value=600.0, step=1.0, key="ot_c")
                        res = FieldCalc.oblique_triangle(a=a, b=b, c=cc)
            with c_out:
                if "error" in res:
                    st.warning(res["error"])
                else:
                    with st.container(border=True):
                        st.markdown("**Ergebnis**")
                        m1, m2, m3 = st.columns(3)
                        m1.metric("a", f"{res['a']:.1f} mm")
                        m2.metric("b", f"{res['b']:.1f} mm")
                        m3.metric("c", f"{res['c']:.1f} mm")
                        m4, m5, m6 = st.columns(3)
                        m4.metric("α", f"{res['alpha']:.2f}°")
                        m5.metric("β", f"{res['beta']:.2f}°")
                        m6.metric("γ", f"{res['gamma']:.2f}°")
                        st.caption(f"Umfang {res['umfang']:.1f} mm · Fläche {res['area']/100:.1f} cm²")

    # ---------------------------------------------------------------- Circle -
    with t_circ:
        render_tool_help("fc_circle")
        c_in, c_out = st.columns([1, 1.4])
        with c_in:
            with st.container(border=True):
                by = st.radio("Vorgabe", ["Durchmesser", "Umfang"], horizontal=True, key="cd_by")
                d_in = st.number_input(f"{'Teil-/Lochkreis-Ø' if by=='Durchmesser' else 'Gemessener Umfang'} (mm)",
                                       value=200.0, min_value=1.0, step=1.0, key="cd_d")
                n = st.number_input("Anzahl Teile / Löcher", value=6, min_value=2, step=1, key="cd_n")
        res = FieldCalc.divide_circle(d_in, int(n), by)
        with c_out:
            if "error" in res:
                st.warning(res["error"])
            else:
                with st.container(border=True):
                    st.markdown("**Anreißmaße**")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Winkelschritt", f"{res['step_deg']:.2f}°")
                    m2.metric("Bogenmaß / Teil", f"{res['arc']:.2f} mm")
                    m3.metric("Sehne (Teilung)", f"{res['chord']:.2f} mm")
                    st.caption(f"Ø {res['D']:.1f} mm · Umfang {res['circ']:.1f} mm · "
                               f"Maß über Eck/gegenüber {res['across']:.1f} mm")
        if "error" not in res:
            cga, cgb = st.columns([1, 1])
            with cga:
                st.pyplot(Visualizer.plot_bolt_circle(res['points'], res['D']), use_container_width=False)
            with cgb:
                st.markdown("**Koordinaten (Nullpunkt unten links)**")
                st.dataframe(pd.DataFrame(res['points']), hide_index=True, use_container_width=True, height=260)


def render_weld_tools(calc: PipeCalculator, df: pd.DataFrame):
    st.markdown('<div class="machine-header-saw">🔥 SCHWEISSEN</div>', unsafe_allow_html=True)
    st.caption("Richtwerte für das Feld – die freigegebene WPS bzw. die Norm haben immer Vorrang.")
    t_fillet, t_prep, t_pre = st.tabs(
        ["📐 a- / z-Maß", "📎 Nahtvorbereitung", "🌡️ Vorwärmen / PWHT"]
    )

    # ------------------------------------------------------------ a / z ----
    with t_fillet:
        render_tool_help("weld_az")
        c_in, c_out = st.columns([1, 1.4])
        with c_in:
            with st.container(border=True):
                which = st.radio("Bekannt", ["z-Maß (Schenkel)", "a-Maß (Nahtdicke)"], key="fz_w")
                if which.startswith("z"):
                    z = st.number_input("z (mm)", value=5.0, min_value=0.1, step=0.5, key="fz_z")
                    res = WeldCalc.fillet_a_z(z=z)
                else:
                    a = st.number_input("a (mm)", value=3.5, min_value=0.1, step=0.5, key="fz_a")
                    res = WeldCalc.fillet_a_z(a=a)
        with c_out:
            with st.container(border=True):
                st.markdown("**Ergebnis**")
                m1, m2 = st.columns(2)
                m1.metric("a-Maß", f"{res['a']:.2f} mm")
                m2.metric("z-Maß", f"{res['z']:.2f} mm")
                st.latex(r"a = \frac{z}{\sqrt{2}} \approx 0{,}707 \cdot z")
                st.caption("Gilt für die gleichschenklige Kehlnaht (Flankenwinkel 90°).")

    # -------------------------------------------------- Nahtvorbereitung ----
    with t_prep:
        render_tool_help("weld_prep")
        JOINTS = {
            "I-Stoß":        dict(angle=0.0,  rf=0.0, gap=3.0, note="Nur bis ~4 mm Wand, ein-/beidseitig."),
            "V-Naht":        dict(angle=60.0, rf=1.6, gap=2.0, note="Standard-Stumpfnaht ~3–16 mm."),
            "HV-Naht":       dict(angle=50.0, rf=1.6, gap=2.0, note="Halb-V, eine Flanke angeschrägt (T-Stoß / Anschluss)."),
            "DV-Naht (X)":   dict(angle=60.0, rf=2.0, gap=2.0, note="Ab ~12 mm, beidseitig zugänglich – halbes Füllvolumen, weniger Verzug."),
            "Kehlnaht":      dict(angle=0.0,  rf=0.0, gap=0.0, note="T-, Eck-, Überlappstoß. Maßgeblich ist das a-Maß."),
        }
        c_in, c_out = st.columns([1, 1.3])
        with c_in:
            with st.container(border=True):
                jt = st.selectbox("Nahtart", list(JOINTS.keys()), index=1, key="wp_jt")
                d = JOINTS[jt]
                t = st.slider("Wandstärke / Blechdicke (mm)", 1.0, 30.0, 8.0, 0.5, key="wp_t")
                if jt == "Kehlnaht":
                    fz = st.slider("z-Maß (Schenkel, mm)", 2.0, 20.0, 6.0, 0.5, key="wp_fz")
                    inc = rf = gap = 0.0
                else:
                    inc = st.slider("Öffnungs-/Flankenwinkel (°)", 20, 80, int(d["angle"]), 1, key="wp_inc")
                    rf = st.slider("Steg / Land (mm)", 0.0, 4.0, d["rf"], 0.1, key="wp_rf")
                    gap = st.slider("Wurzelspalt (mm)", 0.0, 5.0, d["gap"], 0.1, key="wp_gap")
                    fz = 6.0
                st.caption(d["note"])
        ga = WeldCalc.groove_area(jt, t, inc or 60.0, rf, gap, 1.5, 1.0, fz)
        with c_out:
            if jt == "Kehlnaht":
                st.pyplot(Visualizer.plot_joint_prep(90.0, 0.0, 0.0, 0.0, max(t, fz)),
                          use_container_width=True)
            else:
                st.pyplot(Visualizer.plot_joint_prep(inc or 60.0, rf, gap, 0.0, t),
                          use_container_width=True)
            with st.container(border=True):
                m1, m2 = st.columns(2)
                m1.metric("Naht-Querschnitt A", f"{ga['area']:.0f} mm²")
                if jt == "Kehlnaht":
                    m2.metric("a-Maß", f"{ga['a_mass']:.1f} mm")
                else:
                    m2.metric("Fugenbreite oben", f"{ga.get('top_width', 0):.1f} mm")

    # -------------------------------------------------- Vorwärmen / PWHT --
    with t_pre:
        render_tool_help("weld_preheat")
        st.markdown("**Vorwärm-Richtwerte für Pipeline-Rundnähte** (nach WPS-Preheat-Chart)")
        st.dataframe(pd.DataFrame(WeldCalc.PREHEAT_PIPELINE), hide_index=True, use_container_width=True)
        st.caption(WeldCalc.PREHEAT_PIPELINE_NOTE)
        st.divider()
        st.markdown("**Rechnerisch nach EN 1011-2, Methode B** (wenn CET bekannt)")
        c_in, c_out = st.columns([1, 1.4])
        with c_in:
            with st.container(border=True):
                mode = st.radio("CET", ["direkt eingeben", "aus Legierung berechnen"], key="ph_mode")
                if mode == "direkt eingeben":
                    cet_val = st.number_input("CET (%)", value=0.30, min_value=0.10, max_value=0.60,
                                              step=0.01, format="%.2f", key="ph_cet")
                else:
                    e1, e2 = st.columns(2)
                    cC = e1.number_input("C %", value=0.16, step=0.01, format="%.3f", key="ph_c")
                    cMn = e2.number_input("Mn %", value=1.10, step=0.05, format="%.2f", key="ph_mn")
                    cMo = e1.number_input("Mo %", value=0.0, step=0.01, format="%.3f", key="ph_mo")
                    cCr = e2.number_input("Cr %", value=0.0, step=0.01, format="%.3f", key="ph_cr")
                    cCu = e1.number_input("Cu %", value=0.0, step=0.01, format="%.3f", key="ph_cu")
                    cNi = e2.number_input("Ni %", value=0.0, step=0.01, format="%.3f", key="ph_ni")
                    cet_val = WeldCalc.cet(cC, cMn, cMo, cCr, cCu, cNi)
                    st.caption(f"CET = {cet_val:.3f} %")
                thk = st.number_input("Kombinierte Dicke d (mm)", value=45.0, min_value=5.0, step=5.0,
                                      key="ph_d", help="Summe der Blechdicken an der Fuge (Wärmeabfluss).")
                hdt = st.selectbox("Zusatz / Wasserstoff HD", list(WeldCalc.HD_TYPICAL.keys()),
                                   index=1, key="ph_hdt")
                hd = WeldCalc.HD_TYPICAL[hdt]
                q = st.number_input("Streckenenergie Q (kJ/mm)", value=1.0, min_value=0.2, max_value=5.0,
                                    step=0.1, key="ph_q", help="Aus Reiter ⚡ Streckenenergie.")
                st.caption(f"HD ≈ {hd:.0f} ml/100 g")
        r = WeldCalc.preheat_en1011(cet_val, thk, hd, q)
        with c_out:
            with st.container(border=True):
                st.metric("Empfohlene Vorwärm-/Zwischenlagentemperatur",
                          f"{r['Tp']:.0f} °C" if r['Tp'] > 20 else "keine Vorwärmung nötig",
                          f"CET {cet_val:.2f} · d {thk:.0f} mm · Q {q:.1f} kJ/mm")
                for w in r["warnings"]:
                    st.warning("⚠️ " + w)
                st.latex(r"T_p = 697\,C_{ET} + 160\tanh\!\frac{d}{35} + 62\,HD^{0{,}35} + (53\,C_{ET}-32)\,Q - 328")
                _pdf_button("Vorwaermtemperatur EN 1011-2 B",
                            {"CET (%)": round(cet_val, 3), "komb. Dicke d (mm)": thk,
                             "Zusatz/HD": hdt, "Q (kJ/mm)": q},
                            {"Vorwaerm-/Zwischenlagentemp. (C)": round(r['Tp'])},
                            note="; ".join(r["warnings"]) if r["warnings"] else
                            "Eingaben im Gueltigkeitsbereich von EN 1011-2 Methode B.",
                            key="pdf_preheat")
        st.divider()
        st.markdown("**PWHT (Spannungsarmglühen) – Richtwerte**")
        st.dataframe(pd.DataFrame(WeldCalc.PWHT_REF), hide_index=True, use_container_width=True)
        st.caption("Verbindlich sind Regelwerk (EN 13445 / EN 13480 / ASME) und Kundenspezifikation. "
                   "Auf-/Abkühlrate oberhalb ~300 °C typ. ≤ 220 °C/h ÷ (Wanddicke/25), max. 220 °C/h. "
                   "ASME-Haltezeit meist 1 h je 25 mm.")


def render_downhill_school(calc: PipeCalculator, df: pd.DataFrame):
    st.markdown('<div class="machine-header-saw">🎓 FALLNAHT (STOVEPIPE) – CELLULOSE</div>',
                unsafe_allow_html=True)
    render_tool_help("fallnaht")
    st.caption("Lern- und Nachschlagemodul für das fallende Elektrodenschweißen mit "
               "zellulose-umhüllten Elektroden (E xx10, Handelsname z. B. CEL 70). "
               "Alle Werte sind Richtwerte – die freigegebene WPS hat Vorrang.")

    t_over, t_joint, t_angle, t_amp, t_dev, t_pre, t_def, t_seq = st.tabs(
        ["① Überblick", "② Nahtvorbereitung", "③ Elektrodenhaltung", "④ Strom & Lagen",
         "⑤ Gerät (EWM Pico 350)", "⑥ Vorwärmen", "⑦ Fehler & RT-Auswertung", "⑧ Ablauf"]
    )

    with t_over:
        st.markdown(wr.CEL_OVERVIEW)
        with st.expander("🔋 Elektroden-Handling & Lagerung (wichtig bei Cellulose!)", expanded=False):
            st.markdown(wr.CEL_STORAGE)
        with st.expander("⚠️ Sicherheit im Feld", expanded=False):
            st.markdown(wr.CEL_SAFETY)

    with t_joint:
        st.markdown("Stelle die Fugenmaße ein – die Zeichnung und die Wirkung passen sich an.")
        c_in, c_out = st.columns([1, 1.3])
        with c_in:
            with st.container(border=True):
                inc = st.slider("Öffnungswinkel gesamt (°)", 40, 80, 60, 1, key="dh_inc")
                land = st.slider("Steg / Land (mm)", 0.0, 3.0, 1.6, 0.1, key="dh_land")
                gap = st.slider("Wurzelspalt / Gap (mm)", 0.0, 4.0, 1.6, 0.1, key="dh_gap")
                hilo = st.slider("Kantenversatz Hi-Lo (mm)", 0.0, 4.0, 0.0, 0.1, key="dh_hilo")
                wt = st.slider("Wandstärke (mm)", 3.0, 20.0, 8.0, 0.5, key="dh_wt")
        with c_out:
            st.pyplot(Visualizer.plot_joint_prep(inc, land, gap, hilo, wt),
                      use_container_width=True)
        st.divider()
        st.markdown("**Richtwerte und wofür jeder Wert da ist:**")
        rows = [{"Maß": k, "Richtwert": v[0], "Wirkung / Hinweis": v[1]}
                for k, v in wr.CEL_JOINT.items()]
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        st.caption("API 1104 heißt bei Rohrleitungsschweißern nicht umsonst "
                   "\"the sixteenth-inch code\" – fast jedes Maß ist 1/16\" = 1,6 mm.")

    with t_angle:
        st.markdown("Stelle die Winkel ein – das Bild zeigt, **wie die Elektrode gehalten wird**. "
                    "Der grüne Sektor ist der Richtwertbereich für die gewählte Uhrposition.")
        cc1, cc2, cc3 = st.columns(3)
        pos = cc1.selectbox("Uhrposition", list(wr.DRAG_BANDS.keys()), key="dh_pos")
        drag = cc2.slider("Schleppwinkel (°)", 0, 45, 12, 1, key="dh_drag",
                          help="Neigung der Elektrode entgegen der Laufrichtung (Seitenansicht).")
        work = cc3.slider("Arbeitswinkel-Neigung (°)", 0, 25, 6, 1, key="dh_work",
                          help="Kippen aus der Winkelhalbierenden der Fuge zur bereits "
                               "geschweißten Seite (Schnittansicht).")
        lo, hi = wr.DRAG_BANDS[pos]
        st.pyplot(Visualizer.plot_electrode_angles(drag, work, lo, hi), use_container_width=True)

        if drag < lo:
            st.warning(f"⚠️ Schleppwinkel **zu flach** ({drag}°). Richtwert für {pos}: "
                       f"{lo}–{hi}°. Zu flach → Schlacke läuft vor dem Lichtbogen her → "
                       f"Schlackeneinschlüsse.")
        elif drag > hi:
            st.warning(f"⚠️ Schleppwinkel **zu steil** ({drag}°). Richtwert für {pos}: "
                       f"{lo}–{hi}°. Zu steil → der Lichtbogen gräbt → Wurzelkerbe / Durchbrand.")
        else:
            st.success(f"✅ Schleppwinkel im Richtwert ({lo}–{hi}° für {pos}).")

        if work <= 12:
            st.info(wr.WORK_ANGLE_NOTE)
        else:
            st.warning(f"⚠️ Arbeitswinkel-Neigung {work}° ist groß – nur in 3–6 Uhr 5–10° "
                       f"zur kalten Seite kippen, sonst mittig führen.")
        st.divider()
        for k, v in wr.CEL_ANGLES.items():
            st.markdown(f"**{k}**  \n{v}")

        st.divider()
        st.markdown("#### 🖊️ Führungstechnik / Raupenform")
        st.pyplot(Visualizer.plot_travel_patterns(), use_container_width=True)
        st.markdown("**Je Lage:**")
        st.dataframe(pd.DataFrame(wr.CEL_TRAVEL), hide_index=True, use_container_width=True)
        st.markdown("**Je Uhrposition (fallend 12 → 6):**")
        for k, v in wr.CEL_CLOCK_TECHNIQUE.items():
            st.markdown(f"- **{k}** – {v}")
        with st.expander("Muster-Glossar", expanded=False):
            for k, v in wr.CEL_PATTERN_GLOSSARY.items():
                st.markdown(f"- **{k}** – {v}")

    with t_amp:
        st.markdown("**Strom-Richtwerte (Gleichstrom)** – Wurzel DC−, Heiß-/Füll-/Decklage DC+ "
                    "bei den Pipeline-Grades (FOX CEL 70/75/80/90); klassisches E 6010 durchgehend DC+")
        st.dataframe(pd.DataFrame(wr.CEL_AMPERAGE), hide_index=True, use_container_width=True)
        st.info(wr.CEL_AMPERAGE_NOTE)
        st.divider()
        st.markdown("**Lagenaufbau**")
        c_in, c_out = st.columns([1.2, 1])
        with c_in:
            for p in wr.CEL_PASSES:
                with st.container(border=True):
                    st.markdown(
                        f"**{p['Lage']}**  ·  Elektrode {p['Elektrode']}  ·  Strom: {p['Strom']}\n\n"
                        f"*Technik:* {p['Technik']}\n\n*Zweck:* {p['Zweck']}"
                    )
        with c_out:
            nf = st.slider("Fülllagen für die Skizze", 0, 6, 1, 1, key="dh_nfill")
            wt2 = st.slider("Wandstärke (mm)", 3.0, 20.0, 8.0, 0.5, key="dh_wt2")
            st.pyplot(Visualizer.plot_bead_sequence(wt2, nf), use_container_width=True)
        st.caption(wr.CEL_PASS_COUNT)

        st.divider()
        with st.expander("🔑 Wurzelstrom nach Spaltweite + Keyhole steuern", expanded=False):
            st.dataframe(pd.DataFrame(wr.CEL_CURRENT_GAP), hide_index=True, use_container_width=True)
            st.info(wr.CEL_CURRENT_GAP_NOTE)
            st.markdown("**Keyhole lesen:**")
            for k, v in wr.CEL_KEYHOLE.items():
                st.markdown(f"- **{k}** – {v}")

        with st.expander("⏱️ Zeitfenster Wurzel → Heißlage → Fülllage", expanded=False):
            st.warning(wr.CEL_HOTPASS_TIMING)

        with st.expander("🌦️ Wetter & Umgebung", expanded=False):
            st.markdown(wr.CEL_WEATHER)

    with t_dev:
        st.markdown("**EWM Pico 350 (cel) – Geräteeinstellung für die Fallnaht**")
        st.dataframe(pd.DataFrame([{"Kenngröße": k, "Wert": v} for k, v in wr.EWM_PICO350.items()]),
                     hide_index=True, use_container_width=True)
        st.markdown(wr.EWM_PICO350_SETUP)
        st.caption("Angaben aus dem EWM-Datenblatt / der Betriebsanleitung Pico 350 cel puls. "
                   "Skalenwerte für Hotstart/Arcforce am Gerät bzw. im Handbuch ablesen.")

    with t_pre:
        st.markdown("**Vorwärm-Richtwerte** (rundum, vor dem Heften; reale Bauteiltemperatur zählt)")
        st.dataframe(pd.DataFrame(wr.CEL_PREHEAT), hide_index=True, use_container_width=True)
        st.warning(wr.CEL_INTERPASS_NOTE)
        st.caption("Genaue Werte über Kohlenstoffäquivalent (CET/CEV), Wandstärke und "
                   "Streckenenergie nach EN 1011-2 bzw. WPS.")

    with t_def:
        st.markdown("**A – Typische Fehler beim Fallnaht-Schweißen: Ursache und Abhilfe**")
        st.dataframe(pd.DataFrame(wr.CEL_DEFECTS), hide_index=True, use_container_width=True,
                     height=320)
        st.divider()
        st.markdown("**B – Offizielle Benennung nach ISO 6520-1 (für RT-/Röntgen-Protokolle)**")
        st.dataframe(pd.DataFrame(wr.RT_DEFECTS), hide_index=True, use_container_width=True,
                     height=420)
        st.info(wr.RT_NOTE)

    with t_seq:
        st.markdown("**Ablauf einer Rundnaht (Schritt für Schritt)**")
        for i, step in enumerate(wr.CEL_SEQUENCE, 1):
            st.markdown(f"**{i}.** {step}")


ALL_TABS = ["🪚 Smarte Säge", "📐 Geometrie", "🔥 Schweißen", "🧮 Rechner",
            "🎓 Fallnaht", "📚 Smart Data"]


def main():
    init_app_state()

    st.sidebar.title("🏗️ PipeCraft")
    st.sidebar.caption("Feld-Rechner Rohrleitungsbau")

    df_pipe = pd.DataFrame(columns=['DN'])
    try:
        with open("data/pipe_dimensions.json", "r") as f:
            data = json.load(f)
            df_pipe = pd.DataFrame(data)
    except Exception as e:
        st.error(f"Fehler beim Laden der Rohrdaten: {e}")

    calc = PipeCalculator(df_pipe)

    # Sidebar Settings
    with st.sidebar.expander("⚙️ Einstellungen", expanded=False):
        dn = st.selectbox("Standard Nennweite", df_pipe['DN'], index=5, key="global_dn",
                          help="Rohrgröße DN, für die Smart Data die Nachschlagewerte anzeigt.")
        pn = st.selectbox("Druckklasse", ["PN 6", "PN 10", "PN 16", "PN 25", "PN 40"], index=2, key="global_pn",
                          help="Druckstufe. Bestimmt in Smart Data die Flansch- und Schraubenmaße.")
        st.radio("Längen-Anzeige", ["mm", "Zoll"], key="global_unit", horizontal=True,
                 help="Betrifft Nachschlage-Anzeigen (Rohrmaße). Eingabefelder bleiben in mm.")

    st.sidebar.divider()
    st.sidebar.caption(
        "⚠️ Alle Zahlen sind **Richtwerte**. Verbindlich sind die freigegebene WPS, "
        "die Norm (API 1104 / ISO / EN) und die Projektspezifikation."
    )

    # --- Hauptmenü: immer sichtbare Chip-Leiste oben (bricht auf dem Handy um) ---
    tabs = ALL_TABS
    if st.session_state.active_tab not in tabs:
        st.session_state.active_tab = tabs[0]

    sel = st.pills("Bereich", tabs, selection_mode="single",
                   default=st.session_state.active_tab, key="nav_pills",
                   label_visibility="collapsed")
    active = sel or st.session_state.active_tab
    if active != st.session_state.active_tab:
        st.session_state.active_tab = active
        st.rerun()
    st.divider()

    if st.session_state.active_tab == "🪚 Smarte Säge":
        render_smart_saw(calc, df_pipe, dn, pn)
    elif st.session_state.active_tab == "📐 Geometrie":
        render_geometry_tools(calc, df_pipe)
    elif st.session_state.active_tab == "🔥 Schweißen":
        render_weld_tools(calc, df_pipe)
    elif st.session_state.active_tab == "🧮 Rechner":
        render_field_calc(calc, df_pipe)
    elif st.session_state.active_tab == "🎓 Fallnaht":
        render_downhill_school(calc, df_pipe)
    elif st.session_state.active_tab == "📚 Smart Data":
        render_tab_handbook(calc, dn, pn)

def render_geometry_tools(calc: PipeCalculator, df: pd.DataFrame):
    st.markdown('<div class="machine-header-geo">📐 GEOMETRIE & BERECHNUNG</div>', unsafe_allow_html=True)
    geo_tabs = st.tabs([
        "2D Etage (S-Schlag)", "3D Raum-Etage (Rolling)", "Bogen (Standard)",
        "🦞 Segment-Bogen", "Stutzen", "📐 Spalt-Ausgleich",
        "Stutzen schräg/versetzt", "Rohr-Verschneidung", "Reduzierung",
        "Passstück 3D", "Dehnungsausgleicher",
    ])
    
    with geo_tabs[0]:
        render_tool_help("geo_2d")
        c1, c2 = st.columns([1, 2])
        with c1:
            with st.container(border=True):
                with st.form(key="geo_2d_form"):
                    dn = st.selectbox("Nennweite", df['DN'], index=5, key="2d_dn")
                    offset = st.number_input("Versprung (H) [mm]", value=500.0, step=10.0, key="2d_off")
                    angle = st.number_input("Fittings (°)", value=45.0, min_value=0.1, max_value=90.0, step=0.5, key="2d_ang")
                    submit_2d = st.form_submit_button("Berechnen 🚀", type="primary", use_container_width=True)
                
                if submit_2d:
                    res = calc.calculate_2d_offset(dn, offset, angle)
                    st.session_state.calc_res_2d = res 
        
        with c2:
            if 'calc_res_2d' in st.session_state:
                res = st.session_state.calc_res_2d
                if "error" in res: st.error(res["error"])
                else:
                    st.markdown("**Ergebnis**")
                    m1, m2 = st.columns(2)
                    m1.metric("Zuschnitt (Rohr)", f"{res['cut_length']:.1f} mm")
                    m2.metric("Etagenlänge", f"{res['hypotenuse']:.1f} mm")
                    st.info(f"Benötigter Platz (Länge): {res['run']:.1f} mm")
                    
                    if st.button("➡️ An Säge (2D)", key="btn_2d_saw"):
                        st.session_state.active_tab = "🪚 Smarte Säge"
                        st.session_state.transfer_cut_length = res['cut_length']
                        st.rerun()

    with geo_tabs[1]:
        render_tool_help("geo_3d")
        c1, c2 = st.columns([1, 2])
        with c1:
            with st.container(border=True):
                with st.form(key="geo_3d_form"):
                    dn_roll = st.selectbox("Nennweite", df['DN'], index=5, key="3d_dn")
                    roll = st.number_input("Roll (Seite) [mm]", value=300.0, step=10.0)
                    set_val = st.number_input("Set (Höhe) [mm]", value=400.0, step=10.0)
                    # height = st.number_input("Länge (Run) [mm]", value=500.0, step=10.0) # Removed, calculated
                    # angle_std = st.selectbox("Fitting Typ", [45, 60, 90])
                    fit_angle = st.number_input("Fitting Typ (°)", value=45.0, min_value=0.1, max_value=179.9, step=0.5, format="%.1f")
                    
                    submit_3d = st.form_submit_button("Berechnen 🚀", type="primary", use_container_width=True)
                
                if submit_3d:
                    # Logic: We know Roll and Set. The Diagonal_Base is fixed.
                    # We want to use specific Fittings (e.g. 45deg).
                    # This determines the TRAVEL and RUN.
                    
                    diag_base = (roll**2 + set_val**2)**0.5
                    
                    # Hypotenuse (Travel) = Diag_Base / sin(angle)
                    # Run = Diag_Base / tan(angle)
                    
                    if fit_angle == 0: fit_angle = 90
                    rad_angle = math.radians(fit_angle)
                    
                    try:
                        true_offset = diag_base # The "Offset" in the plane of the fitting
                        travel_center = true_offset / math.sin(rad_angle)
                        run_length = true_offset / math.tan(rad_angle)
                        
                        # Deduction
                        ded = calc.get_deduction(f"Bogen (Zuschnitt) {fit_angle}°", dn_roll, "PN 16", fit_angle) # Dummy PN
                        cut_len = travel_center - (2 * ded)
                        
                        st.session_state.calc_res_3d = {
                            "roll": roll, "set": set_val, 
                            "diag_base": diag_base,
                            "travel_center": travel_center,
                            "run_length": run_length,
                            "cut_length": cut_len,
                            "deduction": ded,
                            "angle": fit_angle,
                            "set_val": set_val, # Passed for visualizer
                            "roll_val": roll    # Passed for visualizer
                        }
                    except ZeroDivisionError:
                        st.error("Winkel darf nicht 0 sein")

        with c2:
            if 'calc_res_3d' in st.session_state:
                res = st.session_state.calc_res_3d
                
                col_res1, col_res2 = st.columns(2)
                col_res1.metric("Zuschnitt (Rohr)", f"{res['cut_length']:.1f} mm")
                col_res1.caption(f"Abzug 2x {res['deduction']:.1f} mm")
                
                col_res2.metric("Rohrweg (Mitte)", f"{res['travel_center']:.1f} mm")
                col_res2.caption(f"Hypotenuse bei {res['angle']}°")
                
                st.info(f"Benötigte Baulänge (Run): {res['run_length']:.1f} mm")
                
                if st.button("➡️ An Säge (3D)", key="btn_3d_saw"):
                    st.session_state.active_tab = "🪚 Smarte Säge"
                    st.session_state.transfer_cut_length = res['cut_length']
                    st.rerun()
                
                if PLOTLY_AVAILABLE:
                    st.markdown("### 🧊 3D Vorschau")
                    fig = Visualizer.plot_rolling_offset_interactive(res['roll_val'], res['set_val'], res['run_length'], dn_roll)
                    if fig: st.plotly_chart(fig, use_container_width=True)


    with geo_tabs[2]:
        st.markdown("##### Standard Bogen-Rechner")
        render_tool_help("geo_bogen")
        c_in, c_out = st.columns([1, 1.6])

        with c_in:
            with st.container(border=True):
                st.markdown("**Eingabe**")
                dn_bend = st.selectbox("Nennweite", df['DN'], index=6, key="bend_dn")
                angle_bend = st.number_input("Winkel (°)", min_value=0.0, max_value=180.0,
                                             value=90.0, step=0.5, key="bend_angle")
                row_b = calc.get_row(dn_bend)
                st.caption(
                    f"Bogenradius (BA3): **{float(row_b['Radius_BA3']):.0f} mm**  ·  "
                    f"Ø außen: **{float(row_b['D_Aussen']):.1f} mm**"
                )

        bend_res = calc.calculate_bend_details(dn_bend, angle_bend)

        with c_out:
            with st.container(border=True):
                st.markdown(f"**Ergebnis — DN {dn_bend} / {angle_bend:.1f}°**")
                st.metric("Vorbau (Z-Maß)", f"{bend_res['vorbau']:.1f} mm",
                          help="Achsmaß Rohrende → Achsen-Schnittpunkt = Fitting-Abzug pro Seite.")
                st.divider()
                st.caption("Abwicklungslängen über den Bogen")
                m1, m2, m3 = st.columns(3)
                m1.metric("Rücken (außen)", f"{bend_res['bogen_aussen']:.1f} mm")
                m2.metric("Mitte (Achse)", f"{bend_res['bogen_mitte']:.1f} mm")
                m3.metric("Bauch (innen)", f"{bend_res['bogen_innen']:.1f} mm")

        st.caption(
            "ℹ️ **Vorbau** = Abzug pro Seite bei der Sägelängen-Berechnung.  "
            "**Rücken / Bauch** = Abwicklung außen bzw. innen — zum Anreißen von Falten- oder Segmentschnitten."
        )

    with geo_tabs[3]:
        st.markdown("##### 🦞 Segment-Bogen (Lobster Back)")
        st.caption("Ein Bogen, aus geraden Rohrstücken mit Gehrungsschnitten zusammengeschweißt "
                   "— wenn kein fertiger Bogen da ist.")
        render_tool_help("geo_segment")
        c_in, c_out = st.columns([1, 1.6])

        with c_in:
            with st.container(border=True):
                st.markdown("**Eingabe**")
                dn_seg = st.selectbox("Nennweite", df['DN'], index=8, key="seg_dn")
                r_seg = st.number_input("Bogenradius R [mm] (Rohrmitte)", min_value=1.0, value=1000.0,
                                        step=10.0, key="seg_r")
                cs1, cs2 = st.columns(2)
                n_seg = cs1.number_input("Anzahl Segmente", min_value=2, value=4, step=1, key="seg_n",
                                         help="Gerade Rohrstücke im Bogen. Mehr Segmente = "
                                              "glatterer Bogen, aber mehr Nähte.")
                tot_ang = cs2.number_input("Gesamtwinkel (°)", min_value=1.0, max_value=180.0,
                                           value=90.0, step=5.0, key="seg_ang")

        res_seg = calc.calculate_segment_bend(dn_seg, r_seg, int(n_seg), tot_ang)

        with c_out:
            if "error" in res_seg:
                st.error(res_seg["error"])
            else:
                with st.container(border=True):
                    st.markdown(f"**DN {dn_seg} · {res_seg['num_segments']} Segmente "
                                f"({res_seg['num_segments'] - 2} ganze + 2 halbe) · "
                                f"{res_seg['num_welds']} Nähte**")
                    h1, h2, h3 = st.columns(3)
                    h1.metric("Sägeblatt-Neigung", f"{res_seg['miter_angle']:.1f}°",
                              help="So schräg stellst du das Sägeblatt für jede Schnittfläche.")
                    h2.metric("Knick je Naht", f"{res_seg['turn_per_weld']:.1f}°",
                              help="Um so viel ändert sich die Rohrachse an jeder Schweißnaht "
                                   "(= 2 × Sägeblatt-Neigung).")
                    h3.metric("Ø außen", f"{res_seg['od']:.1f} mm")

        if "error" not in res_seg:
            st.pyplot(Visualizer.plot_segment_bend(
                r_seg, res_seg['od'], res_seg['num_segments'], tot_ang), use_container_width=True)

            st.markdown("**Anreißmaße** (Abwicklung an der Rohr-Außenkontur, gemessen am fertigen Stück)")
            r1, r2 = st.columns(2)
            with r1:
                st.markdown("Ganzes Segment · *beide Enden geschnitten*")
                st.metric("Rücken (außen, lang)", f"{res_seg['mid_back']:.1f} mm")
                st.metric("Achse (Mitte)", f"{res_seg['mid_center']:.1f} mm")
                st.metric("Bauch (innen, kurz)", f"{res_seg['mid_belly']:.1f} mm")
            with r2:
                st.markdown("Endstück · *ein Ende geschnitten, ein Ende gerade*")
                st.metric("Rücken", f"{res_seg['end_back']:.1f} mm")
                st.metric("Achse", f"{res_seg['end_center']:.1f} mm")
                st.metric("Bauch", f"{res_seg['end_belly']:.1f} mm")
            with st.expander("📐 Ein Segment flach (Anreißhilfe)", expanded=False):
                st.pyplot(Visualizer.plot_segment_schematic(
                    res_seg['mid_back'], res_seg['mid_belly'], res_seg['od'], res_seg['miter_angle']),
                    use_container_width=False)
            st.caption(
                "**So geht's:** Rohr rundum in Rücken- und Bauchlinie teilen. Am Rücken (außen) den "
                "langen Wert abtragen, am Bauch (innen) den kurzen – Punkte mit einem Papierstreifen "
                "zur schrägen Schnittlinie verbinden, sägen, Segmente aneinanderlegen und heften. "
                "Die 2 Endstücke sind halbe Segmente, damit die Anschlüsse gerade sind."
            )

    with geo_tabs[4]:
        st.markdown("##### Stutzen-Abwicklung (Sattelschnitt)")
        st.caption(
            "1:1-Schablone für einen **rechtwinklig und mittig** aufgesetzten Stutzen "
            "(Set-on). Alle Maße auf Basis der Rohr-Außendurchmesser."
        )
        render_tool_help("geo_stutzen")

        c_in, c_out = st.columns([1, 1.7])
        with c_in:
            with st.container(border=True):
                st.markdown("**Eingabe**")
                dnh = st.selectbox("Hauptrohr DN", df['DN'], index=8, key="st_dn1")
                dns = st.selectbox("Stutzen DN", df['DN'], index=5, key="st_dn2")
                n_st = st.select_slider(
                    "Stationen (Umfangsteilung)", options=[8, 12, 16, 24, 36, 48],
                    value=24, key="st_n"
                )

        res = calc.calculate_branch_development(dnh, dns, n_st)

        with c_out:
            if "error" in res:
                st.error(res["error"])
            else:
                with st.container(border=True):
                    st.markdown(f"**Ergebnis — Stutzen DN {dns} auf Hauptrohr DN {dnh}**")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Stutzen-Umfang", f"{res['branch_circ']:.1f} mm")
                    m2.metric("Größter Abtrag h", f"{res['h_max']:.1f} mm")
                    m3.metric("Ø-Verhältnis d/D", f"{res['r'] / res['R']:.2f}")
                    st.caption(
                        "**h** = Materialabtrag ab der Anreißlinie im tiefsten Punkt "
                        "(Kontakt am Hauptrohr-Scheitel). **s** = Maßband-Weg um den "
                        "Stutzen ab derselben Linie (Station 0 = Scheitelpunkt)."
                    )

        if "error" not in res:
            fig = Visualizer.plot_branch_development(
                res['dev_s'], res['dev_h'], res['branch_circ'],
                res['hole_u'], res['hole_a']
            )
            st.pyplot(fig, use_container_width=True)

            c_tab, c_howto = st.columns([1, 1])
            with c_tab:
                st.markdown("**Anreißtabelle Stutzen**")
                tbl = pd.DataFrame(res['stations'])
                st.dataframe(tbl, hide_index=True, use_container_width=True, height=280)
                st.download_button(
                    "📥 Tabelle als Excel", Exporter.to_excel(tbl),
                    f"Stutzen_DN{dns}_auf_DN{dnh}.xlsx", key="st_xls"
                )
            with c_howto:
                st.markdown("**Schablone übertragen**")
                st.markdown(
                    "1. Am Stutzen eine **Anreißlinie** rundum anzeichnen "
                    "(Abstand vom Rohrende frei, aber ≥ größter Abtrag).\n"
                    "2. Maßband um den Stutzen legen, **Nullpunkt** = Punkt in Richtung "
                    "der Hauptrohrachse (Scheitelkontakt).\n"
                    "3. Bei jedem `s`-Wert einen Strich, dort `h` von der Anreißlinie "
                    "**Richtung Rohrende** abtragen.\n"
                    "4. Punkte zur Wellenlinie verbinden → Brennschnitt am Stutzen.\n"
                    "5. Ausschnitt im Hauptrohr nach der **rechten Kurve** anzeichnen "
                    "(Nullpunkt = Rohrscheitel)."
                )
            
    with geo_tabs[5]:
        st.markdown("##### 📐 Keilspalt-Rechner (Angular Misalignment)")
        st.caption("Berechnet den Korrekturschnitt für nicht planparallele Rohrenden.")
        render_tool_help("geo_spalt")

        c1, c2 = st.columns([1, 1.5])
        
        with c1:
            with st.container(border=True):
                dn_sel = st.selectbox("Nennweite", df['DN'], index=5, key="gap_dn_geo")
                st.markdown("**Spaltmaße (mm)**")
                cg1, cg2 = st.columns(2)
                g12 = cg1.number_input("12 Uhr (Oben)", 0.0, 100.0, 5.0, step=0.5, key="g12_geo")
                g6 = cg2.number_input("6 Uhr (Unten)", 0.0, 100.0, 0.0, step=0.5, key="g6_geo")
                
                cg3, cg4 = st.columns(2)
                g3 = cg3.number_input("3 Uhr (Rechts)", 0.0, 100.0, 2.0, step=0.5, key="g3_geo")
                g9 = cg4.number_input("9 Uhr (Links)", 0.0, 100.0, 2.0, step=0.5, key="g9_geo")
                
                if st.button("Berechnen 📐", type="primary", use_container_width=True, key="btn_calc_wedge"):
                    res = calc.calculate_wedge_gap(dn_sel, {'12': g12, '3': g3, '6': g6, '9': g9})
                    st.session_state.gap_res = res
        
        with c2:
            if 'gap_res' in st.session_state:
                res = st.session_state.gap_res
                
                if res['max_gap'] == 0:
                    st.success("✅ Rohrenden sind parallel!")
                else:
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Klaffen", f"{res['angle']}°")
                    m2.metric("Max. Spalt", f"{res['max_gap']} mm")
                    m3.metric("Ausrichtung", res['orientation'])
                    
                    st.info(f"Die Rohrenden klaffen am stärksten bei **{res['orientation']}**. Dort ist der Spalt {res['max_gap']} mm höher.")
                    
                    st.markdown("###### ✂️ Anreiß-Tabelle (Maßband & Abtrag)")
                    cut_df = pd.DataFrame(res['cut_data'])
                    
                    # Highlight Columns
                    st.dataframe(
                        cut_df, 
                        use_container_width=True,
                        column_config={
                            "Pos": st.column_config.TextColumn("Uhrzeit"),
                            "Maßband (mm)": st.column_config.NumberColumn("Maßband (Umfang)", format="%.0f mm"),
                            "Abtrag (mm)": st.column_config.NumberColumn("Abtrag (Schnitt)", format="%.1f mm"),
                        },
                        hide_index=True
                    )
                    
                    st.caption("ℹ️ 'Maßband' ist der Weg am Umfang ab 12 Uhr. 'Abtrag' ist das Maß, das weg muss.")

                    with st.expander("📝 Anleitung: So überträgst du das Maß", expanded=False):
                        st.markdown("""
                        1.  **Nullpunkt (12 Uhr):** Markiere "Oben" auf dem Rohr. Das ist 0 mm.
                        2.  **Umfang anzeichnen:** Lege das Maßband an. Mache bei jedem Wert aus der Spalte `Maßband (mm)` einen kleinen Strich.
                        3.  **Tiefe übertragen:** An jedem Strich misst du nun vom Rohrende nach hinten den Wert `Abtrag (mm)` und machst ein Kreuz.
                        4.  **Verbinden:** Verbinde die Kreuze zu einer Wellenlinie (z.B. mit einem Papierstreifen).
                        5.  **Schneiden:** Diese Linie ist dein Schnitt.
                        """)

    # ---------------------------------------------- Stutzen schräg/versetzt --
    with geo_tabs[6]:
        st.markdown("##### Stutzen-Abwicklung – schräg angestellt / außermittig")
        render_tool_help("geo_stutzen_schraeg")
        c_in, c_out = st.columns([1, 1.6])
        with c_in:
            with st.container(border=True):
                st.markdown("**Eingabe**")
                dnh = st.selectbox("Hauptrohr DN", df['DN'], index=8, key="ss_dn1")
                dns = st.selectbox("Stutzen DN", df['DN'], index=5, key="ss_dn2")
                beta = st.slider("Anstellwinkel β (° aus der Senkrechten)", 0, 70, 0, 1, key="ss_b")
                ecc = st.slider("Seitlicher Versatz e (mm)", 0.0, 100.0, 0.0, 1.0, key="ss_e")
                nst = st.select_slider("Stationen", options=[12, 16, 24, 36, 48], value=24, key="ss_n")
        res = calc.calculate_branch_development(dnh, dns, nst, beta_deg=beta, offset_e=ecc)
        with c_out:
            if "error" in res:
                st.error(res["error"])
            else:
                with st.container(border=True):
                    st.markdown(f"**Ergebnis — DN {dns} auf DN {dnh}, β = {res['beta_deg']:.0f}°, e = {res['offset_e']:.0f} mm**")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Stutzen-Umfang", f"{res['branch_circ']:.1f} mm")
                    m2.metric("Größter Abtrag h", f"{res['h_max']:.1f} mm")
                    m3.metric("Ø-Verhältnis d/D", f"{res['r']/res['R']:.2f}")
        if "error" not in res:
            st.pyplot(Visualizer.plot_branch_development(
                res['dev_s'], res['dev_h'], res['branch_circ'], res['hole_u'], res['hole_a']),
                use_container_width=True)
            st.dataframe(pd.DataFrame(res['stations']), hide_index=True, use_container_width=True, height=260)
            st.caption("β und e machen den Sattel unsymmetrisch – Nullpunkt der Schablone ist "
                       "weiterhin der Punkt in Richtung Hauptrohrachse. Bei β > 0 die Schablone "
                       "seitenrichtig auflegen (Markierung am Stutzen anbringen).")

    # ---------------------------------------------- Rohr-Verschneidung -------
    with geo_tabs[7]:
        st.markdown("##### Rohr-Verschneidung – gleicher Durchmesser")
        render_tool_help("geo_verschneidung")
        c_in, c_out = st.columns([1, 1.6])
        with c_in:
            with st.container(border=True):
                dn_v = st.selectbox("Nennweite (beide Rohre)", df['DN'], index=8, key="v_dn")
                mode_v = st.radio("Fall", ["Abzweig / Lateral", "Y symmetrisch"], key="v_mode")
                ang_v = st.slider("Winkel zwischen den Rohrachsen (°)", 15, 165, 90, 1, key="v_ang")
                nst_v = st.select_slider("Stationen", options=[12, 16, 24, 36], value=24, key="v_n")
        rv = calc.calculate_equal_pipe_miter(dn_v, ang_v, nst_v, mode_v)
        with c_out:
            if "error" in rv:
                st.error(rv["error"])
            else:
                with st.container(border=True):
                    st.markdown(f"**Ergebnis — DN {dn_v}, Achswinkel {ang_v}°**")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Gehrungswinkel je Rohr", f"{rv['miter_angle']:.1f}°")
                    m2.metric("Rohr-Umfang", f"{rv['circ']:.1f} mm")
                    m3.metric("Abtrag Ferse→Zunge", f"{rv['h_peak']:.1f} mm")
                    st.caption("Bei gleichem Ø ist der Schnitt **eben** (reine Gehrung). "
                               "Beide Rohre werden identisch geschnitten.")
        if "error" not in rv:
            st.pyplot(Visualizer.plot_template_curve(
                rv['dev_s'], rv['dev_h'], rv['circ'],
                f"Gehrungs-Schablone · {rv['miter_angle']:.1f}°"), use_container_width=True)
            st.dataframe(pd.DataFrame(rv['stations']), hide_index=True, use_container_width=True, height=260)

    # ---------------------------------------------- Reduzierung ------------
    with geo_tabs[8]:
        st.markdown("##### Reduzierung – Abwicklung (Kegelstumpf)")
        render_tool_help("geo_reduzierung")
        c_in, c_out = st.columns([1, 1.5])
        with c_in:
            with st.container(border=True):
                use_dn = st.checkbox("Ø aus DN-Tabelle", value=True, key="rd_usedn")
                if use_dn:
                    d1 = _od_from_dn(df, st.selectbox("großes DN", df['DN'], index=9, key="rd_d1"), 200.0)
                    d2 = _od_from_dn(df, st.selectbox("kleines DN", df['DN'], index=6, key="rd_d2"), 100.0)
                else:
                    d1 = st.number_input("großer Ø (mm)", value=219.1, min_value=1.0, step=1.0, key="rd_d1m")
                    d2 = st.number_input("kleiner Ø (mm)", value=114.3, min_value=1.0, step=1.0, key="rd_d2m")
                axl = st.number_input("Baulänge L (mm)", value=150.0, min_value=1.0, step=10.0, key="rd_l")
                ecc = st.radio("Bauart", ["konzentrisch", "exzentrisch"], key="rd_ecc")
                nst_r = st.select_slider("Stationen (nur exzentrisch)", options=[8, 12, 16, 24],
                                         value=12, key="rd_n")
        rr = calc.calculate_reducer(d1, d2, axl, eccentric=(ecc == "exzentrisch"), num_stations=nst_r)
        with c_out:
            if "error" in rr:
                st.error(rr["error"])
            elif rr["type"] == "konzentrisch":
                with st.container(border=True):
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Mantellinie (slant)", f"{rr['slant']:.1f} mm")
                    m2.metric("Sektorwinkel", f"{rr['sector_deg']:.1f}°")
                    m3.metric("Radien R_außen / R_innen", f"{rr['r_out']:.0f} / {rr['r_in']:.0f}")
                    st.caption(f"Bogen außen {rr['arc_out']:.1f} mm (= großer Umfang), "
                               f"Bogen innen {rr['arc_in']:.1f} mm.")
                if rr['sector_deg'] > 360:
                    st.warning("⚠️ Sektorwinkel > 360° – die Abwicklung überlappt sich. "
                               "Sehr kurze, stark reduzierende Konen als Segmentschuss ausführen "
                               "oder in Ringe teilen.")
                st.pyplot(Visualizer.plot_cone_sector(rr['r_out'], rr['r_in'], min(rr['sector_deg'], 359.5)),
                          use_container_width=False)
            else:
                with st.container(border=True):
                    m1, m2 = st.columns(2)
                    m1.metric("Mantellinie (gerade Seite)", f"{rr['slant']:.1f} mm")
                    m2.metric("Versatz", f"{rr['offset']:.1f} mm")
                    st.caption(f"Sehne große Kante {rr['chord_big']:.1f} mm · "
                               f"kleine Kante {rr['chord_small']:.1f} mm (Stechzirkel).")
                st.dataframe(pd.DataFrame(rr['stations']), hide_index=True, use_container_width=True)
                st.caption("Wahre Längen je Station – flach übertragen: Dreieck für Dreieck von der "
                           "Naht aus abschlagen (Elementlinie, dann Diagonale zur nächsten Station). "
                           "Nur eine Hälfte gerechnet – die zweite ist gespiegelt.")

    # ---------------------------------------------- Passstück 3D ----------
    with geo_tabs[9]:
        st.markdown("##### Passstück 3D – aus zwei vermessenen Anschlusspunkten")
        render_tool_help("geo_passstueck")
        c_in, c_out = st.columns([1, 1.4])
        with c_in:
            with st.container(border=True):
                st.markdown("**Achsversatz Anschluss 1 → Anschluss 2 (mm)**")
                dx = st.number_input("Lauf ΔX (entlang Rohrachse 1)", value=800.0, step=10.0, key="sp_x")
                dy = st.number_input("Seite ΔY", value=300.0, step=10.0, key="sp_y")
                dz = st.number_input("Höhe ΔZ", value=400.0, step=10.0, key="sp_z")
                elb = st.number_input("Bogenwinkel (°)", value=45.0, min_value=1.0, max_value=89.0,
                                      step=0.5, key="sp_e")
        sp = calc.calculate_spool_3d(dx, dy, dz, elb)
        with c_out:
            if "error" in sp:
                st.warning(sp["error"])
            else:
                with st.container(border=True):
                    st.markdown("**Ergebnis**")
                    m1, m2 = st.columns(2)
                    m1.metric("Wahrer Achsversatz", f"{sp['true_offset']:.1f} mm")
                    m2.metric("Raumdiagonale", f"{sp['space_diag']:.1f} mm")
                    if sp.get("straight"):
                        st.success("Anschlüsse fluchten – gerades Passstück genügt.")
                    else:
                        m3, m4 = st.columns(2)
                        m3.metric("Rohrweg Mitte-Mitte", f"{sp['travel']:.1f} mm")
                        m4.metric("Verdrehung (Roll)", f"{sp['roll_angle']:.1f}°")
                        st.caption(f"Baulänge in Laufrichtung {sp['run']:.1f} mm; "
                                   f"verbleibende gerade Länge auf ΔX ≈ {sp['run_vs_dx']:.1f} mm. "
                                   f"Zwei Bögen à {sp['elbow_deg']:.0f}°.")
                        if sp['run_vs_dx'] < 0:
                            st.warning("⚠️ Die zwei Bögen brauchen mehr Baulänge, als ΔX hergibt "
                                       "(verbleibende Länge negativ). Steileren Bogenwinkel wählen "
                                       "oder den Versatz anders aufteilen.")
                if not sp.get("straight"):
                    st.pyplot(Visualizer.plot_2d_offset(sp['run'], sp['true_offset']),
                              use_container_width=False)

    # ---------------------------------------------- Dehnungsausgleicher ---
    with geo_tabs[10]:
        st.markdown("##### Dehnungsausgleicher – Wärmedehnung & Vorauslegung")
        render_tool_help("geo_dehnung")
        c_in, c_out = st.columns([1, 1.4])
        with c_in:
            with st.container(border=True):
                mat = st.selectbox("Werkstoff", ["Stahl unlegiert (α≈12)", "Austenit 1.4404 (α≈16,5)",
                                                 "eigener Wert"], key="ex_mat")
                alpha = {"Stahl unlegiert (α≈12)": 12.0, "Austenit 1.4404 (α≈16,5)": 16.5}.get(
                    mat, st.number_input("α (10⁻⁶ / K)", value=12.0, step=0.5, key="ex_a"))
                Ln = st.number_input("Leitungslänge L (m)", value=30.0, min_value=0.1, step=1.0, key="ex_l")
                dT = st.number_input("Temperaturhub ΔT (K)", value=120.0, step=5.0, key="ex_dt")
                od = _od_from_dn(df, st.selectbox("DN", df['DN'], index=8, key="ex_dn"), 168.3)
                emod = st.number_input("E-Modul (GPa)", value=210.0, step=5.0, key="ex_e",
                                       help="Stahl ~210, Austenit ~200 (warm weniger).")
                sa = st.number_input("zul. Spannung Sa (MPa)", value=100.0, min_value=10.0, step=10.0,
                                     key="ex_sa", help="Zulässiger Spannungsbereich für Sekundärspannungen.")
                shp = st.radio("Form", ["U-Bogen (Lyra)", "Z-Bogen", "L-Bogen"], key="ex_shp")
        ex = calc.calculate_expansion(alpha, Ln, dT, emod, od, sa, shp)
        with c_out:
            with st.container(border=True):
                st.markdown("**Ergebnis**")
                m1, m2 = st.columns(2)
                m1.metric("Wärmedehnung ΔL", f"{ex['dL']:.1f} mm")
                m2.metric("Schenkellänge (Richtwert)", f"{ex['leg_m']:.2f} m")
                st.latex(r"\Delta L = \alpha \cdot L \cdot \Delta T \qquad "
                         r"L_{Schenkel} \approx \sqrt{\dfrac{3\,E\,D\,\Delta L_{wirk}}{S_a}}")
                st.caption(f"ΔL_wirksam je Schenkel = {ex['dL_eff']:.1f} mm (Formfaktor {ex['factor']}). "
                           "Guided-Cantilever-Näherung – **ersetzt keine Flexibilitätsanalyse** "
                           "(Rohrklasse, Festpunkte, Führungen, Gewicht, Innendruck).")
                if ex['leg_m'] > 12:
                    st.warning("⚠️ Sehr langer Schenkel – für die Baustelle meist unrealistisch. "
                               "Prüfen: Vorspannung (Kaltverformung), mehrere kleinere Bögen, "
                               "Kompensator, oder Sa/ΔT realistischer ansetzen.")
                elif ex['leg_m'] < 0.3:
                    st.info("Sehr kurzer Schenkel – ΔL ist gering; oft reicht die natürliche "
                            "Rohrflexibilität ohne eigenen Ausgleicher.")
                _pdf_button("Dehnungsausgleicher",
                            {"alpha (1e-6/K)": alpha, "Laenge (m)": Ln, "dT (K)": dT,
                             "DN-Aussen (mm)": round(od, 1), "E (GPa)": emod, "Sa (MPa)": sa, "Form": shp},
                            {"Waermedehnung dL (mm)": round(ex['dL'], 1),
                             "Schenkellaenge (m)": round(ex['leg_m'], 2)},
                            key="pdf_expansion")
            st.pyplot(Visualizer.plot_expansion_loop(shp, ex['leg_mm']), use_container_width=True)


if __name__ == "__main__":
    main()
