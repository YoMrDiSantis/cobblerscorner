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

def get_dynamic_date_meta(week_code, target_year):
    """
    Dynamically maps a week number to its corresponding calendar month label and 
    Power BI custom string format to automate timeline tracking without manual entries.
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
        "Drag and drop weekly session files here (Supports CSV/Excel formats)", 
        type=["csv", "xlsx"], 
        accept_multiple_files=True
    )

    scoremagic_dfs = []
    bracket_dfs = []

    if uploaded_files:
        for file in uploaded_files:
            try:
                if file.name.endswith('.xlsx'):
                    df = pd.read_excel(file)
                else:
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

    if st.button("🚀 Process Streams & Compile Power BI Matrix"):
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
            dynamic_month, dynamic_rolling = get_dynamic_date_meta(selected_week_code, target_year)
            
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
                    rounds = int(pd.to_numeric(row.get('Rounds', 0), errors='coerce') or 0)
                    
                    def clean_to_int(val):
                        """Safely converts clean raw counts directly to integers, stripping text markers."""
                        if pd.isna(val): return 0
                        clean_str = str(val).replace('%', '').strip()
                        return int(float(clean_str)) if clean_str else 0
                    
                    # --- DIRECT EXTRACTION PROTOCOL ---
                    # Pulling whole counts and raw percentages straight from the source file
                    raw_4in = clean_to_int(row.get('4IN', 0))
                    four_in_pct = clean_to_int(row.get('4IN %', 0))
                    
                    calculated_in = clean_to_int(row.get('IN', 0))
                    in_pct = clean_to_int(row.get('IN %', 0))
                    
                    calculated_on = clean_to_int(row.get('ON', 0))
                    on_pct = clean_to_int(row.get('ON %', 0))
                    
                    calculated_off = clean_to_int(row.get('OFF', 0))
                    off_pct = clean_to_int(row.get('OFF %', 0))
                    
                    total_points_thrown = pd.to_numeric(row.get('Total Points', 0), errors='coerce') or 0
                    opp_points_thrown = pd.to_numeric(row.get('Opp Points', 0), errors='coerce') or 0

                    # --- FIXED PLACEMENT BONUS MATRIX ENGINE ---
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
                        if calculated_tier == "Tier 1 (>= 8.5)": podium_points = 8
                        elif calculated_tier == "Tier 2 (8.0 - 8.49)": podium_points = 2
                    elif podium_place in [7, 8]:
                        if calculated_tier == "Tier 1 (>= 8.5)": podium_points = 6
                    elif podium_place in [9, 10, 11, 12]:
                        if calculated_tier == "Tier 1 (>= 8.5)": podium_points = 4
                    elif podium_place in [13, 14, 15, 16]:
                        if calculated_tier == "Tier 1 (>= 8.5)": podium_points = 2
                    elif podium_place >= 17:
                        if calculated_tier == "Tier 1 (>= 8.5)": podium_points = 1

                    # Stage Play Rule Overrides
                    if season_stage == "Regular League Play (Stats Only)":
                        podium_points = 0
                    elif season_stage == "League Championship / Playoffs":
                        if calculated_tier == "Tier 1 (>= 8.5)":
                            podium_points = max(podium_points, 20) if ppr > 8.5 else max(podium_points, 10)

                    compiled_rows.append({
                        'Display Name': disp_name,
                        'First Name': first_name,
                        'Last Name': last_name,
                        'Email': email_addr,
                        'PPR': ppr,
                        'DPR': dpr,
                        'OPP PPR': opp_ppr,
                        '4IN': raw_4in,
                        '4IN %': four_in_pct,
                        'IN': calculated_in,
                        'IN %': in_pct,
                        'ON': calculated_on,
                        'ON %': on_pct,
                        'OFF': calculated_off,
                        'OFF %': off_pct,
                        'Rounds': rounds,
                        'Total Points': total_points_thrown,
                        'Opp Points': opp_points_thrown,
                        'Game Name': str(bracket_data['Division']),
                        'Year': target_year,
                        'Month': selected_week_code,
                        'Location': str(row.get('Location', 'Delaware Cornhole')),
                        'Event': "Switch / BD",
                        'Season': "Summer 2026" if target_year == 2026 else "Historical Season",
                        'Level': str(row.get('Level', 'Open')),
                        'Name Check': f"{first_name} {last_name}".strip(),
                        'Podiums': 1 if podium_place in [1, 2, 3] else 0,
                        'Month 2': dynamic_month,
                        'Rolling Year': dynamic_rolling
                    })

            df_output = pd.DataFrame(compiled_rows)

            # Initialize the empty separator column slot directly in memory before ordering
            df_output[''] = ""

            # PRECISE LIST ORDER COMPLIANCE MATRIX MATED TO POWER BI TARGET SHEET MODEL
            pbi_schema_columns = [
                'Display Name', 'First Name', 'Last Name', 'Email', 'PPR', 'DPR', 
                'OPP PPR', '4IN', '4IN %', 'IN', 'IN %', 'ON', 'ON %', 'OFF', 'OFF %', 
                'Rounds', 'Total Points', 'Opp Points', 'Game Name', 'Year', 'Month', 
                'Location', 'Event', 'Season', 'Level', 'Name Check', 'Podiums', 
                'Month 2', '', 'Rolling Year'
            ]
            
            final_pbi_export = df_output[pbi_schema_columns].copy()

            st.balloons()

            st.subheader(f"📈 Power BI Mapped Row Structure Matrix Preview")
            st.dataframe(final_pbi_export.head(10), use_container_width=True)

            st.subheader("📦 Export Operations Suite")
            
            output_buffer = io.BytesIO()
            with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
                final_pbi_export.to_excel(writer, sheet_name='PPR Data', index=False)
            excel_data = output_buffer.getvalue()

            st.download_button(
                label="📥 Download Append Entries to Excel Workbook (.xlsx)",
                data=excel_data,
                file_name=f"PPR_Data_Import_Append_{selected_week_code}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# ==============================================================================
# MODULE 2: LEAGUE OS CORE OPERATIONS (HISTORICAL ANALYTICS HUB)
# ==============================================================================
elif app_mode == "⚙️ League OS Core Operations":
    st.title("⚙️ League OS Core Historical Lookup Hub")
    st.write("Upload your complete master database spreadsheet file to run timeline aggregations.")
    
    master_file = st.file_uploader("📥 Upload Master League History Dataset (.xlsx Master File)", type=["xlsx"])
    
    if master_file:
        try:
            master_df = pd.read_excel(master_file, sheet_name='PPR Data')
            master_df.columns = [str(c).strip() for c in master_df.columns]
            st.success("✅ Master 'PPR Data' sheet loaded successfully into engine memory.")
            
            st.sidebar.header("🔍 Filter Scope Settings")
            timeframe_scope = st.sidebar.selectbox(
                "Select Target Review Scope:",
                ["Specific Week", "Full Dataset Overview"]
            )
            
            if timeframe_scope == "Specific Week":
                unique_weeks = sorted(master_df['Month'].dropna().unique(), key=parse_week_num) if 'Month' in master_df.columns else []
                target_week = st.sidebar.selectbox("Choose Target Week:", unique_weeks)
                filtered_df = master_df[master_df['Month'] == target_week]
                
                st.subheader(f"📊 Historical Summary Breakdown for {target_week}")
                st.dataframe(filtered_df, use_container_width=True)
            else:
                st.subheader("📋 Comprehensive Database Structure Layout Overview")
                st.dataframe(master_df.head(100), use_container_width=True)
        except Exception as e:
            st.error(f"Error alignment verification failed: {e}")