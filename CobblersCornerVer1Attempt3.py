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
                        'Sanitized_Player_Name': clean_player_name(disp_name),
                        'PPR': ppr,
                        'OPP PPR': opp_ppr,
                        'DPR': dpr,
                        'Rounds': rounds,
                        '4Bagger %': four_bagger,
                        'OFF %': off_board,
                        'Tournament Podium Bonus Pts': podium_points,
                        'Month': selected_week_code,
                        'Year': target_year,
                        'Division': bracket_data['Division'],
                        'Calculated Bracket Avg PPR': round(bracket_avg_ppr, 2),
                        'Assigned Tier Category': calculated_tier,
                        'Column Y Designation': "League Championship" if season_stage == "League Championship / Playoffs" else "Regular Season"
                    })

            df_output = pd.DataFrame(compiled_rows)

            # ==================================================================
            # ADVANCED MASTER INDEX BONUS ENGINES (IMAGE_4F1E61 MATRIX RULES)
            # ==================================================================
            # 1. Dynamic Tiered Volume Round Bonus Execution
            df_output['Round Bonus'] = df_output['Rounds'].apply(
                lambda r: 12 if r >= 300 else (8 if r >= 200 else (5 if r >= 100 else 0))
            )

            # 2. Ranked PPR Performance Bonus Field Scaling (Top 20 get 20 down to 1)
            df_output = df_output.sort_values(by='PPR', ascending=False).reset_index(drop=True)
            df_output['PPR Bonus Pts'] = 0
            for idx in range(min(20, len(df_output))):
                df_output.loc[idx, 'PPR Bonus Pts'] = 20 - idx

            # 3. Ranked Board Precision Bonus Field Scaling (Top 10 Lowest OFF% get 10 down to 1)
            df_output = df_output.sort_values(by='OFF %', ascending=True).reset_index(drop=True)
            df_output['OFF% Bonus Points'] = 0
            for idx in range(min(10, len(df_output))):
                df_output.loc[idx, 'OFF% Bonus Points'] = 10 - idx

            # Compute Absolute Comprehensive Metric Score
            df_output['Total'] = (
                df_output['Tournament Podium Bonus Pts'] + 
                df_output['Round Bonus'] + 
                df_output['PPR Bonus Pts'] + 
                df_output['OFF% Bonus Points']
            )

            st.balloons()

            # --- DISPLAY DASHBOARD PREVIEWS ---
            st.subheader(f"📈 Performance Preview Leaderboard for {selected_week_code}")
            preview_df = df_output.sort_values(by='Total', ascending=False)
            st.dataframe(preview_df[['Display Name', 'PPR', 'OFF %', 'Tournament Podium Bonus Pts', 'Round Bonus', 'PPR Bonus Pts', 'OFF% Bonus Points', 'Total', 'Assigned Tier Category']], use_container_width=True)

            # --- SYSTEM DOWNLOAD MATRIX BUTTONS ---
            col_out1, col_out2, col_out3 = st.columns(3)
            with col_out1:
                st.subheader("📊 Power BI Update Line")
                csv_pbi = io.StringIO()
                df_output.to_csv(csv_pbi, index=False)
                st.download_button("📥 Download Append CSV", csv_pbi.getvalue().encode('utf-8'), f"BI_Append_{selected_week_code}.csv", "text/csv")
            with col_out2:
                st.subheader("🎨 Canva Graphic Matrix")
                top_10 = df_output.sort_values(by='Total', ascending=False).head(10)
                canva_df = top_10[['Total', 'Display Name', 'PPR', 'OFF %']].copy()
                canva_df.columns = ['POINTS', 'PLAYER', 'PPR', 'OFF_PCT']
                csv_canva = io.StringIO()
                canva_df.to_csv(csv_canva, index=False)
                st.download_button("📥 Download Canva CSV", csv_canva.getvalue().encode('utf-8'), f"Canva_{selected_week_code}.csv", "text/csv")
            with col_out3:
                st.subheader("📈 Local Ledger")
                csv_ledger = io.StringIO()
                df_output.sort_values(by='Total', ascending=False).to_csv(csv_ledger, index=False)
                st.download_button("📥 Download Standings Ledger", csv_ledger.getvalue().encode('utf-8'), f"Ledger_{selected_week_code}.csv", "text/csv")

            # --- FULL FORMAT WEEKLY FACEBOOK RECAP GENERATOR ---
            st.write("---")
            st.subheader("🔊 Output 4: Comprehensive Facebook Post Hype Text")
            
            top_10_leaders = df_output.sort_values(by='Total', ascending=False).head(10)
            
            post_text = f"## 🌽 DELAWARE CORNHOLE CONNECTION • {selected_week_code.upper()} NIGHTLY RECAP\n"
            post_text += "====================================================\n\n"
            post_text += f"The weekly stats are locked, the brackets are settled, and the dynamic tier scoring matrix has run perfectly! Here are your top point-getters and efficiency kings on the court tonight: 🎉👇\n\n"
            
            post_text += f"🏆 **NIGHTLY TOP 10 LEADERBOARD (Indexed Placement & Performance Engine):\n"
            post_text += "----------------------------------------------------\n"
            for rank, (_, row) in enumerate(top_10_leaders.iterrows(), 1):
                post_text += f"{rank:02d}. 👤 **{row['Display Name']}** — {row['PPR']:.2f} PPR | **{int(row['Total'])} Total Pts** ({row['Assigned Tier Category']})\n"
            
            post_text += f"\n👑 **THE EFFICIENCY SECTOR RADARS:**\n"
            post_text += "----------------------------------------------------\n"
            post_text += f"🔥 **Highest Overall PPR Execution:** {df_output.sort_values(by='PPR', ascending=False).iloc[0]['Display Name']} ({df_output.sort_values(by='PPR', ascending=False).iloc[0]['PPR']:.2f} Avg PPR)\n"
            post_text += f"🎯 **4-Bagger Streak King:** {df_output.sort_values(by='4Bagger %', ascending=False).iloc[0]['Display Name']} ({int(df_output.sort_values(by='4Bagger %', ascending=False).iloc[0]['4Bagger %'])}% max value rate)\n"
            post_text += f"❌ **Clean Board Execution (Lowest OFF%):** {df_output.sort_values(by='OFF %', ascending=True).iloc[0]['Display Name']} (Only missing the board {df_output.sort_values(by='OFF %', ascending=True).iloc[0]['OFF %']:.1f}% of throws)\n\n"

            post_text += "📝 **League Director Executive Commentary Notes:** \n"
            post_text += "[Insert specific bracket story points, upset matches, and milestone callouts here]\n\n"
            post_text += "====================================================\n"
            post_text += "Slide true, practice hard, and we'll see you back on the boards next week! 🌽🕳"
            st.text_area("Copy and Paste Directly into Facebook Layout Engine", value=post_text, height=450)

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
        
        # Flexibly align Master Historical naming convention from spreadsheet layout
        if 'Player' in master_df.columns:
            master_df['Display Name'] = master_df['Player']
        elif 'Display Name' not in master_df.columns:
            st.error("❌ Could not locate player identity column. Make sure your history file features a 'Player' or 'Display Name' column.")
            st.stop()
            
        st.success("✅ Master Database loaded successfully into engine memory.")
        
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
        
        # Apply Filters Dynamically Based on Choices WITH CORRECT SYNTAX
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
            filtered_df = filtered_df[filtered_df['Month'].apply(parse_week_num) <= mid_cutoff]
            writeup_title = f"MID-YEAR MILESTONE REPORT (W.1 - W.{mid_cutoff})"
            
        elif timeframe_scope == "Full Year Review":
            unique_years = sorted(master_df['Year'].dropna().unique()) if 'Year' in master_df.columns else [2026, 2025]
            target_year = st.sidebar.selectbox("Choose Target Year:", unique_years)
            filtered_df = filtered_df[filtered_df['Year'] == target_year]
            writeup_title = f"{target_year} COMPREHENSIVE YEAR-END REVIEW"

        # --- EXECUTING MAIN HISTORICAL AGGREGATIONS ---
        if timeframe_scope != "Year-Over-Year Comparison (2025 vs 2026)":
            if not filtered_df.empty:
                # Process base stats grouping
                player_stats = filtered_df.groupby('Display Name').agg({
                    'Total': 'sum',
                    'Rounds': 'sum',
                    'PPR': 'mean',
                    'OFF %': 'mean',
                    '4Bagger %': 'mean'
                }).reset_index()
                
                # Render Historical Leaderboard Dashboard Tabs
                st.subheader(f"📊 Live Dashboard: {writeup_title}")
                tab1, tab2 = st.tabs(["🏆 Leaderboards & Totals", "📝 Automated Facebook Write-up Text"])
                
                with tab1:
                    col_m1, col_m2 = st.columns(2)
                    with col_m1:
                        st.markdown("**Top 10 Cumulative Point Scorers:**")
                        st.dataframe(player_stats.sort_values(by='Total', ascending=False).head(10), use_container_width=True)
                    with col_m2:
                        st.markdown(f"**Top Efficiency Radars (Min. {min_rounds_filter} Rounds Thrown):**")
                        st.dataframe(player_stats[player_stats['Rounds'] >= min_rounds_filter].sort_values(by='PPR', ascending=False).head(10), use_container_width=True)
                
                with tab2:
                    # --- BREAKOUT CHRONOLOGICAL HALVES CALCULATION ENGINE ---
                    breakout_list = []
                    for player, group in filtered_df.groupby('Display Name'):
                        sorted_group = group.copy()
                        sorted_group['wk_idx'] = sorted_group['Month'].apply(parse_week_num)
                        sorted_group = sorted_group.sort_values(by='wk_idx')
                        
                        mid_idx = len(sorted_group) // 2
                        half_a = sorted_group.iloc[:mid_idx]
                        half_b = sorted_group.iloc[mid_idx:]
                        
                        rounds_a = half_a['Rounds'].sum()
                        rounds_b = half_b['Rounds'].sum()
                        
                        if rounds_a >= min_rounds_filter and rounds_b >= min_rounds_filter:
                            ppr_a = half_a['PPR'].mean()
                            ppr_b = half_b['PPR'].mean()
                            off_a = half_a['OFF %'].mean()
                            off_b = half_b['OFF %'].mean()
                            
                            ppr_delta = ppr_b - ppr_a
                            off_delta = off_a - off_b
                            
                            if ppr_delta > 0 or off_delta > 0:
                                breakout_list.append({
                                    'Player': player,
                                    'PPR Delta': ppr_delta,
                                    'OFF Delta': off_delta,
                                    'PPR Form': ppr_b
                                })
                    
                    df_breakouts = pd.DataFrame(breakout_list)
                    top_breakout_str = "None met the criteria round thresholds"
                    if not df_breakouts.empty:
                        best_grower = df_breakouts.sort_values(by='PPR Delta', ascending=False).iloc[0]
                        top_breakout_str = f"📈 **{best_grower['Player']}** — Boosted their average scoring by **+{best_grower['PPR Delta']:.2f} PPR** during the second half of this stretch!"

                    # Construct Hype Report
                    top_scorer = player_stats.sort_values(by='Total', ascending=False).iloc[0]
                    top_round_workhorse = player_stats.sort_values(by='Rounds', ascending=False).iloc[0]
                    
                    report_text = f"## 🌽 DELAWARE CORNHOLE CONNECTION • {writeup_title}\n"
                    report_text += "====================================================\n\n"
                    report_text += f"The historical books have been compiled across our master ledger. Here are our major milestone updates and standout performers for this look-up timeline block:\n\n"
                    report_text += f"👑 **CUMULATIVE POINT LEADERS TOP 5:**\n"
                    report_text += "----------------------------------------------------\n"
                    for rank, (_, r) in enumerate(player_stats.sort_values(by='Total', ascending=False).head(5).iterrows(), 1):
                        report_text += f"{rank}. **{r['Display Name']}** — {int(r['Total'])} Total Points ({r['PPR']:.2f} Historical Avg PPR)\n"
                    
                    report_text += f"\n🎯 **STAMINA & WORKHORSE MILESTONES:**\n"
                    report_text += "----------------------------------------------------\n"
                    report_text += f"• **Most Dedicated Workhorse:** {top_round_workhorse['Display Name']} throwing a massive **{int(top_round_workhorse['Rounds'])} rounds** over this period!\n"
                    
                    report_text += f"\n📈 **LEAGUE BREAKOUT PACESETTERS (Min. {min_rounds_filter} Rounds Per Half Validation Gate):**\n"
                    report_text += "----------------------------------------------------\n"
                    report_text += f"{top_breakout_str}\n\n"
                    report_text += "====================================================\n"
                    report_text += "Slide true, practice hard, and keep climbing the leaderboard! 🌽🕳"
                    
                    st.text_area("Copy Generated Narrative Summary:", value=report_text, height=400)
            else:
                st.warning("No data found matching this specified criteria filter block.")

        # --- YEAR-OVER-YEAR COMPARISON CALCULATION MODULE ---
        else:
            st.subheader("📅 Year-Over-Year Career Development Engine (2025 vs 2026)")
            
            df_2025 = master_df[master_df['Year'] == 2025]
            df_2026 = master_df[master_df['Year'] == 2026]
            
            stats_2025 = df_2025.groupby('Display Name').agg({'Rounds': 'sum', 'PPR': 'mean', 'OFF %': 'mean'}).reset_index()
            stats_2026 = df_2026.groupby('Display Name').agg({'Rounds': 'sum', 'PPR': 'mean', 'OFF %': 'mean'}).reset_index()
            
            yoy_merged = pd.merge(stats_2025, stats_2026, on='Display Name', suffixes=('_2025', '_2026'))
            
            # Apply Double-Gate Moveable Round filter validation rule checks
            yoy_qualified = yoy_merged[
                (yoy_merged['Rounds_2025'] >= min_rounds_filter) & 
                (yoy_merged['Rounds_2026'] >= min_rounds_filter)
            ].copy()
            
            if not yoy_qualified.empty:
                yoy_qualified['PPR Delta'] = yoy_qualified['PPR_2026'] - yoy_qualified['PPR_2025']
                yoy_qualified['OFF Delta'] = yoy_qualified['OFF %_2025'] - yoy_qualified['OFF %_2026']
                
                st.markdown(f"### 📈 Career Developers Ranked By PPR Jump (Min. {min_rounds_filter} Rounds in BOTH Seasons)")
                display_yoy = yoy_qualified[['Display Name', 'PPR_2025', 'PPR_2026', 'PPR Delta', 'OFF Delta']].sort_values(by='PPR Delta', ascending=False)
                st.dataframe(display_yoy, use_container_width=True)
                
                # FIXED MULTI-LINE STRING ENCLOSURE LITERAL ERROR HERE
                yoy_text = f"## 📈 DELAWARE CORNHOLE YEAR-OVER-YEAR MASTER DEVELOPERS (Min. {min_rounds_filter} Rounds Threshold)\n"
                yoy_text += "====================================================\n\n"
                yoy_text += "We ran the comparative analytics between the full 2025 season and the current 2026 campaign to reward our most dedicated grinders. Check out who made the biggest career jumps on the boards:\n\n"
                
                for idx, (_, row) in enumerate(display_yoy.head(5).iterrows(), 1):
                    yoy_text += f"{idx:02d}. 🏆 **{row['Display Name']}**\n"
                    yoy_text += f"   • **PPR Progress:** +{row['PPR Delta']:.2f} (Climbed from {row['PPR_2025']:.2f} in '25 to {row['PPR_2026']:.2f} in '26!)\n"
                    yoy_text += f"   • **Precision Accuracy:** Slashed off-the-board misses by -{row['OFF Delta']:.1f}%\n\n"
                
                yoy_text += "====================================================\n"
                yoy_text += "The development is real! Keep putting in those reps on the practice boards. 🌽🕳"
                st.text_area("Copy Year-Over-Year Write-up Text Box:", value=yoy_text, height=350)
            else:
                st.warning(f"No players cleared the double-gate qualification check of having thrown at least {min_rounds_filter} rounds in BOTH 2025 and 2026.")