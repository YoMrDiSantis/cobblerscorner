import streamlit as st
import pandas as pd
import numpy as np
import io
import re

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
    """Extracts numeric integer values from week codes to allow proper chronological sorting."""
    nums = re.findall(r'\d+', str(week_str))
    return int(nums[0]) if nums else 9999

def get_dynamic_date_meta(week_code, target_year):
    """
    Dynamically maps a week number to its corresponding calendar month label and 
    Power BI custom string format to automate chronological sorting metrics.
    """
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
        
    rolling_year_str = f"{target_year} {seq_num} {month_str}"
    return month_str, rolling_year_str

def parse_filename_token(filename):
    """Extracts the common unique identifier token out of uploaded file names to group triplets."""
    match = re.search(r'-(.+?)\.csv', str(filename))
    return match.group(1) if match else str(filename)

def compute_dynamic_event_type(game_name):
    """
    Scans game names and applies priority-based rules to map specific 
    historical event taxonomy labels required by Power BI.
    """
    name_upper = str(game_name).upper()
    
    if "CAP" in name_upper:
        return "Tourney"
    elif "SINGLES" in name_upper:
        return "Singles"
    elif "SQUADHOLIO" in name_upper:
        return "Squadholio"
    elif "KNOCKOUT" in name_upper:
        return "Knockout"
    elif any(kw in name_upper for kw in ["SWITCH", "BLIND DRAW"]):
        return "Switch / BD"
    else:
        return "Switch / BD"

def compute_dynamic_location(game_name):
    """Maps custom game headers directly to certified physical venues in Delaware."""
    name_lower = str(game_name).lower()
    if "elks" in name_lower:
        return "Cape Elks"
    elif "birdies" in name_lower:
        return "Birdies"
    elif "vets" in name_lower:
        return "Del Vets"
    elif "chesapeake" in name_lower:
        return "Chesapeake Inn"
    else:
        return "Birdies"

