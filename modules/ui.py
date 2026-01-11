import streamlit as st
import time
from datetime import datetime
from modules.database import DatabaseRepository

def init_app_state():
    defaults = {
        'active_project_id': None,
        'active_project_name': "Kein Projekt",
        'project_archived': 0,
        'fitting_list': [],
        'saved_cuts': [],
        'editing_id': None,
        'bulk_edit_ids': [], 
        'last_iso': '',
        'last_naht': '',
        'last_apz': '',
        'last_schweisser': '',
        'last_datum': datetime.now(),
        'form_dn_red_idx': 0,
        'logbook_view_index': 0,
        'active_tab': "🪚 Smarte Säge",
        # NEU: Selection State
        'logbook_select_all': False,
        'logbook_key_counter': 0
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def render_smart_input(label: str, db_column: str, current_value: str, key_prefix: str, active_pid: int) -> str:
    known_values = DatabaseRepository.get_known_values(db_column, active_pid)
    
    if known_values:
        options = ["✨ Neu / Manuell"] + known_values
        try: 
            sel_idx = options.index(current_value)
        except ValueError:
            sel_idx = 0 
            
        selection = st.selectbox(label, options, index=sel_idx, key=f"{key_prefix}_sel")
        
        if selection == "✨ Neu / Manuell":
            final_val = st.text_input(f"{label} (Eingabe)", value=current_value, key=f"{key_prefix}_txt")
        else:
            final_val = selection
    else:
        final_val = st.text_input(label, value=current_value, key=f"{key_prefix}_txt_only")
        
    return final_val

from dataclasses import asdict
from modules.models import FittingItem, SavedCut

def serialize_state():
    return {
        'fitting_list': [asdict(x) for x in st.session_state.fitting_list],
        'saved_cuts': [asdict(x) for x in st.session_state.saved_cuts]
    }

def deserialize_state(data: dict):
    # Restore Fitting List
    raw_fits = data.get('fitting_list', [])
    restored_fits = [FittingItem(**item) for item in raw_fits]
    
    # Restore Saved Cuts
    raw_cuts = data.get('saved_cuts', [])
    restored_cuts = []
    for cut in raw_cuts:
        # Reconstruct nested FittingItems
        if 'fittings' in cut:
            cut['fittings'] = [FittingItem(**f) for f in cut['fittings']]
        restored_cuts.append(SavedCut(**cut))
        
    return restored_fits, restored_cuts

def render_sidebar_projects():
    st.sidebar.title("🏗️ PipeCraft")
    st.sidebar.caption("v3.5 (Final)")
    
    projects = DatabaseRepository.get_projects() 
    
    # Initial Load if not set
    if st.session_state.active_project_id is None and projects:
        pid, pname, parch = projects[0]
        st.session_state.active_project_id = pid
        st.session_state.active_project_name = pname
        st.session_state.project_archived = parch
        
        # Load Workspace on Startup
        ws_data = DatabaseRepository.load_workspace(pid)
        if ws_data:
            fl, sc = deserialize_state(ws_data)
            st.session_state.fitting_list = fl
            st.session_state.saved_cuts = sc

    current_proj_data = next((p for p in projects if p[0] == st.session_state.active_project_id), None)
    if current_proj_data:
        st.session_state.project_archived = current_proj_data[2]
    
    projects = DatabaseRepository.get_projects()
    # projects: [(id, name, archived, order_number), ...]
    
    # Format: "Name | #OrderNum"
    proj_options = []
    for p in projects:
        p_id, p_name, p_arch = p[0], p[1], p[2]
        p_ord = p[3] if len(p) > 3 and p[3] else ""
        
        label = f"{p_name}"
        if p_ord: label += f" | #{p_ord}"
        if p_arch: label += " 🔒"
        proj_options.append(label)

    # Determine current index
    current_idx = 0
    if st.session_state.active_project_id:
        for i, p in enumerate(projects):
            if p[0] == st.session_state.active_project_id:
                current_idx = i
                break
    
    sel_label = st.sidebar.selectbox("📂 Projekt wählen", proj_options, index=current_idx, key="proj_selector")
    sel_index = proj_options.index(sel_label)
    
    # Extract data from selected index
    new_id = projects[sel_index][0]
    new_name = projects[sel_index][1]
    is_archived = projects[sel_index][2]
    new_ord = projects[sel_index][3] if len(projects[sel_index]) > 3 else ""
    
    # Update State
    st.session_state.active_project_order = new_ord
    
    if new_id != st.session_state.active_project_id:
        # SAVE OLD WORKSPACE
        old_id = st.session_state.active_project_id
        if old_id:
            data = serialize_state()
            DatabaseRepository.save_workspace(old_id, data)
        
        # SWITCH PROJECT
        st.session_state.active_project_id = new_id
        st.session_state.active_project_name = new_name
        st.session_state.project_archived = is_archived
        st.session_state.active_project_order = new_ord
        
        # LOAD NEW WORKSPACE
        ws_data = DatabaseRepository.load_workspace(new_id)
        if ws_data:
            fl, sc = deserialize_state(ws_data)
            st.session_state.fitting_list = fl
            st.session_state.saved_cuts = sc
        else:
            st.session_state.saved_cuts = [] 
            st.session_state.fitting_list = []
            
        st.rerun()

    if st.session_state.project_archived == 1:
        st.sidebar.warning("🔒 Projekt ist archiviert (Read-Only)")

    with st.sidebar.expander("➕ Neues Projekt"):
        new_proj = st.text_input("Projekt-Name", placeholder="z.B. Halle 4")
        new_ord_num = st.text_input("Auftragsnummer (Optional)", placeholder="z.B. AN-12345678")
        if st.button("Erstellen"):
            if new_proj:
                ok, msg = DatabaseRepository.create_project(new_proj, new_ord_num)
                if ok: 
                    st.success(msg)
                    st.rerun()
                else: 
                    st.error(msg)
    st.sidebar.divider()
    
    with st.sidebar.expander("💾 Datensicherung"):
        if st.session_state.active_project_id:
            json_data = DatabaseRepository.export_project_to_json(st.session_state.active_project_id)
            if json_data:
                fname = f"Backup_{st.session_state.active_project_name.replace(' ', '_')}.json"
                st.download_button("📤 Projekt Exportieren", json_data, fname, "application/json")
        
        uploaded_file = st.file_uploader("📥 Projekt Importieren", type=["json"])
        if uploaded_file is not None:
            if st.button("Import Starten"):
                string_data = uploaded_file.getvalue().decode("utf-8")
                ok, msg = DatabaseRepository.import_project_from_json(string_data)
                if ok:
                    st.success(msg)
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(msg)
