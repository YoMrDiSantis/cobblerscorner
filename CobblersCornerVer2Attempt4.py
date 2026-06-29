import streamlit as st
import pandas as pd
import numpy as np
import io
import re
import csv
import sys

# Maximize CSV parser cell headroom limits to bypass overflow crashing artifacts
csv.field_size_limit(sys.maxsize)

# --- MASTER LAYOUT INITIALIZATION ---
st.set_page_config(
    page_title="Delaware Cornhole League OS Master", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CENTRAL NAVIGATION ---
st.sidebar.title("🎮 Operating System Menu")
app_mode = st.sidebar.selectbox(
    "Choose Active Workspace Module:",
    ["📊 Weekly Data Stream Processing Suite", "⚙️ League OS Core Master Registry View"]
)
st.sidebar.write("---")

def parse_week_num(week_str):
    nums = re.findall(r'\d+', str(week_str))
    return int(nums[0]) if nums else 9999

def get_dynamic_date_meta(week_code, target_year):
    wk_num = parse_week_num(week_code)
    if wk_num <= 8:
        month_str = "January"
        seq_num = "101"
    elif wk_num <= 16:
        month_str = "April"
        seq_num = "104"
    elif wk_num <= 24:
        month_str = "June"
        seq_num = "106"
    else:
        month_str = "September"
        seq_num = "109"
    return month_str, f"{target_year} {seq_num} {month_str}"

def compute_dynamic_event_type(game_name):
    name_upper = str(game_name).upper()
    if "CAP" in name_upper:
        return "Tourney"
    elif "SINGLES" in name_upper:
        return "Singles"
    elif "SQUADHOLIO" in name_upper:
        return "Squadholio"
    elif "KNOCKOUT" in name_upper:
        return "Knockout"
    return "Switch / BD"

def compute_dynamic_location(game_name):
    name_lower = str(game_name).lower()
    if "elks" in name_lower: return "Cape Elks"
    if "birdies" in name_lower: return "Birdies"
    if "vets" in name_lower: return "Del Vets"
    if "chesapeake" in name_lower: return "Chesapeake Inn"
    return "Birdies"

def clean_percent_to_int(pct_val):
    if pd.isna(pct_val): return 0
    try:
        return int(float(str(pct_val).replace('%', '').strip()))
    except Exception:
        return 0

# ==============================================================================
# MODULE 1: WEEKLY DATA STREAM PROCESSING SUITE
# ==============================================================================
if app_mode == "📊 Weekly Data Stream Processing Suite":
    st.title("🎛️ Delaware Cornhole Weekly Production Suite")
    st.subheader("Automated Cross-Validation & Processing Engine")
    
    st.sidebar.header("📅 Timeframe Target Context")
    selected_week_code = st.sidebar.text_input("League Week Code Designation:", value="W.23")
    target_year = st.sidebar.selectbox("Select Target Year", [2026, 2025, 2024], index=0)

    st.header("📥 Multi-Stream Data Ingestion")
    st.info("💡 **Step 1:** Drop your files here together. **Step 2:** Click the Stage button to process maps into session storage. **Step 3:** Use the independent expander panels at the bottom to download your sheets!")
    
    uploaded_files = st.file_uploader(
        "Drop complete weekly files here (.csv format supported)", 
        type=["csv"], 
        accept_multiple_files=True,
        key="uploader_stream"
    )

    # Core logic configuration button to lock outputs to memory
    if uploaded_files:
        if st.button("⚙️ Stage Uploaded Streams for Processing", key="stage_files_trigger"):
            stats_list = []
            brackets_by_game = {}
            rosters_by_game = {}
            
            for f in uploaded_files:
                try:
                    content = f.read().decode("utf-8", errors="ignore")
                    df = pd.read_csv(io.StringIO(content))
                    df.columns = df.columns.str.strip()
                    
                    if "Game Name" in df.columns:
                        df["Game Name"] = df["Game Name"].astype(str).str.strip()
                    
                    if "PPR" in df.columns and "Email" in df.columns:
                        stats_list.append(df)
                    elif "Place" in df.columns and "Team Name" in df.columns:
                        if "Game Name" in df.columns and len(df) > 0:
                            g_name = str(df["Game Name"].iloc[0]).strip().lower()
                            brackets_by_game[g_name] = df
                    elif "Club Name" in df.columns or "Player Email" in df.columns:
                        if "Game Name" in df.columns and len(df) > 0:
                            g_name = str(df["Game Name"].iloc[0]).strip().lower()
                            rosters_by_game[g_name] = df
                except Exception as ex:
                    st.error(f"Bypassed file format error on {f.name}: {ex}")

            # --- PROCESS MASTER INTER-CONNECTIVITY DATA ARRAYS ---
            compiled_pbi_records = []
            compiled_potw_records = []
            compiled_canva_brackets = []
            compiled_canva_pprs = []

            dynamic_month, dynamic_rolling = get_dynamic_date_meta(selected_week_code, target_year)

            for stats_df in stats_list:
                if len(stats_df) == 0:
                    continue

                game_title = str(stats_df['Game Name'].iloc[0]).strip() if 'Game Name' in stats_df.columns else "Open Tournament"
                game_key = game_title.lower()

                bracket_df = brackets_by_game.get(game_key)
                roster_df = rosters_by_game.get(game_key)

                stats_df['PPR_Numeric'] = pd.to_numeric(stats_df['PPR'], errors='coerce').fillna(0.0)
                bracket_avg_ppr = stats_df['PPR_Numeric'].mean() if len(stats_df) > 0 else 0.0
                calculated_tier = "Tier 1" if bracket_avg_ppr >= 8.5 else ("Tier 2" if bracket_avg_ppr >= 8.0 else ("Tier 3" if bracket_avg_ppr >= 7.5 else ("Tier 4" if bracket_avg_ppr >= 7.0 else "Tier 5")))

                # Safe placement indexing mapping
                placement_map = {}
                if bracket_df is not None:
                    for _, row in bracket_df.iterrows():
                        place = str(row.get('Place', '0')).strip()
                        for p_idx in ['PlayerEmail1', 'PlayerEmail2', 'PlayerEmail3', 'PlayerEmail4']:
                            if p_idx in bracket_df.columns:
                                email = str(row.get(p_idx, '')).strip().lower()
                                if email and email != 'nan' and email != '':
                                    placement_map[email] = place

                # Safe roster mapping
                club_map = {}
                if roster_df is not None:
                    email_col = 'Player Email' if 'Player Email' in roster_df.columns else ('Email' if 'Email' in roster_df.columns else '')
                    club_col = 'Club Name' if 'Club Name' in roster_df.columns else ''
                    if email_col and club_col:
                        for _, row in roster_df.iterrows():
                            email = str(row.get(email_col, '')).strip().lower()
                            club = str(row.get(club_col, '')).strip()
                            if email and email != 'nan' and email != '':
                                club_map[email] = club

                resolved_event = compute_dynamic_event_type(game_title)
                resolved_location = compute_dynamic_location