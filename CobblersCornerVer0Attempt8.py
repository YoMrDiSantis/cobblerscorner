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

                    # Globals / Stage Modifications
                    if season_stage == "Regular League Play (Stats Only)":
                        podium_points = 0
                    elif season_stage == "League Championship / Playoffs":
                        if calculated_tier == "Tier 1 (>= 8.5)":
                            podium_points = max(podium_points, 20) if ppr > 8.5 else max(podium_points, 10)

                    total_weekly_score = ppr_bonus + off_bonus + round_bonus + podium_points

                    compiled_rows.append({
                        'Name Check': disp_name,
                        'First Name': first_name,
                        'Last Name': last_name,
                        'Email': email_addr,
                        'Sanitized_Player_Name': clean_player_name(disp_name),
                        'PPR': ppr,
                        'OPP PPR': opp_ppr,
                        'DPR': dpr,
                        'Rounds': rounds,
                        '4Bagger %': four_bagger,
                        'OFF %': off_board,
                        'PPR Bonus Pts': ppr_bonus,
                        'OFF% Bonus Points': off_bonus,
                        'Tournament Podium Bonus Pts': podium_points,
                        'Round Bonus': round_bonus,
                        'Total': total_weekly_score,
                        'Month': selected_week_code,
                        'Year': target_year,
                        'Division': bracket_data['Division'],
                        'Calculated Bracket Avg PPR': round(bracket_avg_ppr, 2),
                        'Assigned Tier Category': calculated_tier,
                        'Column Y Designation': "League Championship" if season_stage == "League Championship / Playoffs" else "Regular Season"
                    })

            df_output = pd.DataFrame(compiled_rows)
            st.balloons()

            # --- DISPLAY DASHBOARD PREVIEWS ---
            st.subheader(f"📈 Performance Preview Leaderboard for {selected_week_code}")
            preview_df = df_output[df_output['Rounds'] >= 10].sort_values(by='Total', ascending=False)
            st.dataframe(preview_df[['Name Check', 'PPR', 'OFF %', 'Tournament Podium Bonus Pts', 'Total', 'Assigned Tier Category']], use_container_width=True)

            # --- SYSTEM DOWNLOAD MATRIX BUTTONS ---
            col_out1, col_out2, col_out3 = st.columns(3)
            with col_out1:
                st.subheader("📊 Power BI Update Line")
                csv_pbi = io.StringIO()
                df_output.to_csv(csv_pbi, index=False)
                st.download_button("📥 Download Append CSV", csv_pbi.getvalue().encode('utf-8'), f"BI_Append_{selected_week_code}.csv", "text/csv")
            with col_out2:
                st.subheader("🎨 Canva Graphic Matrix")
                top_10 = df_output[df_output['Rounds'] >= 10].sort_values(by='Total', ascending=False).head(10)
                canva_df = top_10[['Total', 'Name Check', 'PPR', 'OFF %']].copy()
                canva_df.columns = ['POINTS', 'PLAYER', 'PPR', 'OFF_PCT']
                csv_canva = io.StringIO()
                canva_df.to_csv(csv_canva, index=False)
                st.download_button("📥 Download Canva CSV", csv_canva.getvalue().encode('utf-8'), f"Canva_{selected_week_code}.csv", "text/csv")
            with col_out3:
                st.subheader("📈 Local Ledger")
                csv_ledger = io.StringIO()
                df_output.sort_values(by='Total', ascending=False).to_csv(csv_ledger, index=False)
                st.download_button("📥 Download Standings Ledger", csv_ledger.getvalue().encode('utf-8'), f"Ledger_{selected_week_code}.csv", "text/csv")

            # --- WEEKLY FACEBOOK RECAP GENERATOR ---
            st.write("---")
            st.subheader("🔊 Output 4: Abbreviated Facebook Post Hype Text")
            
            top_10_leaders = df_output[df_output['Rounds'] >= 10].sort_values(by='Total', ascending=False).head(10)
            
            post_text = f"## 🌽 DELAWARE CORNHOLE CONNECTION • {selected_week_code.upper()} RECAP\n\n"
            post_text += f"The weekly stats are locked and the dynamic point matrix has been calculated perfectly against our bracket average PPR guidelines! Check out our performance leaders below. 📊👇\n\n"
            
            post_text += f"📸 **IMAGE 1: THE WEEKLY TOP 10 LEADERBOARD**\n"
            for rank, (_, row) in enumerate(top_10_leaders.iterrows(), 1):
                post_text += f"{rank}. **{row['Name Check']}** — {row['PPR']:.2f} PPR | **{int(row['Total'])} Pts** ({row['Assigned Tier Category']})\n"
            
            post_text += f"\n👑 **WEEKLY PACE SETTERS:**\n"
            post_text += f"• **Highest PPR Performance:** {df_output.sort_values(by='PPR', ascending=False).iloc[0]['Name Check']} ({df_output.sort_values(by='PPR', ascending=False).iloc[0]['PPR']:.2f})\n"
            post_text += f"• **4Bagger Excellence:** {df_output.sort_values(by='4Bagger %', ascending=False).iloc[0]['Name Check']} ({int(df_output.sort_values(by='4Bagger %', ascending=False).iloc[0]['4Bagger %'])}%)\n"

            post_text += f"\nSee you all on the courts next week! 🌽🕳"
            st.text_area("Copy and Paste Directly into Facebook Layout Engine", value=post_text, height=350)

