import streamlit as st
import pandas as pd
import numpy as np
import io
import re

# --- SYSTEM WIDE CONFIGURATION ---
st.set_page_config(
    page_title="Delaware Cornhole League OS Master", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CENTRAL NAVIGATION ---
st.sidebar.title("🎮 Operating System Menu")
app_mode = st.sidebar.selectbox(
    "Choose Active Workspace Menu Module:",
    ["📊 Preset Timeframe Stats Generator", "⚙️ League OS Core Operations"]
)
st.sidebar.write("---")

def clean_player_name(name_val):
    """Sanitizes decorative badges, emojis, and extra white space from player names."""
    if pd.isna(name_val):
        return ""
    text = str(name_val).strip()
    text = re.sub(r'[^\w\s\.\-]', '', text)
    return " ".join(text.split())

def parse_week_num(week_str):
    """Extracts numeric values from week codes to allow proper chronological sorting."""
    nums = re.findall(r'\d+', str(week_str))
    return int(nums[0]) if nums else 9999

# ==============================================================================
# MODULE 1: PRESET TIMEFRAME STATS GENERATOR (WEEKLY PRODUCTION SUITE)
# ==============================================================================
if app_mode == "📊 Preset Timeframe Stats Generator":
    st.title("🎛️ Delaware Cornhole Weekly Production Suite")
    st.subheader("Module 1: Dynamic Tiered Scoring Engine")
    
    st.sidebar.header("📅 Timeframe Target Scope")
    selected_week_code = st.sidebar.text_input("League Week Code Designation:", value="W.23")
    target_year = st.sidebar.selectbox("Select Target Year", [2026, 2025, 2024], index=0)

    st.sidebar.write("---")
    st.sidebar.header("🏆 Season Format Phase Modifiers")
    season_stage = st.sidebar.selectbox(
        "Tournament Rule Mode:",
        ["Standard Tournament Night", "Regular League Play (Stats Only)", "League Championship / Playoffs"]
    )

    st.header("📥 Weekly Session Data Ingestion")
    st.info(f"💡 **Drop All Files for {selected_week_code}:** Upload your ScoreMagic statistics files and bracket standing files together.")
    
    uploaded_files = st.file_uploader(
        "Drag and drop weekly session files here (Supports up to 50 CSV files)", 
        type=["csv"], 
        accept_multiple_files=True
    )

    scoremagic_dfs = []
    bracket_dfs = []

    if uploaded_files:
        for file in uploaded_files:
            try:
                df = pd.read_csv(file)
                df.columns = df.columns.str.strip()
                
                if "PPR" in df.columns and "DPR" in df.columns:
                    df['Origin_File'] = file.name
                    scoremagic_dfs.append(df)
                elif "Place" in df.columns and "Team Name" in df.columns:
                    bracket_dfs.append(df)
            except Exception as e:
                st.error(f"Error reading `{file.name}`: {e}")

        col_sm, col_bk = st.columns(2)
        with col_sm: st.metric("ScoreMagic Stats Files Loaded", len(scoremagic_dfs))
        with col_bk: st.metric("Bracket Standings Files Loaded", len(bracket_dfs))

    st.write("---")

    if st.button("🚀 Process Streams & Compile 4-Output Matrix"):
        if not scoremagic_dfs:
            st.error("❌ Please upload your ScoreMagic statistics files to run computations.")
        else:
            # 1. Map Bracket Placements from Standings Files
            bracket_placement = {}
            if bracket_dfs:
                combined_brackets = pd.concat(bracket_dfs, ignore_index=True)
                for _, row in combined_brackets.iterrows():
                    place_val = str(row.get('Place', '0')).strip()
                    game_name = str(row.get('Game Name', 'Tournament')).strip()
                    for p_idx in ['PlayerName1', 'PlayerName2', 'PlayerName3', 'PlayerName4']:
                        p_name = str(row.get(p_idx, '')).strip()
                        if p_name and p_name != 'nan':
                            bracket_placement[p_name] = {'Place': place_val, 'Division': game_name}

            # 2. Process Rows Based on Dynamic Bracket Averages
            compiled_rows = []
            
            for df_file in scoremagic_dfs:
                df_file['PPR_Numeric'] = pd.to_numeric(df_file['PPR'], errors='coerce').fillna(0.0)
                bracket_avg_ppr = df_file['PPR_Numeric'].mean()
                
                # Assign Exact Hand-Written Sheet Tiers
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
                
                for _, row in df_file.iterrows():
                    disp_name = str(row.get('Display Name', '')).strip()
                    if not disp_name:
                        continue
                    
                    bracket_data = bracket_placement.get(disp_name, {'Place': '0', 'Division': str(row.get('Game Name', 'Tournament'))})
                    
                    first_name = str(row.get('First Name', '')).strip()
                    last_name = str(row.get('Last Name', '')).strip()
                    email_addr = str(row.get('Email', '')).strip()
                    
                    ppr = row['PPR_Numeric']
                    opp_ppr = pd.to_numeric(row.get('OPP PPR', 0), errors='coerce') or 0.0
                    dpr = pd.to_numeric(row.get('DPR', 0), errors='coerce') or 0.0
                    rounds = pd.to_numeric(row.get('Rounds', 0), errors='coerce') or 0
                    
                    def clean_pct(val):
                        if pd.isna(val): return 0.0
                        return float(str(val).replace('%', '').strip()) or 0.0
                    
                    off_board = clean_pct(row.get('OFF %', 0))
                    four_bagger = clean_pct(row.get('4IN %', 0))

                    # --- CORE STATS BONUSES ---
                    ppr_bonus = 5 if ppr >= 8.0 else (3 if ppr >= 7.0 else 0)
                    off_bonus = 5 if off_board <= 10 else (3 if off_board <= 15 else 0)
                    round_bonus = 2 if rounds >= 30 else 0
                    
                    # --- LOCKED PLACEMENT BONUS MATRIX ENGINE ---
                    podium_place = int(bracket_data['Place']) if str(bracket_data['Place']).isdigit() else 0
                    podium_points = 0
                    
                    if podium_place == 1:
                        if calculated_tier == "Tier 1 (>= 8.5)": podium_points = 20
                        elif calculated_tier == "Tier 2 (8.0 - 8.49)": podium_points = 10
                        elif calculated_tier == "Tier 3 (7.50 - 7.99)": podium_points = 8
                        elif calculated_tier == "Tier 4 (7.0 - 7.49)": podium_points = 6
                        elif calculated_tier == "Tier 5 (< 7.0)": podium_points = 4
                    elif podium_place == 2:
                        if calculated_tier == "Tier 1 (>= 8.5)": podium_points = 15
                        elif calculated_tier == "Tier 2 (8.0 - 8.49)": podium_points = 8
                        elif calculated_tier == "Tier 3 (7.50 - 7.99)": podium_points = 6
                        elif calculated_tier == "Tier 4 (7.0 - 7.49)": podium_points = 4
                        elif calculated_tier == "Tier 5 (< 7.0)": podium_points = 2
                    elif podium_place == 3:
                        if calculated_tier == "Tier 1 (>= 8.5)": podium_points = 12
                        elif calculated_tier == "Tier 2 (8.0 - 8.49)": podium_points = 6
                        elif calculated_tier == "Tier 3 (7.50 - 7.99)": podium_points = 4
                        elif calculated_tier == "Tier 4 (7.0 - 7.49)": podium_points = 2
                    elif podium_place == 4:
                        if calculated_tier == "Tier 1 (>= 8.5)": podium_points = 10
                        elif calculated_tier == "Tier 2 (8.0 - 8.49)": podium_points = 4
                        elif calculated_tier == "Tier 3 (7.50 - 7.99)": podium_points = 2
                    elif podium_place in [5, 6]:
                        if calculated_tier == "Tier 1 (>= 8.5)": podium_points =