def clean_percent_to_int(pct_val):
    """Converts text-formatted percentages directly to clean, model-safe integers."""
    if pd.isna(pct_val):
        return 0
    clean_str = str(pct_val).replace('%', '').strip()
    try:
        return int(float(clean_str))
    except ValueError:
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
    st.info("💡 **Drop All Files Together:** Upload ScoreMagic stats, Bracket Standings, and Player Rosters simultaneously. The internal token-mapping matrix groups them automatically.")
    
    uploaded_files = st.file_uploader(
        "Drop complete weekly files here (.csv format supported)", 
        type=["csv"], 
        accept_multiple_files=True
    )

    if uploaded_files:
        # Group incoming data streams by their cryptographic unique identifiers
        file_registry = {}
        
        for f in uploaded_files:
            token = parse_filename_token(f.name)
            if token not in file_registry:
                file_registry[token] = {"stats": None, "bracket": None, "roster": None}
            
            content = f.read().decode("utf-8")
            df = pd.read_csv(io.StringIO(content))
            df.columns = df.columns.str.strip()
            
            if "PPR" in df.columns and "DPR" in df.columns:
                file_registry[token]["stats"] = df
            elif "Place" in df.columns and "Team Name" in df.columns:
                file_registry[token]["bracket"] = df
            elif "Action" in df.columns and "Club Name" in df.columns:
                file_registry[token]["roster"] = df

        st.success(f"Successfully tracked and partitioned `{len(file_registry)}` active tournament groups from file streams.")

        if st.button("🚀 Execute Processing Engine & Compile Outputs"):
            all_processed_records = []
            potw_records = []
            canva_brackets_summary = []
            canva_top_pprs = []

            dynamic_month, dynamic_rolling = get_dynamic_date_meta(selected_week_code, target_year)

            # Process each individual tournament file group independently
            for token, group in file_registry.items():
                stats_df = group["stats"]
                bracket_df = group["bracket"]
                roster_df = group["roster"]

                if stats_df is None:
                    continue  # Missing structural baseline stats file for this token group

                # 1. Establish Master Local Bracket Skill Level Averages
                stats_df['PPR_Numeric'] = pd.to_numeric(stats_df['PPR'], errors='coerce').fillna(0.0)
                bracket_avg_ppr = stats_df['PPR_Numeric'].mean()

                if bracket_avg_ppr >= 8.5:
                    calculated_tier = "Tier 1 (>= 8.5)"
                elif bracket_avg_ppr >= 8.0:
                    calculated_tier = "Tier 2 (8.0 - 8.49)"
                elif bracket_avg_ppr >= 7.5:
                    calculated_tier = "Tier 3 (7.50 - 7.99)"
                elif bracket_avg_ppr >= 7.0:
                    calculated_tier = "Tier 4 (7.0 - 7.49)"
                else:
                    calculated_tier = "Tier 5 (< 7.0)"

                # 2. Extract Cross-Tab Placement Metrics
                placement_map = {}
                if bracket_df is not None:
                    for _, row in bracket_df.iterrows():
                        place = str(row.get('Place', '0')).strip()
                        for p_idx in ['PlayerEmail1', 'PlayerEmail2', 'PlayerEmail3', 'PlayerEmail4']:
                            email = str(row.get(p_idx, '')).strip().lower()
                            if email and email != 'nan':
                                placement_map[email] = place

                # 3. Extract Club Affiliation Lookup Tables
                club_map = {}
                if roster_df is not None:
                    for _, row in roster_df.iterrows():
                        email = str(row.get('Player Email', '')).strip().lower()
                        club = str(row.get('Club Name', '')).strip()
                        if email and email != 'nan':
                            club_map[email] = club

                # 4. Map, Scale, and Format Flat Schema Values
                game_title = stats_df['Game Name'].iloc[0] if 'Game Name' in stats_df.columns else "Tournament Night"
                resolved_event = compute_dynamic_event_type(game_title)
                resolved_location = compute_dynamic_location(game_title)

                # Uniform Level Rule: Track lower brackets under Open to keep historical datasets intact
                resolved_level = "Open"

                for _, row in stats_df.iterrows():
                    p_email = str(row.get('Email', '')).strip().lower()
                    d_name = str(row.get('Display Name', '')).strip()
                    f_name = str(row.get('First Name', '')).strip()
                    l_name = str(row.get('Last Name', '')).strip()
                    
                    if not d_name or p_email == 'nan':
                        continue

                    # Lookup dynamic cross-file flags
                    assigned_place = placement_map.get(p_email, "0")
                    assigned_club = club_map.get(p_email, "")
                    
                    podium_int = int(assigned_place) if assigned_place.isdigit() else 0
                    is_podium_finish = 1 if podium_int in [1, 2, 3] else 0

                    ppr_val = float(row['PPR_Numeric'])
                    dpr_val = pd.to_numeric(row.get('DPR', 0), errors='coerce') or 0.0
                    opp_ppr_val = pd.to_numeric(row.get('OPP PPR', 0), errors='coerce') or 0.0

                    # Standardize raw count values straight from source rows without scaling multipliers
                    val_4in = clean_percent_to_int(row.get('4IN', 0))
                    pct_4in = clean_percent_to_int(row.get('4IN %', 0))
                    val_in = clean_percent_to_int(row.get('IN', 0))
                    pct_in = clean_percent_to_int(row.get('IN %', 0))
                    val_on = clean_percent_to_int(row.get('ON', 0))
                    pct_on = clean_percent_to_int(row.get('ON %', 0))
                    val_off = clean_percent_to_int(row.get('OFF', 0))
                    pct_off = clean_percent_to_int(row.get('OFF %', 0))

                    tot_rounds = int(pd.to_numeric(row.get('Rounds', 0), errors='coerce') or 0)
                    pts_total = pd.to_numeric(row.get('Total Points', 0), errors='coerce') or 0
                    pts_opp = pd.to_numeric(row.get('Opp Points', 0), errors='coerce') or 0

                    # --- PODIUM MATRIX SCORE ENGINE ---
                    bonus_points = 0
                    if podium_int == 1:
                        if "Tier 1" in calculated_tier: bonus_points = 20
                        elif "Tier 2" in calculated_tier: bonus_points = 10
                        elif "Tier 3" in calculated_tier: bonus_points = 8
                        elif "Tier 4" in calculated_tier: bonus_points = 6
                        elif "Tier 5" in calculated_tier: bonus_points = 4
                    elif podium_int == 2:
                        if "Tier 1" in calculated_tier: bonus_points = 15
                        elif "Tier 2" in calculated_tier: bonus_points = 8
                        elif "Tier 3" in calculated_tier: bonus_points = 6
                        elif "Tier 4" in calculated_tier: bonus_points = 4
                        elif "Tier 5" in calculated_tier: bonus_points = 2
                    elif podium_int == 3:
                        if "Tier 1" in calculated_tier: bonus_points = 12
                        elif "Tier 2" in calculated_tier: bonus_points = 6
                        elif "Tier 3" in calculated_tier: bonus_points = 4
                        elif "Tier 4" in calculated_tier: bonus_points = 2
                    elif podium_int == 4:
                        if "Tier 1" in calculated_tier: bonus_points = 10
                        elif "Tier 2" in calculated_tier: bonus_points = 4
                        elif "Tier 3" in calculated_tier: bonus_points = 2