# ==============================================================================
# MODULE 2: LEAGUE OS CORE OPERATIONS (HISTORICAL ANALYTICS HUB)
# ==============================================================================
elif app_mode == "⚙️ League OS Core Operations":
    st.title("⚙️ League OS Core Historical Lookup Hub")
    st.write("Upload your historical master database file to run multi-week reviews, season metrics, and track breakout player progression.")
    
    master_file = st.file_uploader("📥 Upload Master League History Dataset (Power BI Master CSV)", type=["csv"])
    
    if master_file:
        master_df = pd.read_csv(master_file)
        master_df.columns = master_df.columns.str.strip()
        
        st.success("¼ Master Database loaded successfully into engine memory.")
        
        # Central Config Controls
        st.sidebar.header("🔍 Filter Scope Settings")
        timeframe_scope = st.sidebar.selectbox(
            "Select Target Review Scope:",
            ["Specific Week", "Specific Month / Custom Group", "Mid-Year Checkpoint", "Full Year Review", "Year-Over-Year Comparison (2025 vs 2026)"]
        )
        
        # Moveable Volume Filter Box
        min_rounds_filter = st.sidebar.number_input("⚡ Moveable Gate: Minimum Rounds Per Comparison Period:", min_value=1, value=100, step=10)
        
        filtered_df = master_df.copy()
        writeup_title = ""
        
        # Apply Filters Dynamically Based on Choices
        if timeframe_scope == "Specific Week":
            unique_weeks = sorted(master_df['Month'].dropna().unique(), key=parse_week_num) if 'Month' in master_df.columns else []
            target_week = st.sidebar.selectbox("Choose Target Week:", unique_weeks)
            filtered_df = filtered_df[filtered_df['Month'] == target_week]
            writeup_title = f"WEEK {str(target_week).upper()} SUMMARY"
            
        elif timeframe_scope == "Specific Month / Custom Group":
            unique_weeks = sorted(master_df['Month'].dropna().unique(), key=parse_week_num) if 'Month' in master_df.columns else []
            target_group = st.sidebar.multiselect("Select Weeks to Group Together into Timeframe:", unique_weeks)
            if target_group:
                filtered_df = filtered_df[filtered_df['Month'].isin(target_group)]
            writeup_title = "CUSTOM TIMEFRAME BLOCK REPORT"
            
        elif timeframe_scope == "Mid-Year Checkpoint":
            unique_weeks = sorted(master_df['Month'].dropna().unique(), key=parse_week_num) if 'Month' in master_df.columns else []
            mid_cutoff = st.sidebar.slider("Isolate Weeks Up To Cutoff:", min_value=1, max_value=len(unique_weeks)+1, value=18)
            filtered_df = filtered_df[filtered_df['Month'].apply(parse_week_num)