import json
import time
import math
from dataclasses import asdict
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

from modules.models import FittingItem, SavedCut
from modules.calculations import (
    PipeCalculator, HandbookCalculator,
    FieldCalc, PipeRef,
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
    /* Der Streamlit-Kopfbereich ist 60 px hoch und liegt mit hohem z-index
       ueber dem Inhalt. Bei 2rem Abstand steckte die Menueleiste zur Haelfte
       darunter - darum so viel Luft, dass sie frei darunter liegt. */
    div[data-testid="stMainBlockContainer"] { padding-top: 4.75rem; padding-bottom: 3rem; }
    div[data-testid="stSidebar"] { min-width: 300px !important; }
    h1, h2, h3, h4, h5 { font-family: 'Segoe UI', sans-serif; font-weight: 600; color: #1e293b; }
    .machine-header-saw { border-bottom: 4px solid #f97316; color: #f97316; padding: 5px 0; font-weight: 700; font-size: 1.2rem; margin-bottom: 15px; text-transform: uppercase; }
    .machine-header-geo { border-bottom: 4px solid #0ea5e9; color: #0ea5e9; padding: 5px 0; font-weight: 700; font-size: 1.2rem; margin-bottom: 15px; text-transform: uppercase; }
    .machine-header-doc { border-bottom: 4px solid #64748b; color: #64748b; padding: 5px 0; font-weight: 700; font-size: 1.2rem; margin-bottom: 15px; text-transform: uppercase; }
    div[data-testid="stVerticalBlockBorderWrapper"] { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.5rem; }
    div[data-testid="stMetric"] { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 15px; }

    /* --- Hauptmenue (st.pills) ---------------------------------------------
       Streamlit gibt dem Emoji-Icon weniger Hoehe, als es braucht (14 px bei
       19 px Inhalt) und schneidet es unten ab - die Reiter sahen dadurch halb
       verdeckt aus. Icon frei atmen lassen und die Leiste etwas groesser
       machen: es ist das Hauptmenue, nicht ein Nebenschalter. */
    div[data-testid="stButtonGroup"] [data-testid="stIconEmoji"] {
        height: auto !important;
        line-height: 1.3 !important;
        overflow: visible !important;
        font-size: 1.05rem !important;
    }
    div[data-testid="stButtonGroup"] button,
    div[data-testid="stButtonGroup"] button > div,
    div[data-testid="stButtonGroup"] button > div > span {
        overflow: visible !important;
    }
    div[data-testid="stButtonGroup"] button {
        min-height: 44px !important;
        padding: 6px 18px !important;
        border: 1px solid #cbd5e1 !important;
        background: #f8fafc !important;
    }
    /* Der aktive Bereich muss sich deutlich abheben - sonst sucht man, wo man
       gerade ist. Streamlit markiert ihn als role="radio" mit aria-checked. */
    div[data-testid="stButtonGroup"] button[aria-checked="true"],
    div[data-testid="stButtonGroup"] button[data-selected="true"] {
        background: #1e293b !important;
        border-color: #1e293b !important;
    }
    div[data-testid="stButtonGroup"] button[aria-checked="true"] p,
    div[data-testid="stButtonGroup"] button[data-selected="true"] p,
    div[data-testid="stButtonGroup"] button[aria-checked="true"] [data-testid="stIconEmoji"],
    div[data-testid="stButtonGroup"] button[data-selected="true"] [data-testid="stIconEmoji"] {
        color: #ffffff !important;
    }
    div[data-testid="stButtonGroup"] button:hover {
        border-color: #94a3b8 !important;
        background: #eef2f7 !important;
    }
    div[data-testid="stButtonGroup"] button p {
        font-size: 0.95rem !important;
        font-weight: 600 !important;
    }
    div[data-testid="stButtonGroup"] {
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 6px !important;
    }

    /* --- RESPONSIVE / MOBILE --- */
    @media (max-width: 1024px) {
        div[data-testid="stSidebar"] { min-width: 250px !important; }
        div[data-testid="stMainBlockContainer"] { padding-left: 1rem !important; padding-right: 1rem !important; }
        h1 { font-size: 1.8rem !important; }
    }
    @media (max-width: 768px) {
        div[data-testid="stSidebar"] { min-width: 100% !important; }
        div[data-testid="stMainBlockContainer"] { padding-left: 0.6rem !important; padding-right: 0.6rem !important; }

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

DATA_DIR = Path(__file__).parent / "data"


@st.cache_data(show_spinner=False)
def load_pipe_table() -> pd.DataFrame:
    """Rohrmaß-Tabelle laden (Pfad relativ zu dieser Datei, UTF-8)."""
    fp = DATA_DIR / "pipe_dimensions.json"
    try:
        with open(fp, "r", encoding="utf-8") as f:
            return pd.DataFrame(json.load(f))
    except FileNotFoundError:
        st.error(f"Rohrdaten nicht gefunden: {fp}")
    except (json.JSONDecodeError, ValueError) as e:
        st.error(f"Rohrdaten defekt ({fp.name}): {e}")
    st.stop()


def render_smart_saw(calc: PipeCalculator, df: pd.DataFrame, current_dn: int, pn: str):
    st.markdown('<div class="machine-header-saw">🪚 SMARTE SÄGE</div>', unsafe_allow_html=True)
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
                f_type = cf1.selectbox("Typ", ["Bogen", "Flansch (Vorschweiß)", "T-Stück", "Reduzierung"], label_visibility="collapsed")

                try:
                    default_dn_idx = df['DN'].tolist().index(current_dn)
                except ValueError:
                    default_dn_idx = 0
                f_dn = cf2.selectbox("DN", df['DN'], index=default_dn_idx, label_visibility="collapsed")

                cf3, cf4 = st.columns([1, 1])
                f_cnt = cf3.number_input("Anzahl", 1, 10, 1)
                f_ang = 90.0
                if f_type == "Bogen":
                    f_ang = cf4.number_input("Winkel (°)", min_value=1.0, max_value=90.0,
                                             value=90.0, step=0.5, format="%.1f",
                                             help="Bogen-Zuschnittwinkel. 90° = Standard-BA3-Bogen.")
                else:
                    cf4.markdown("") # Spacer

                st.markdown("<br>", unsafe_allow_html=True)
                
                col_btn_add, col_btn_calc = st.columns(2)
                
                # Button A: Fügt Bauteil hinzu UND berechnet
                submitted_add = col_btn_add.form_submit_button("➕ Bauteil dazu", type="secondary", width="stretch")
                
                # Button B: Nur Berechnen
                submitted_calc = col_btn_calc.form_submit_button("🔄 Berechnen", type="primary", width="stretch")

            # --- LOGIK NACH DEM FORMULAR-SUBMIT ---
            
            # Fall A: Bauteil hinzufügen
            if submitted_add:
                deduct = calc.get_deduction(f_type, f_dn, pn, f_ang)
                uid = f"{len(st.session_state.fitting_list)}_{datetime.now().timestamp()}"
                nm = f"{f_type} DN{f_dn}" + (f" ({f_ang:g}°)" if f_type == "Bogen" else "")
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
                        # Vorschlag aus der Bauteilliste: je Bauteil eine Naht + Anschlussnaht
                        est_welds = min(20, sum(i.count for i in st.session_state.fitting_list) + 1) \
                            if st.session_state.fitting_list else 2
                        tc1, tc2 = st.columns(2)
                        num_welds = tc1.number_input("Anzahl Nähte", min_value=1, max_value=20,
                                                     value=est_welds, step=1,
                                                     help="Vorbelegt aus der Bauteilliste – bei Bedarf überschreiben.")
                        shrinkage = tc2.number_input("Schrumpfung/Naht (mm)", min_value=0.5, max_value=5.0, value=2.0, step=0.5)
                        
                        tol_result = calc.apply_tolerance_stack(res['final'], num_welds, shrinkage)
                        
                        st.divider()
                        tm1, tm2 = st.columns(2)
                        tm1.metric("Original", f"{tol_result['original']:.1f} mm")
                        tm2.metric("Korrigiert", f"{tol_result['adjusted']:.1f} mm", delta=f"+{tol_result['compensation']:.1f} mm")
                        st.caption(f"📏 Für {tol_result['num_welds']} Nähte à {tol_result['shrinkage_per_weld']}mm")
                    
                    if st.button("💾 IN LISTE SPEICHERN", type="primary", width="stretch"):
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
                st.button("🗑️ Löschen", disabled=True, width="stretch")
        else:
            data = [asdict(c) for c in st.session_state.saved_cuts]
            df_s = pd.DataFrame(data)
            if 'Auswahl' not in df_s.columns: df_s['Auswahl'] = False
            
            df_display = df_s[['Auswahl', 'name', 'raw_length', 'cut_length', 'details', 'id']]
            
            edited_df = st.data_editor(
                df_display, 
                hide_index=True, 
                width="stretch",
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

                if col_del.button(f"🗑️ Löschen ({num_sel})", disabled=btns_disabled, type="secondary", width="stretch"):
                    st.session_state.saved_cuts = [c for c in st.session_state.saved_cuts if c.id not in selected_ids]
                    st.toast(f"🗑️ {num_sel} Einträge gelöscht!", icon="🗑️")
                    time.sleep(0.5)
                    st.rerun()

                fname_base = f"Saege_PipeCraft_{datetime.now().strftime('%Y%m%d')}"
                excel_data = Exporter.to_excel(df_s)
                col_excel.download_button("📥 Excel (Alle)", excel_data, f"{fname_base}.xlsx", width="stretch")

            # --- OPTIMIZER BLOCK ---
            st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
            with st.expander("✂️ Schnitt-Optimierung (Verschnitt-Minimierung)", expanded=False):
                st.caption("Berechnet die optimale Aufteilung der gewählten Schnitte auf Stangen.")
                
                c_opt1, c_opt2 = st.columns(2)
                stock_len = c_opt1.number_input("Stangenlänge (mm)", value=6000.0, step=500.0)
                saw_width = c_opt2.number_input("Sägeblatt (mm)", value=3.0, step=0.5)
                
                if st.button("🚀 Optimierung starten", disabled=btns_disabled, width="stretch"):
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
                        st.pyplot(fig_opt, width="stretch")
                    
                    with st.expander("Detailliste"):
                        for b in bars:
                            st.markdown(f"**Stange {b.id}** (Rest: {b.waste:.1f}mm)")
                            txts = [f"{c.length:.0f}" for c in b.cuts]
                            st.caption(" | ".join(txts))

            st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
            if st.button("Alles Reset (Liste leeren)", type="secondary"):
                st.session_state.saved_cuts = []
                st.rerun()


def _spool_leer():
    return pd.DataFrame({
        "Bauteil": pd.Series(dtype="object"),
        "Mass (mm)": pd.Series(dtype="float"),
        "Massart": pd.Series(dtype="object"),
        "Seite (mm)": pd.Series(dtype="float"),
        "Winkel": pd.Series(dtype="float"),
        "Richtung": pd.Series(dtype="object"),
        "DN": pd.Series(dtype="float"),
    })


def _spool_demo():
    z = lambda t, m=None, r=None, d=None, ma=None, s=None, w=None: {
        "Bauteil": t, "Mass (mm)": m, "Massart": ma, "Seite (mm)": s,
        "Winkel": w, "Richtung": r, "DN": d}
    return pd.DataFrame([
        z("Rohr", 800),
        z("Vorschweissflansch"),
        z("Armatur mit Flanschen", 300),
        z("Armatur mit Flanschen", 250),
        z("Vorschweissflansch"),
        z("Rohr", 1200),
        z("Bogen 90", r="N"),
        z("Rohr", 2500, ma="Achsmass"),
        z("T-Stueck"),
        z("Rohr", 1800),
        z("Versprung", 800, s=600, w=45),
        z("Bogen 90", r="Hoch"),
        z("Rohr", 1500),
    ])


def _branch_leer():
    return pd.DataFrame({
        "An Bauteil": pd.Series(dtype="float"),
        "Art": pd.Series(dtype="object"),
        "Richtung": pd.Series(dtype="object"),
        "DN": pd.Series(dtype="float"),
        "Abstand (mm)": pd.Series(dtype="float"),
        "Rohrlaenge (mm)": pd.Series(dtype="float"),
        "Ende": pd.Series(dtype="object"),
    })


def _branch_demo():
    return pd.DataFrame([
        {"An Bauteil": 9, "Art": "Fertig-T", "Richtung": "Runter", "DN": 80,
         "Abstand (mm)": None, "Rohrlaenge (mm)": 1200,
         "Ende": "Vorschweissflansch"},
        {"An Bauteil": 8, "Art": "Anschweissstutzen", "Richtung": "Hoch", "DN": 50,
         "Abstand (mm)": 800, "Rohrlaenge (mm)": 600, "Ende": "offenes Ende"},
    ])


def render_spool(calc: PipeCalculator, df: pd.DataFrame, dn_global: int, pn: str):
    st.markdown('<div class="machine-header-geo">\U0001f9ed ROHRFOLGE-SKIZZE</div>',
                unsafe_allow_html=True)
    render_tool_help("spool")

    dn_list = list(df['DN'])
    try:
        dn_idx = dn_list.index(dn_global)
    except ValueError:
        dn_idx = 5

    c1, c2, c3 = st.columns(3)
    dn_start = c1.selectbox("Start-Nennweite", dn_list, index=dn_idx, key="sp_dn")
    dir_start = c2.selectbox("Start-Richtung", list(PipeCalculator.ROUTE_DIRS.keys()),
                             index=2, key="sp_dir")
    stock = c3.number_input("Rohr-Stangenlaenge (mm)", min_value=1000, value=6000,
                            step=500, key="sp_stock",
                            help="Ab dieser Laenge braucht ein Rohrstueck zusaetzliche "
                                 "Rundnaehte - die werden mitgezaehlt.")
    count_ends = st.checkbox("Anschluesse aussen mitzaehlen", value=True,
                             key="sp_ends",
                             help="Zaehlt die beiden freien Enden der Kette als "
                                  "Anschlussnaht bzw. Flanschverbindung mit.")
    with st.expander("📋 Projektdaten (Werkstoff, Koordinaten, Titelblock)",
                     expanded=False):
        w1, w2, w3 = st.columns(3)
        werkstoff = w1.text_input("Werkstoff", value="P235GH", key="sp_werk",
                                  help="Steht in der Stueckliste bei Rohr, Boegen, "
                                       "T-Stuecken und Flanschen. Verbindlich ist "
                                       "die Projektspezifikation.")
        schedule = w2.selectbox("Schedule / Wanddicke", ["STD", "Sch10", "XS",
                                                         "Sch160", "XXS"],
                                key="sp_sched",
                                help="Nach ASME B36.10M. Bestimmt die Wanddicke in "
                                     "der Stueckliste. STD = Sch40 bis 12 Zoll.")
        leitung = w3.text_input("Leitungsnummer", value="", key="sp_line",
                                help="Zum Beispiel 80-PL-1001-P235GH. Steht im "
                                     "Titelblock.")
        z1_, z2_, z3_ = st.columns(3)
        zeichnr = z1_.text_input("Zeichnungsnummer", value="", key="sp_dwg")
        projekt = z2_.text_input("Projekt / Anlage", value="", key="sp_prj")
        ersteller = z3_.text_input("Erstellt von", value="", key="sp_by")
        b1, b2, b3 = st.columns(3)
        druck = b1.text_input("Auslegungsdruck", value="", key="sp_p",
                              help="Zum Beispiel 16 bar.")
        temp = b2.text_input("Auslegungstemperatur", value="", key="sp_t",
                             help="Zum Beispiel 120 Grad C.")
        isol = b3.text_input("Isolierung", value="", key="sp_iso",
                             help="Zum Beispiel 60 mm MW oder keine.")
        k1, k2, k3 = st.columns(3)
        x_start = k1.number_input("X Startpunkt (mm)", value=0, step=100,
                                  key="sp_x",
                                  help="Ost-Koordinate im Anlagenraster. Nur fuer "
                                       "die Nahtliste - die Skizze aendert sich "
                                       "dadurch nicht.")
        y_start = k2.number_input("Y Startpunkt (mm)", value=0, step=100,
                                  key="sp_y",
                                  help="Nord-Koordinate im Anlagenraster.")
        z_start = k3.number_input("Z Startpunkt (mm)", value=0, step=100,
                                  key="sp_z",
                                  help="Hoehe des ersten Bauteils. Nur der "
                                       "Nullpunkt fuer die Z-Spalte der "
                                       "Nahtliste - ohne Anlagenraster auf 0 "
                                       "lassen.")
        st.caption("X = Ost, Y = Nord, Z = Hoehe (EL). Wer ohne Anlagenraster "
                   "arbeitet, laesst alles auf 0 - dann sind es Relativmasse "
                   "ab dem ersten Bauteil. Leere Felder bleiben im Titelblock leer.")

    st.caption(
        "Eine Zeile = **ein Bauteil**, in Einbaureihenfolge. **Mass** nur bei "
        "*Rohr* (Saegelaenge) und *Armatur* (Baulaenge) noetig - Boegen, Flansche "
        "und T-Stuecke kommen aus der DN-Tabelle. **Richtung** nur beim Bogen "
        "(die neue Laufrichtung). **DN** nur bei einer Reduzierung (neue Nennweite "
        "ab dort). Beim **Versprung** ist *Mass* die **Hoehe**, dazu *Seite* und "
        "*Winkel* (45 Grad ueblich) - die App macht daraus zwei Boegen mit "
        "schraegem Rohr und rechnet Rohrweg, Verdrehung und Saegelaenge. "
        "Bauteile duerfen direkt aneinander stossen - kein Rohr noetig. "
        "**Massart** bleibt normalerweise leer - dann gilt **Achsmass** und "
        "die App zieht Boegen, Flansche, T-Stuecke und Reduzierungen selbst ab. "
        "Nur wenn du schon die fertige Saegelaenge hast, stellst du "
        "*Rohrlaenge* ein. "
        "**Zeile loeschen:** links am Zeilenkopf anklicken und Entf druecken."
    )

    if "sp_base" not in st.session_state:
        st.session_state.sp_base = _spool_leer()
        st.session_state.sp_bbase = _branch_leer()
        st.session_state.sp_nonce = 0

    b1, b2 = st.columns(2)
    if b1.button("\U0001f5d1\ufe0f Leeren", key="sp_clear", width="stretch"):
        st.session_state.sp_base = _spool_leer()
        st.session_state.sp_bbase = _branch_leer()
        st.session_state.sp_nonce += 1
        st.rerun()
    if b2.button("\U0001f4ce Beispiel laden", key="sp_demo", width="stretch"):
        st.session_state.sp_base = _spool_demo()
        st.session_state.sp_bbase = _branch_demo()
        st.session_state.sp_nonce += 1
        st.rerun()

    nonce = st.session_state.sp_nonce
    edited = st.data_editor(
        st.session_state.sp_base, num_rows="dynamic", width="stretch",
        key=f"sp_ed_{nonce}",
        column_config={
            "Bauteil": st.column_config.SelectboxColumn(
                "Bauteil", options=PipeCalculator.SPOOL_PARTS, required=True, width="medium"),
            "Mass (mm)": st.column_config.NumberColumn(
                "Mass (mm)", min_value=0, step=10, format="%d",
                help="Rohr = das gemessene Mass (standardmaessig **Achsmass**, "
                     "siehe Spalte Massart), Armatur = Baulaenge (EN 558). "
                     "Sonst leer."),
            "Seite (mm)": st.column_config.NumberColumn(
                "Seite (mm) - Versprung", step=10, format="%d",
                help="Nur Versprung: Seitenversatz. + = nach links zur "
                     "Laufrichtung. Die Hoehe kommt in die Spalte 'Mass (mm)'."),
            "Winkel": st.column_config.NumberColumn(
                "Winkel - Versprung", min_value=5, max_value=85, step=5,
                format="%g", help="Nur Versprung: Bogenwinkel der beiden Boegen, "
                                  "ueblich 45 Grad."),
            "Massart": st.column_config.SelectboxColumn(
                "Massart (leer = Achsmass)", options=PipeCalculator.MASSARTEN,
                help="**Leer oder Achsmass** (Voreinstellung): das Mass geht "
                     "von Bezugspunkt zu Bezugspunkt der Nachbarn - Bogen = "
                     "Eckpunkt, Flansch = Dichtflaeche, Armatur = "
                     "Aussenflaeche, T-Stueck = Rohrmitte. Die Formteile "
                     "werden abgezogen, der Abzug steht in der Saegeliste. "
                     "**Rohrlaenge**: das Mass ist schon die fertige "
                     "Saegelaenge, es wird nichts abgezogen."),
            "Richtung": st.column_config.SelectboxColumn(
                "Richtung (nur Bogen)", options=list(PipeCalculator.ROUTE_DIRS.keys())),
            "DN": st.column_config.NumberColumn(
                "DN (nur Reduzierung)", min_value=10, step=5, format="%d"),
        },
    )
    parts = edited.to_dict("records")          # bewusst NICHT zurueckschreiben

    with st.expander("\u2795 Abzweige / Stutzen", expanded=False):
        st.caption("**An Bauteil** = Nummer aus der Bauteilliste unten. *Fertig-T* "
                   "sitzt auf einem **T-Stueck** der Kette, *Anschweissstutzen* auf "
                   "einem **Rohr**. **Stutzen bei** = Abstand ab Rohranfang, wo der "
                   "Stutzen aufgeschweisst wird (leer = Mitte). "
                   "**Rohrlaenge** = Saegelaenge des Abzweigrohrs.")
        bedited = st.data_editor(
            st.session_state.sp_bbase, num_rows="dynamic", width="stretch",
            key=f"sp_bed_{nonce}",
            column_config={
                "An Bauteil": st.column_config.NumberColumn(
                    "An Bauteil Nr.", min_value=1, step=1, format="%d"),
                "Art": st.column_config.SelectboxColumn(
                    "Art", options=PipeCalculator.BRANCH_ARTEN),
                "Richtung": st.column_config.SelectboxColumn(
                    "Richtung", options=list(PipeCalculator.ROUTE_DIRS.keys())),
                "DN": st.column_config.NumberColumn("DN Abzweig", min_value=10,
                                                    step=5, format="%d"),
                "Abstand (mm)": st.column_config.NumberColumn(
                    "Stutzen bei (mm)", min_value=0, step=10, format="%d",
                    help="Nur Anschweissstutzen: Abstand ab Rohranfang, wo der "
                         "Stutzen aufgeschweisst wird. Leer = Rohrmitte."),
                "Rohrlaenge (mm)": st.column_config.NumberColumn(
                    "Rohrlaenge (mm)", min_value=0, step=10, format="%d"),
                "Ende": st.column_config.SelectboxColumn(
                    "Ende", options=PipeCalculator.BRANCH_ENDS),
            },
        )
    branches = bedited.to_dict("records")

    sp = calc.build_spool(parts, int(dn_start), pn, dir_start=dir_start,
                          el_start=float(z_start), stock_len=float(stock),
                          branches=branches,
                          count_ends=bool(count_ends),
                          x_start=float(x_start), y_start=float(y_start),
                          werkstoff=werkstoff.strip() or "-", schedule=schedule)
    if "error" in sp:
        st.info(sp["error"])
        return

    for w in sp["warnings"]:
        st.warning("\u26a0\ufe0f " + w)

    z1, z2 = st.columns([2, 1])
    modus = z1.selectbox(
        "Ansicht", Visualizer.MODI, index=0, key="sp_modus",
        help="Eine Zeichnung kann nicht alles gleichzeitig zeigen, ohne "
             "unleserlich zu werden. Jede Ansicht bringt nur das, was fuer "
             "diesen Job gebraucht wird: **Aufmass & Saegen** = Bauteilnummern, "
             "Masse. **Schweissen** = Nahtzeichen und Nahtnummern. "
             "**Montage** = Positionsballons. **Alles** legt "
             "alles uebereinander - nur fuer den Ueberblick.")
    massstab = z2.toggle("massstaeblich", value=False, key="sp_scale",
                         help="Aus (empfohlen): wie eine echte Isometrie - kurze "
                              "Teile bleiben sichtbar, lange Laeufe erdruecken die "
                              "Zeichnung nicht. Die Masse stimmen trotzdem.")
    fig = Visualizer.plot_spool(
        sp,
        "DN %d - Rohr %.2f m - %d Naehte - %d Flanschverbindungen"
        % (dn_start, sp["total_axis"] / 1000.0, sp["naehte"],
           sp["flanschverbindungen"]),
        massstab=massstab, naht_nr=True, ballons=True, modus=modus)
    st.pyplot(fig, width="stretch")

    d1, d2 = st.columns(2)
    for col, fmt, mime, lbl in ((d1, "png", "image/png", "PNG"),
                                (d2, "pdf", "application/pdf", "PDF")):
        buf = BytesIO()
        fig.savefig(buf, format=fmt, dpi=200, bbox_inches="tight", facecolor="white")
        col.download_button(f"\U0001f4e5 Skizze als {lbl}", buf.getvalue(),
                            f"Rohrfolge_DN{dn_start}.{fmt}", mime=mime,
                            key=f"sp_dl_{fmt}", width="stretch")

    st.markdown("**Feldzettel A3** - Skizze, Listen, Legende und Titelblock auf "
                "einem Blatt zum Ausdrucken und Mitnehmen.")
    kopf = {"zeichnr": zeichnr, "leitung": leitung, "projekt": projekt,
            "dn": dn_start, "druck": druck, "temp": temp, "isol": isol,
            "ersteller": ersteller,
            "datum": datetime.now().strftime("%d.%m.%Y")}
    blatt = Visualizer.plot_iso_blatt(sp, kopf=kopf, massstab=massstab,
                                      modus=modus)
    a1, a2 = st.columns(2)
    for col, fmt, mime, lbl in ((a1, "pdf", "application/pdf", "PDF"),
                                (a2, "png", "image/png", "PNG")):
        buf = BytesIO()
        blatt.savefig(buf, format=fmt, dpi=200, facecolor="white")
        col.download_button(f"📄 Feldzettel A3 als {lbl}", buf.getvalue(),
                            f"Rohrfolge_A3_DN{dn_start}.{fmt}", mime=mime,
                            key=f"sp_a3_{fmt}", width="stretch")
    with st.expander("👁️ Feldzettel ansehen", expanded=False):
        st.pyplot(blatt, width="stretch")
        st.caption("Passt eine Liste nicht komplett aufs Blatt, steht das rot "
                   "darunter - vollstaendig sind die Listen im Excel-Export.")

    st.caption(
        "**Symbole:** roter Querstrich = Vorschweissflansch (1 Strich = 1 Flansch) - "
        "Fliege mit Spindel = Armatur - offener Kreis = Montagestoss - "
        "grauer Doppelstrich = Reduzierung - rotes Quadrat = Fertig-T - "
        "rote Raute = Anschweissstutzen - Knick = Bogen. "
        "**Nahtzeichen:** schwarzer Punkt = Werkstattnaht - roter Kreis mit "
        "Kreuz = Baustellennaht. "
        "**Bemassung:** auf der Zeichnung steht nur je ein **Gesamtmass "
        "pro geradem Lauf** (Eckpunkt zu Eckpunkt), in Bahnen ausserhalb der "
        "Leitung. Die Bauteile tragen nur ihre **Nummer** - die Einzellaengen "
        "und Abzuege stehen in der Saegeliste. Der **Abzweig** bekommt ein "
        "Mass direkt neben sich: von der Rohrachse bis zu seinem Ende. "
        "Beim **Versprung** spannt die schraffierte Flaeche den Versatz auf; "
        "die drei Werte stehen als Block daneben: **H** = Hoehe, **S** = Seite, "
        "**L** = Lauf. Beschriftungen weichen einander aus - es ueberschneidet "
        "sich nichts. "
        "Die Kompassrose zeigt, wo N/O/S/W liegen."
    )

    st.markdown("**Stueckliste (Richtwert)**")
    mto_df = pd.DataFrame(sp["pos_rows"])
    st.dataframe(mto_df, hide_index=True, width="stretch")
    st.caption("Die **Pos**-Nummer ist die Nummer im Ballon in der Skizze. "
               "Wanddicke nach %s - nur bei Rohr, Schweissformteilen und "
               "Vorschweissflansch, die anderen haben keine." % sp["schedule"])
    st.download_button("📥 Stueckliste (Excel)", Exporter.to_excel(mto_df),
                       f"Rohrfolge_MTO_DN{dn_start}.xlsx", key="sp_mto_xls")

    st.markdown("**Saegeliste** (nur die Rohrstuecke)")
    cut_df = pd.DataFrame(sp["cut_rows"])
    if not cut_df.empty:
        st.dataframe(cut_df, hide_index=True, width="stretch")
        st.download_button("📥 Saegeliste (Excel)", Exporter.to_excel(cut_df),
                           f"Rohrfolge_Schnitte_DN{dn_start}.xlsx", key="sp_cut_xls")
    else:
        st.caption("Noch kein Rohrstueck in der Kette.")

    st.markdown("**Nahtliste** (Richtwert)")
    naht_df = pd.DataFrame(sp["naht_rows"])
    if not naht_df.empty:
        n_feld = int((naht_df["Werkstatt/Feld"] == "Baustelle").sum())
        st.caption("%d Naehte gesamt - davon %d auf der Baustelle. "
                   "X/Y/Z sind die Koordinaten der Nahtmitte."
                   % (len(naht_df), n_feld))
        st.dataframe(naht_df, hide_index=True, width="stretch")
        st.download_button("📥 Nahtliste (Excel)", Exporter.to_excel(naht_df),
                           f"Rohrfolge_Naehte_DN{dn_start}.xlsx", key="sp_wf_xls")
    else:
        st.caption("Noch keine Naht in der Kette.")

    with st.expander("\U0001f4cb Bauteilliste (aufgeloest)", expanded=False):
        rows = [{"Nr": it["row"], "Bauteil": it["part"], "DN": it["dn"],
                 "Baulaenge (mm)": round(it["len"] * (2 if it["turn"] else 1)),
                 "Enden": "%s - %s" % it["ends"]} for it in sp["items"]]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        if sp["offene_enden"]:
            st.caption("Freie Enden: " + " - ".join(f"{w} = {a}" for w, a in sp["offene_enden"]))
        st.caption("Bogen: Baulaenge = beide Schenkel ab Eckpunkt. "
                   "Enden: S = Schweissende, F = Flanschende, X = geschlossen.")

    st.caption(
        "**Naeherung fuer Aufmass und Bestellung - keine Fertigungsisometrie.** "
        "Naehte und Flanschverbindungen kommen aus den Stoessen zwischen "
        "benachbarten Bauteilen; trifft ein Schweissende auf ein Flanschende, "
        "wird das als Fehler gemeldet. Baulaengen von Boegen, Flanschen, "
        "T-Stuecken und Reduzierungen sind Richtwerte nach EN 10253 / EN 1092-1 - "
        "Herstellerkatalog hat Vorrang. Reduzierte T-Stuecke werden mit dem Mass "
        "des Hauptrohrs gerechnet."
    )


def render_tab_handbook(calc: PipeCalculator, dn: int, pn: str):
    st.markdown('<div class="machine-header-doc">📚 SMART DATA</div>', unsafe_allow_html=True)
    render_tool_help("smartdata")
    row = calc.get_row(dn)
    suffix = "_16" if pn == "PN 16" else "_10"
    st.markdown(f"**DN {dn} / {pn}**")

    od = float(row['D_Aussen'])
    flange_b = float(row[f'Flansch_b{suffix}'])          # Typ-11-Baulänge (Weld-Neck)
    flange_c = HandbookCalculator.flange_thickness_c(dn)  # Blattdicke C (Bolzen-Klemmlänge)
    lk = float(row[f'LK_k{suffix}'])
    bolt = row[f'Schraube_M{suffix}']
    n_holes = int(row[f'Lochzahl{suffix}'])
    

    sd_tabs = st.tabs([
        "🏗️ Flansch & Schrauben", "📏 Rohrmaße / Schedule",
        "📋 Fitting-Einbaumaße",
    ])

    with sd_tabs[0]:
        wt_input = st.number_input("Wandstärke (mm) – für die Dichtungs-/Bolzenrechnung",
                                   value=6.3, min_value=1.0, step=0.1, key="sd_wt")

        c_geo1, c_geo2 = st.columns(2)
        with c_geo1:
            with st.container(border=True):
                st.markdown("##### 📐 Flansch")
                st.write(f"**Baulänge (Typ 11):** {flange_b:.0f} mm | "
                         f"**Blattdicke C:** {flange_c:.0f} mm")
                st.write(f"**Lochkreis:** {lk:.0f} mm | **Bohrung:** {n_holes} x {bolt}")
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
                is_stud = st.toggle("Stiftschraube (2 Muttern)", value=False,
                                    help="Aus = Sechskantschraube + 1 Mutter (EN-Feldpraxis). "
                                         "An = Stiftschraube/Stud mit 2 Muttern (Prozess/ASME).")
                use_washers = st.checkbox("2x U-Scheibe", value=False)
                is_lubed = st.toggle("Geschmiert (MoS2)", value=True)
                gasket_thk = st.number_input("Dichtung", value=2.0, step=0.5)

            with cb_col2:
                bolt_info = HandbookCalculator.BOLT_DATA.get(bolt, [0, 0, 0])
                sw, nm_dry, nm_lube = bolt_info

                # Klemmlänge über die Flansch-Blattdicke C (nicht die Typ-11-Baulänge!)
                # Los-/Blindflansch sind Plattenflansche und deutlich dicker als
                # der Vorschweißflansch (EN 1092-1 Typ 02 / Typ 05 ≈ 1,25–1,35·C).
                t1 = flange_c
                t2 = flange_c
                if "Los" in conn_type:
                    t2 = round(1.25 * flange_c)           # Losflansch (Typ 02) auf Bund
                elif "Blind" in conn_type:
                    t2 = round(1.35 * flange_c)           # Blindflansch (Typ 05)

                n_washers = 2 if use_washers else 0
                calc_len = HandbookCalculator.get_bolt_length(
                    t1, t2, bolt, n_washers, gasket_thk, stud=is_stud)
                torque = nm_lube if is_lubed else nm_dry
                bez = "Stiftschraube" if is_stud else "Sechskantschraube"

                m1, m2, m3 = st.columns(3)
                m1.metric(bez, f"{bolt} x {calc_len}", f"{n_holes} Stk.")
                m2.metric("Schlüsselweite", f"SW {sw} mm", "Nuss/Ring")
                m3.metric("Drehmoment", f"{torque} Nm", "Geschmiert" if is_lubed else "Trocken")
                st.caption(
                    f"Länge = C + C + 2·Dichtleiste(2 mm) + Dichtung + "
                    f"{'2·' if is_stud else ''}(Mutter ≈ 0,85·d + 2 Gewindegänge), "
                    f"aufgerundet auf 5 mm (hier C = {flange_c:.0f} mm, EN 1092-1 Typ 11). "
                    "So stehen real ~2–3½ Gänge über die Mutter. "
                    "Richtwert; Blind-/Losflansch und RTJ weichen ab."
                )

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
        st.dataframe(_df_sched, hide_index=True, width="stretch")
        st.caption("ASME B36.10M · \"STD\" = Sch 40 bis NPS 12, darüber fest 9,53 mm · "
                   "\"XS\" = Sch 80 bis NPS 8, darüber fest 12,7 mm · XXS für NPS ≥ 14 nicht definiert. "
                   "Innen-Ø = OD − 2·Wand. Im Zweifel Norm / Werksbescheinigung.")

    # ---------------------------------------------- Fitting-Einbaumaße ------
    with sd_tabs[2]:
        render_tool_help("sd_fittings")
        st.markdown(f"**Einbau-/Abzugsmaße je DN – {pn}** (mm)")
        bend_ang = st.number_input("Bogenwinkel für die Vorbau-Spalte (°)",
                                   min_value=1.0, max_value=90.0, value=90.0, step=0.5,
                                   format="%.1f", key="sd_fit_ang",
                                   help="Vorbau = R·tan(Winkel/2). 90° → Vorbau = Bogenradius. "
                                        "Übliche Bögen: 90 · 45 · 30 · 22,5 · 11,25°.")
        tan_half = math.tan(math.radians(bend_ang / 2.0))
        rows_fit = []
        for _, r in calc.df.iterrows():
            R = float(r['Radius_BA3'])
            rows_fit.append({
                "DN": int(r['DN']),
                "Ø außen": round(float(r['D_Aussen']), 1),
                "Bogen R": round(R, 0),
                f"Vorbau {bend_ang:g}°": round(R * tan_half, 0),
                "Flansch Baul.": round(float(r[f'Flansch_b{suffix}']), 0),
                "T-Stück H": round(float(r['T_Stueck_H']), 0),
                "Reduz. L": round(float(r['Red_Laenge_L']), 0),
            })
        st.dataframe(pd.DataFrame(rows_fit), hide_index=True, width="stretch", height=460)
        st.caption(
            "**Vorbau** (= Z-Maß) = Abzug pro Bogenseite bei der Sägelänge: R·tan(Winkel/2) "
            "– Winkel oben einstellbar, bei 90° = Bogenradius R. "
            "**Flansch Baul.** = Baulänge Vorschweißflansch Typ 11 (Weld-Neck), "
            "Abzug pro Flansch. **T-Stück H** = Mitte Hauptrohr → Stutzen-Ende. "
            "**Reduz. L** = Baulänge konzentrische Reduzierung (ein Sprung). "
            "Werte sind Richtwerte nach EN 10253 / EN 1092-1 – Herstellerkatalog hat Vorrang."
        )


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
                st.pyplot(Visualizer.plot_bolt_circle(res['points'], res['D']), width="stretch")
            with cgb:
                st.markdown("**Koordinaten (Nullpunkt unten links)**")
                st.dataframe(pd.DataFrame(res['points']), hide_index=True, width="stretch", height=260)


def render_downhill_school(calc: PipeCalculator, df: pd.DataFrame):
    st.markdown('<div class="machine-header-saw">🎓 FALLNAHT (STOVEPIPE) – CELLULOSE</div>',
                unsafe_allow_html=True)
    render_tool_help("fallnaht")
    st.caption("Lern- und Nachschlagemodul für das fallende Elektrodenschweißen mit "
               "zellulose-umhüllten Elektroden (E xx10, Handelsname z. B. CEL 70). "
               "Alle Werte sind Richtwerte – die freigegebene WPS hat Vorrang.")

    t_over, t_joint, t_angle, t_amp, t_pre, t_def = st.tabs(
        ["① Überblick", "② Nahtvorbereitung", "③ Elektrodenhaltung", "④ Strom & Lagen",
         "⑤ Vorwärmen", "⑥ Fehler & RT-Auswertung"]
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
                      width="stretch")
        st.divider()
        st.markdown("**Richtwerte und wofür jeder Wert da ist:**")
        rows = [{"Maß": k, "Richtwert": v[0], "Wirkung / Hinweis": v[1]}
                for k, v in wr.CEL_JOINT.items()]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
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
        st.pyplot(Visualizer.plot_electrode_angles(drag, work, lo, hi), width="stretch")

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
        st.pyplot(Visualizer.plot_travel_patterns(), width="stretch")
        st.markdown("**Je Lage:**")
        st.dataframe(pd.DataFrame(wr.CEL_TRAVEL), hide_index=True, width="stretch")
        st.markdown("**Je Uhrposition (fallend 12 → 6):**")
        for k, v in wr.CEL_CLOCK_TECHNIQUE.items():
            st.markdown(f"- **{k}** – {v}")
        with st.expander("Muster-Glossar", expanded=False):
            for k, v in wr.CEL_PATTERN_GLOSSARY.items():
                st.markdown(f"- **{k}** – {v}")

    with t_amp:
        st.markdown("**Strom-Richtwerte (Gleichstrom)** – Wurzel DC−, Heiß-/Füll-/Decklage DC+ "
                    "bei den Pipeline-Grades (FOX CEL 70/75/80/90); klassisches E 6010 durchgehend DC+")
        st.dataframe(pd.DataFrame(wr.CEL_AMPERAGE), hide_index=True, width="stretch")
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
            st.pyplot(Visualizer.plot_bead_sequence(wt2, nf), width="stretch")
        st.caption(wr.CEL_PASS_COUNT)

        st.divider()
        with st.expander("🔑 Wurzelstrom nach Spaltweite + Keyhole steuern", expanded=False):
            st.dataframe(pd.DataFrame(wr.CEL_CURRENT_GAP), hide_index=True, width="stretch")
            st.info(wr.CEL_CURRENT_GAP_NOTE)
            st.markdown("**Keyhole lesen:**")
            for k, v in wr.CEL_KEYHOLE.items():
                st.markdown(f"- **{k}** – {v}")

        with st.expander("⏱️ Zeitfenster Wurzel → Heißlage → Fülllage", expanded=False):
            st.warning(wr.CEL_HOTPASS_TIMING)

        with st.expander("🌦️ Wetter & Umgebung", expanded=False):
            st.markdown(wr.CEL_WEATHER)

    with t_pre:
        st.markdown("**Vorwärm-Richtwerte** (rundum, vor dem Heften; reale Bauteiltemperatur zählt)")
        st.dataframe(pd.DataFrame(wr.CEL_PREHEAT), hide_index=True, width="stretch")
        st.warning(wr.CEL_INTERPASS_NOTE)
        st.caption("Für unlegierten Baustahl (P235GH) reicht meist die untere Zeile. "
                   "Genauer: über Kohlenstoffäquivalent, Wandstärke und Streckenenergie "
                   "nach EN 1011-2 bzw. WPS.")

    with t_def:
        st.markdown("**A – Typische Fehler beim Fallnaht-Schweißen: Ursache und Abhilfe**")
        st.dataframe(pd.DataFrame(wr.CEL_DEFECTS), hide_index=True, width="stretch",
                     height=320)
        st.divider()
        st.markdown("**B – Offizielle Benennung nach ISO 6520-1 (für RT-/Röntgen-Protokolle)**")
        st.dataframe(pd.DataFrame(wr.RT_DEFECTS), hide_index=True, width="stretch",
                     height=420)
        st.info(wr.RT_NOTE)


def render_geometry_tools(calc: PipeCalculator, df: pd.DataFrame):
    st.markdown('<div class="machine-header-geo">📐 GEOMETRIE & BERECHNUNG</div>', unsafe_allow_html=True)
    geo_tabs = st.tabs([
        "2D Etage (S-Schlag)", "3D Raum-Etage (Rolling)", "Bogen (Standard)",
        "🦞 Segment-Bogen", "Stutzen", "📐 Spalt-Ausgleich",
        "Stutzen schräg/versetzt", "Rohr-Verschneidung", "Passstück 3D",
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
                    submit_2d = st.form_submit_button("Berechnen 🚀", type="primary", width="stretch")
                
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
                    fit_angle = st.number_input("Fitting Typ (°)", value=45.0, min_value=1.0,
                                                max_value=89.0, step=0.5, format="%.1f")
                    submit_3d = st.form_submit_button("Berechnen 🚀", type="primary", width="stretch")

                if submit_3d:
                    # reiner Rolling-Offset: ΔX = 0, der Versatz steckt in Roll (Y) + Set (Z)
                    sp = calc.calculate_spool_3d(0.0, roll, set_val, fit_angle)
                    if "error" in sp:
                        st.error(sp["error"])
                    else:
                        ded = calc.calculate_bend_details(dn_roll, fit_angle)["vorbau"]
                        st.session_state.calc_res_3d = {
                            "roll_val": roll, "set_val": set_val,
                            "travel_center": sp["travel"],
                            "run_length": sp["run"],
                            "cut_length": sp["travel"] - 2 * ded,
                            "deduction": ded,
                            "angle": fit_angle,
                            "roll_angle": sp["roll_angle"],
                        }

        with c2:
            if 'calc_res_3d' in st.session_state:
                res = st.session_state.calc_res_3d

                col_res1, col_res2 = st.columns(2)
                col_res1.metric("Zuschnitt (Rohr)", f"{res['cut_length']:.1f} mm")
                col_res1.caption(f"Abzug 2x {res['deduction']:.1f} mm")

                col_res2.metric("Rohrweg (Mitte)", f"{res['travel_center']:.1f} mm")
                col_res2.caption(f"Hypotenuse bei {res['angle']:.1f}°")

                st.info(f"Benötigte Baulänge (Run): {res['run_length']:.1f} mm · "
                        f"Verdrehung (Roll) {res['roll_angle']:.1f}°")
                if res['cut_length'] < 0:
                    st.warning("⚠️ Negatives Zuschnittmaß – die zwei Bögen brauchen mehr "
                               "Weg, als der Versatz hergibt. Steileren Bogenwinkel wählen.")

                if st.button("➡️ An Säge (3D)", key="btn_3d_saw"):
                    st.session_state.active_tab = "🪚 Smarte Säge"
                    st.session_state.transfer_cut_length = res['cut_length']
                    st.rerun()

                if PLOTLY_AVAILABLE:
                    st.markdown("### 🧊 3D Vorschau")
                    fig = Visualizer.plot_rolling_offset_interactive(
                        res['roll_val'], res['set_val'], res['run_length'], dn_roll)
                    if fig:
                        st.plotly_chart(fig, width="stretch")


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
                r_seg, res_seg['od'], res_seg['num_segments'], tot_ang), width="stretch")

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
                    width="stretch")
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
            st.pyplot(fig, width="stretch")

            c_tab, c_howto = st.columns([1, 1])
            with c_tab:
                st.markdown("**Anreißtabelle Stutzen**")
                tbl = pd.DataFrame(res['stations'])
                st.dataframe(tbl, hide_index=True, width="stretch", height=280)
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
                
                if st.button("Berechnen 📐", type="primary", width="stretch", key="btn_calc_wedge"):
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
                        width="stretch",
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
                width="stretch")
            st.dataframe(pd.DataFrame(res['stations']), hide_index=True, width="stretch", height=260)
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
                f"Gehrungs-Schablone · {rv['miter_angle']:.1f}°"), width="stretch")
            st.dataframe(pd.DataFrame(rv['stations']), hide_index=True, width="stretch", height=260)
    # ---------------------------------------------- Passstück 3D ----------
    with geo_tabs[8]:
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
                              width="stretch")


ALL_TABS = ["🪚 Smarte Säge", "🧭 Rohrfolge-Skizze", "📐 Geometrie", "🧮 Rechner",
            "🎓 Fallnaht", "📚 Smart Data"]


def main():
    init_app_state()

    st.sidebar.title("🏗️ PipeCraft")
    st.sidebar.caption("Feld-Rechner Rohrleitungsbau")

    df_pipe = load_pipe_table()
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
        # Scratch-Ergebnisse des vorherigen Bereichs verwerfen (Listen bleiben)
        for k in ("calc_res_2d", "calc_res_3d", "gap_res", "last_calc_result", "opt_results"):
            st.session_state.pop(k, None)
        st.rerun()
    st.divider()

    if st.session_state.active_tab == "🪚 Smarte Säge":
        render_smart_saw(calc, df_pipe, dn, pn)
    elif st.session_state.active_tab == "🧭 Rohrfolge-Skizze":
        render_spool(calc, df_pipe, dn, pn)
    elif st.session_state.active_tab == "📐 Geometrie":
        render_geometry_tools(calc, df_pipe)
    elif st.session_state.active_tab == "🧮 Rechner":
        render_field_calc(calc, df_pipe)
    elif st.session_state.active_tab == "🎓 Fallnaht":
        render_downhill_school(calc, df_pipe)
    elif st.session_state.active_tab == "📚 Smart Data":
        render_tab_handbook(calc, dn, pn)

if __name__ == "__main__":
    main()
