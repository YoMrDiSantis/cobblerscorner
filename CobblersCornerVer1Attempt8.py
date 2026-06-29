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
    st.info("💡 **Drop All Files Together:** Upload ScoreMagic stats, Bracket Standings, and Player Rosters simultaneously.")
    
    uploaded_files = st.file_uploader(
        "Drop complete weekly files here (.csv format supported)", 
        type=["csv"], 
        accept_multiple_files=True,
        key="uploader_stream"
    )

    if uploaded_files:
        file_registry = {}
        
        # Ingest files and protect against column format discrepancies
        for f in uploaded_files:
            token = parse_filename_token(f.name)
            if token not in file_registry:
                file_registry[token] = {"stats": None, "bracket": None, "roster": None}
            
            try:
                content = f.read().decode("utf-8", errors="ignore")
                df = pd.read_csv(io.StringIO(content))
                df.columns = df.columns.str.strip()
                
                if "PPR" in df.columns:
                    file_registry[token]["stats"] = df
                elif "Place" in df.columns or "Team Name" in df.columns:
                    file_registry[token]["bracket"] = df
                elif "Club Name" in df.columns or "Player Email" in df.columns:
                    file_registry[token]["roster"] = df
            except Exception as ex:
                st.error(f"Error checking file {f.name}: {ex}")

        st.success(f"Tracked and isolated `{len(file_registry)}` tournament key matches.")

        # Main processing trigger button
        if st.button("🚀 Execute Processing Engine & Compile Outputs", key="run_main_engine"):
            all_processed_records = []
            potw_records = []
            canva_brackets_summary = []
            canva_top_pprs = []

            dynamic_month, dynamic_rolling = get_dynamic_date_meta(selected_week_code, target_year)

            for token, group in file_registry.items():
                stats_df = group["stats"]
                bracket_df = group["bracket"]
                roster_df = group["roster"]

                if stats_df is None:
                    continue  

                # Calculate Tier placement thresholds safely
                stats_df['PPR_Numeric'] = pd.to_numeric(stats_df['PPR'], errors='coerce').fillna(0.0)
                bracket_avg_ppr = stats_df['PPR_Numeric'].mean() if len(stats_df) > 0 else 0.0

                if bracket_avg_ppr >= 8.5:
                    calculated_tier = "Tier 1"
                elif bracket_avg_ppr >= 8.0:
                    calculated_tier = "Tier 2"
                elif bracket_avg_ppr >= 7.5:
                    calculated_tier = "Tier 3"
                elif bracket_avg_ppr >= 7.0:
                    calculated_tier = "Tier 4"
                else:
                    calculated_tier = "Tier 5"

                # Extract Bracket Placings
                placement_map = {}
                if bracket_df is not None:
                    for _, row in bracket_df.iterrows():
                        place = str(row.get('Place', '0')).strip()
                        for p_idx in ['PlayerEmail1', 'PlayerEmail2', 'PlayerEmail3', 'PlayerEmail4']:
                            if p_idx in bracket_df.columns:
                                email = str(row.get(p_idx, '')).strip().lower()
                                if email and email != 'nan' and email != '':
                                    placement_map[email] = place

                # Extract Club Affiliation Lookup Tables
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

                game_title = str(stats_df['Game Name'].iloc[0]).strip() if 'Game Name' in stats_df.columns else "Open Tournament"
                resolved_event = compute_dynamic_event_type(game_title)
                resolved_location = compute_dynamic_location(game_title)
                resolved_level = "Open"

                # Compile each rows information cleanly
                for _, row in stats_df.iterrows():
                    try:
                        p_email = str(row.get('Email', '')).strip().lower()
                        d_name = str(row.get('Display Name', '')).strip()
                        f_name = str(row.get('First Name', '')).strip()
                        l_name = str(row.get('Last Name', '')).strip()
                        
                        if not d_name or p_email == 'nan' or p_email == '':
                            continue

                        assigned_place = placement_map.get(p_email, "0")
                        assigned_club = club_map.get(p_email, "")
                        
                        podium_int = int(assigned_place) if str(assigned_place).isdigit() else 0
                        is_podium_finish = 1 if podium_int in [1, 2, 3] else 0

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

                        # --- PODIUM POINT SCALE SYSTEM ---
                        bonus_points = 0
                        if podium_int == 1:
                            if "Tier 1" in calculated_tier: bonus_points = 20
                            elif "Tier 2" in calculated_tier: bonus_points = 10
                            elif "Tier 3" in calculated_tier: bonus_points = 8
                            elif "Tier 4" in calculated_tier: bonus_points = 6
                            else: bonus_points = 4
                        elif podium_int == 2:
                            if "Tier 1" in calculated_tier: bonus_points = 15
                            elif "Tier 2" in calculated_tier: bonus_points = 8
                            elif "Tier 3" in calculated_tier: bonus_points = 6
                            elif "Tier 4" in calculated_tier: bonus_points = 4
                            else: bonus_points = 2
                        elif podium_int == 3:
                            if "Tier 1" in calculated_tier: bonus_points = 12
                            elif "Tier 2" in calculated_tier: bonus_points = 6
                            elif "Tier 3" in calculated_tier: bonus_points = 4
                            elif "Tier 4" in calculated_tier: bonus_points = 2
                        elif podium_int == 4:
                            if "Tier 1" in calculated_tier: bonus_points = 10
                            elif "Tier 2" in calculated_tier: bonus_points = 4
                            elif "Tier 3" in calculated_tier: bonus_points = 2
                        elif podium_int in [5, 6]:
                            if "Tier 1" in calculated_tier: bonus_points = 8
                            elif "Tier 2" in calculated_tier: bonus_points = 2
                        elif podium_int in [7, 8]:
                            if "Tier 1" in calculated_tier: bonus_points = 6
                        elif podium_int in [9, 10, 11, 12]:
                            if "Tier 1" in calculated_tier: bonus_points = 4
                        elif podium_int in [13, 14, 15, 16]:
                            if "Tier 1" in calculated_tier: bonus_points = 2
                        elif podium_int >= 17:
                            if "Tier 1" in calculated_tier: bonus_points = 1

                        flat_record = {
                            'Display Name': d_name, 'First Name': f_name, 'Last Name': l_name, 'Email': p_email,
                            'PPR': ppr_val, 'DPR': dpr_val, 'OPP PPR': opp_ppr_val,
                            '4IN': val_4in, '4IN %': pct_4in, 'IN': val_in, 'IN %': pct_in,
                            'ON': val_on, 'ON %': pct_on, 'OFF': val_off, 'OFF %': pct_off,
                            'Rounds': tot_rounds, 'Total Points': pts_total, 'Opp Points': pts_opp,
                            'Game Name': game_title, 'Year': int(target_year), 'Month': str(selected_week_code),
                            'Location': resolved_location, 'Event': resolved_event, 'Season': f"Summer {target_year}",
                            'Level': resolved_level, 'Name Check': "", 'Podiums': is_podium_finish,
                            'Month 2': dynamic_month, 'Club': assigned_club, 'Rolling Year': dynamic_rolling
                        }
                        all_processed_records.append(flat_record)

                        # Match native club qualifiers
                        if any(m in str(assigned_club).upper() for m in ["DELAWARE CORNHOLE", "DE BAGGERS", "DE CORNHOLE"]):
                            potw_records.append({
                                'Player': f"{f_name} {l_name}".strip() if f_name else d_name,
                                'Club': assigned_club, 'Game': game_title, 'Tier': calculated_tier,
                                'Finish': assigned_place if podium_int > 0 else "Unplaced",
                                'PPR': ppr_val, 'Points Awarded': bonus_points
                            })
                        
                        canva_top_pprs.append({'Name': d_name, 'PPR': ppr_val, 'Game': game_title})
                    except Exception as row_err:
                        continue

                if bracket_df is not None and len(bracket_df) > 0:
                    t1_teams = bracket_df[bracket_df['Place'].astype(str) == '1']['Team Name'].fillna("Unknown").tolist()
                    t1_str = t1_teams[0] if t1_teams else "N/A"
                    canva_brackets_summary.append(f"🥇 **{game_title}:** {t1_str} ({calculated_tier})")

            # --- RENDERING GENERATED DATA SETS ---
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
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="pbi_download_btn"
                )

                st.write("---")
                st.header("🏆 Pipeline 2: Delaware Cornhole Player of the Week Matrix")
                if potw_records:
                    df_potw = pd.DataFrame(potw_records)
                    df_potw_grouped = df_potw.groupby('Player').agg({
                        'Club': 'first',
                        'PPR': 'mean',
                        'Points Awarded': 'sum'
                    }).reset_index().sort_values(by='Points Awarded', ascending=False)
                    
                    st.dataframe(df_potw_grouped, use_container_width=True)

                    buffer_potw = io.BytesIO()
                    with pd.ExcelWriter(buffer_potw, engine='openpyxl') as writer:
                        df_potw_grouped.to_excel(writer, sheet_name='POTW Leaderboard', index=False)
                    
                    st.download_button(
                        label="📥 Download POTW Leaderboard (.xlsx)",
                        data=buffer_potw.getvalue(),
                        file_name=f"POTW_Leaderboard_{selected_week_code}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="potw_download_btn"
                    )
                else:
                    st.info("No Delaware Cornhole club affiliations matched from the Roster files to generate points.")

                st.write("---")
                st.header("🎨 Pipeline 3: Canva Clipboard Text Generation Engine")
                
                canva_raw_output = [
                    f"✨ DELAWARE CORNHOLE WEEKLY REPORT • {selected_week_code} ✨\n",
                    "🏆 TOURNAMENT PODIUM CHAMPIONS"
                ]
                for summary in canva_brackets_summary:
                    canva_raw_output.append(summary)
                
                if canva_top_pprs:
                    canva_raw_output.append("\n🔥 TOP INDIVIDUAL PERFORMANCE HONORS (HIGHEST SINGLE PPRS)")
                    df_top = pd.DataFrame(canva_top_pprs).sort_values(by='PPR', ascending=False).head(5)
                    for idx, (_, s_row) in enumerate(df_top.iterrows(), 1):
                        canva_raw_output.append(f"{idx}. {s_row['Name']} — {s_row['PPR']:.2f} PPR ({str(s_row['Game']).strip()})")

                st.text_area("Copy-Paste Block directly into Canva Layout Template Tools:", value="\n".join(canva_raw_output), height=250)
                st.balloons()
            else:
                st.error("No valid entries were extracted. Double check that the ScoreMagic files have explicit data rows.")

# ==============================================================================
# MODULE 2: LEAGUE OS CORE MASTER REGISTRY VIEW
# ==============================================================================
elif app_mode == "⚙️ League OS Core Master Registry View":
    st.title("⚙️ League OS Historical Master Database Viewer")
    st.write("Upload your existing centralized master data repository below to run point lookups.")
    
    historical_file = st.file_uploader("📥 Ingest Master Historical Record Sheet (.xlsx Format)", type=["xlsx"], key="hist_uploader")
    
    if historical_file:
        try:
            df_hist = pd.read_excel(historical_file, sheet_name='PPR Data')
            df_hist.columns = df_hist.columns.str.strip()
            st.success(f"Successfully loaded database containing `{len(df_hist)}` archived rows.")
            st.dataframe(df_hist.head(100), use_container_width=True)
        except Exception as e:
            st.error(f"Registry processing layout mismatch encountered: {e}")