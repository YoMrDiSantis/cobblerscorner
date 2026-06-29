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
    st.info("💡 **Drop All Files Together:** Upload your ScoreMagic, Bracket Standings, and Player Rosters simultaneously. The internal engine will match them using their internal Game Names automatically.")
    
    uploaded_files = st.file_uploader(
        "Drop complete weekly files here (.csv format supported)", 
        type=["csv"], 
        accept_multiple_files=True,
        key="uploader_stream"
    )

    if uploaded_files:
        # Separate raw structures
        stats_list = []
        brackets_by_game = {}
        rosters_by_game = {}
        
        for f in uploaded_files:
            try:
                content = f.read().decode("utf-8", errors="ignore")
                df = pd.read_csv(io.StringIO(content))
                df.columns = df.columns.str.strip()
                
                # Identify file structure and anchor to Game Name
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
                st.error(f"Error indexing file {f.name}: {ex}")

        st.success(f"Successfully loaded `{len(stats_list)}` Stat Groups, `{len(brackets_by_game)}` Bracket Maps, and `{len(rosters_by_game)}` Roster Lookups.")

        if st.button("🚀 Execute Processing Engine & Compile Outputs", key="run_main_engine"):
            all_processed_records = []
            potw_records = []
            canva_brackets_summary = []
            canva_top_pprs = []

            dynamic_month, dynamic_rolling = get_dynamic_date_meta(selected_week_code, target_year)

            for stats_df in stats_list:
                if len(stats_df) == 0:
                    continue

                # Universal Key: Game Name mapping anchor
                game_title = str(stats_df['Game Name'].iloc[0]).strip() if 'Game Name' in stats_df.columns else "Open Tournament"
                game_key = game_title.lower()

                # Bind corresponding bracket and rosters safely
                bracket_df = brackets_by_game.get(game_key)
                roster_df = rosters_by_game.get(game_key)

                # Determine Bracket Averages for Tier Scoring
                stats_df['PPR_Numeric'] = pd.to_numeric(stats_df['PPR'], errors='coerce').fillna(0.0)
                bracket_avg_ppr = stats_df['PPR_Numeric'].mean() if len(stats_df) > 0 else 0.0
                calculated_tier = "Tier 1" if bracket_avg_ppr >= 8.5 else ("Tier 2" if bracket_avg_ppr >= 8.0 else ("Tier 3" if bracket_avg_ppr >= 7.5 else ("Tier 4" if bracket_avg_ppr >= 7.0 else "Tier 5")))

                # Cross-reference Bracket Placements
                placement_map = {}
                if bracket_df is not None:
                    for _, row in bracket_df.iterrows():
                        place = str(row.get('Place', '0')).strip()
                        for p_idx in ['PlayerEmail1', 'PlayerEmail2', 'PlayerEmail3', 'PlayerEmail4']:
                            if p_idx in bracket_df.columns:
                                email = str(row.get(p_idx, '')).strip().lower()
                                if email and email != 'nan':
                                    placement_map[email] = place

                # Cross-reference Roster Club Names
                club_map = {}
                if roster_df is not None:
                    email_col = 'Player Email' if 'Player Email' in roster_df.columns else ('Email' if 'Email' in roster_df.columns else '')
                    club_col = 'Club Name' if 'Club Name' in roster_df.columns else ''
                    if email_col and club_col:
                        for _, row in roster_df.iterrows():
                            email = str(row.get(email_col, '')).strip().lower()
                            club = str(row.get(club_col, '')).strip()
                            if email and email != 'nan':
                                club_map[email] = club

                resolved_event = compute_dynamic_event_type(game_title)
                resolved_location = compute_dynamic_location(game_title)

                for _, row in stats_df.iterrows():
                    try:
                        p_email = str(row.get('Email', '')).strip().lower()
                        d_name = str(row.get('Display Name', '')).strip()
                        if not d_name or p_email == 'nan' or p_email == '':
                            continue

                        f_name = str(row.get('First Name', '')).strip()
                        l_name = str(row.get('Last Name', '')).strip()
                        
                        assigned_place = placement_map.get(p_email, "0")
                        assigned_club = club_map.get(p_email, "")
                        
                        podium_int = int(assigned_place) if str(assigned_place).isdigit() else 0
                        is_podium_finish = 1 if podium_int in [1, 2, 3] else 0

                        # Read all required statistics
                        ppr_val = float(row.get('PPR_Numeric', 0.0))
                        dpr_val = float(pd.to_numeric(row.get('DPR', 0), errors='coerce') or 0.0)
                        opp_ppr_val = float(pd.to_numeric(row.get('OPP PPR', 0), errors='coerce') or 0.0)
                        val_4in = clean_percent_to_int(row.get('4IN', 0))
                        pct_4in = clean_percent_to_int(row.get('4IN %', 0))
                        val_in = clean_percent_to_int(row.get('IN', 0))
                        pct_in = clean_percent_to_int(row.get('IN %', 0))
                        val_on = clean_percent_to_int(row.get('ON', 0))
                        pct_on = clean_percent_to_int(row.get('ON %', 0))
                        val_off = clean_percent_to_int(row.get('OFF', 0))
                        pct_off = clean_percent_to_int(row.get('OFF %', 0))
                        tot_rounds = int(pd.to_numeric(row.get('Rounds', 0), errors='coerce') or 0)
                        pts_total = int(pd.to_numeric(row.get('Total Points', 0), errors='coerce') or 0)
                        pts_opp = int(pd.to_numeric(row.get('Opp Points', 0), errors='coerce') or 0)

                        # --- LEAGUE POINT MATRICES ---
                        bonus_points = 0
                        if podium_int == 1:
                            bonus_points = 20 if "Tier 1" in calculated_tier else (10 if "Tier 2" in calculated_tier else (8 if "Tier 3" in calculated_tier else (6 if "Tier 4" in calculated_tier else 4)))
                        elif podium_int == 2:
                            bonus_points = 15 if "Tier 1" in calculated_tier else (8 if "Tier 2" in calculated_tier else (6 if "Tier 3" in calculated_tier else (4 if "Tier 4" in calculated_tier else 2)))
                        elif podium_int == 3:
                            bonus_points = 12 if "Tier 1" in calculated_tier else (6 if "Tier 2" in calculated_tier else (4 if "Tier 3" in calculated_tier else (2 if "Tier 4" in calculated_tier else 0)))
                        elif podium_int == 4:
                            bonus_points = 10 if "Tier 1" in calculated_tier else (4 if "Tier 2" in calculated_tier else (2 if "Tier 3" in calculated_tier else 0))
                        elif podium_int in [5, 6]:
                            bonus_points = 8 if "Tier 1" in calculated_tier else (2 if "Tier 2" in calculated_tier else 0)
                        elif podium_int in [7, 8] and "Tier 1" in calculated_tier: bonus_points = 6
                        elif podium_int in [9, 10, 11, 12] and "Tier 1" in calculated_tier: bonus_points = 4
                        elif podium_int in [13, 14, 15, 16] and "Tier 1" in calculated_tier: bonus_points = 2
                        elif podium_int >= 17 and "Tier 1" in calculated_tier: bonus_points = 1

                        flat_record = {
                            'Display Name': d_name, 'First Name': f_name, 'Last Name': l_name, 'Email': p_email,
                            'PPR': ppr_val, 'DPR': dpr_val, 'OPP PPR': opp_ppr_val,
                            '4IN': val_4in, '4IN %': pct_4in, 'IN': val_in, 'IN %': pct_in,
                            'ON': val_on, 'ON %': pct_on, 'OFF': val_off, 'OFF %': pct_off,
                            'Rounds': tot_rounds, 'Total Points': pts_total, 'Opp Points': pts_opp,
                            'Game Name': game_title, 'Year': int(target_year), 'Month': str(selected_week_code),
                            'Location': resolved_location, 'Event': resolved_event, 'Season': f"Summer {target_year}",
                            'Level': "Open", 'Name Check': "", 'Podiums': is_podium_finish,
                            'Month 2': dynamic_month, 'Club': assigned_club, 'Rolling Year': dynamic_rolling
                        }
                        all_processed_records.append(flat_record)

                        # Filter for local leaderboard
                        if any(m in str(assigned_club).upper() for m in ["DELAWARE CORNHOLE", "DE BAGGERS", "DE CORNHOLE"]):
                            potw_records.append({
                                'Player': f"{f_name} {l_name}".strip() if f_name else d_name,
                                'Club': assigned_club, 'Game': game_title, 'Tier': calculated_tier,
                                'Finish': assigned_place if podium_int > 0 else "Unplaced",
                                'PPR': ppr_val, 'Points Awarded': bonus_points
                            })
                        canva_top_pprs.append({'Name': d_name, 'PPR': ppr_val, 'Game': game_title})
                    except Exception:
                        continue

                if bracket_df is not None and len(bracket_df) > 0:
                    t1_teams = bracket_df[bracket_df['Place'].astype(str) == '1']['Team Name'].fillna("Unknown").tolist()
                    canva_brackets_summary.append(f"🥇 **{game_title}:** {t1_teams[0] if t1_teams else 'N/A'} ({calculated_tier})")

            # --- RENDER SUITE INTERFACES ---
            if all_processed_records:
                st.write("---")
                st.header("📋 Pipeline 1: Power BI Import Sheet (Flat Append Set)")
                df_pbi = pd.DataFrame(all_processed_records)
                
                pbi_cols = [
                    'Display Name', 'First Name', 'Last Name', 'Email', 'PPR', 'DPR', 
                    'OPP PPR', '4IN', '4IN %', 'IN', 'IN %', 'ON', 'ON %', 'OFF', 'OFF %', 
                    'Rounds', 'Total Points', 'Opp Points', 'Game Name', 'Year', 'Month', 
                    'Location', 'Event', 'Season', 'Level', 'Name Check', 'Podiums', 
                    'Month 2', 'Club', 'Rolling Year'
                ]
                df_pbi_final = df_pbi.reindex(columns=pbi_cols).fillna("")
                st.dataframe(df_pbi_final, use_container_width=True)

                buffer_pbi = io.BytesIO()
                with pd.ExcelWriter(buffer_pbi, engine='openpyxl') as writer:
                    df_pbi_final.to_excel(writer, sheet_name='PPR Data', index=False)
                
                st.download_button(
                    label="📥 Download Power BI Append Set (.xlsx)",
                    data=buffer_pbi.getvalue(),
                    file_name=f"PBI_PPR_Import_Append_{selected_week_code}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                st.write("---")
                st.header("🏆 Pipeline 2: Delaware Cornhole Player of the Week Matrix")
                if potw_records:
                    df_potw = pd.DataFrame(potw_records)
                    df_potw_grouped = df_potw.groupby('Player').agg({
                        'Club': 'first', 'PPR': 'mean', 'Points Awarded': 'sum'
                    }).reset_index().sort_values(by='Points Awarded', ascending=False)
                    st.dataframe(df_potw_grouped, use_container_width=True)

                    buffer_potw = io.BytesIO()
                    with pd.ExcelWriter(buffer_potw, engine='openpyxl') as writer:
                        df_potw_grouped.to_excel(writer, sheet_name='POTW Leaderboard', index=False)
                    
                    st.download_button(
                        label="📥 Download POTW Leaderboard (.xlsx)",
                        data=buffer_potw.getvalue