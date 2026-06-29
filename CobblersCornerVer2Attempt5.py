import streamlit as st
import pandas as pd
import numpy as np
import io
import re
import csv
import sys

# Maximize CSV parser limits to avoid overflow crashes
csv.field_size_limit(sys.maxsize)

# --- MASTER LAYOUT INITIALIZATION ---
st.set_page_config(
    page_title="Delaware Cornhole League Power BI Formatter", 
    layout="wide"
)

st.title("📊 Power BI Direct Import Formatter")
st.subheader("Single-Purpose Clean Pipeline Matrix")

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

# --- CONTROL VARIABLES PANEL ---
col1, col2 = st.columns(2)
with col1:
    selected_week_code = st.text_input("League Week Code Designation:", value="W.23")
with col2:
    target_year = st.selectbox("Select Target Year", [2026, 2025, 2024], index=0)

st.write("---")

# --- FILE INPUT UPLOADER ---
uploaded_files = st.file_uploader(
    "Drop all weekly ScoreMagic stats, Bracket Standings, and Player Rosters together here (.csv format):", 
    type=["csv"], 
    accept_multiple_files=True
)

if uploaded_files:
    stats_list = []
    brackets_by_game = {}
    rosters_by_game = {}
    
    # Ingest and classify all files immediately
    for f in uploaded_files:
        try:
            f.seek(0)
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
            st.error(f"Error reading file {f.name}: {ex}")

    # Process if we have data to compile
    if stats_list:
        all_processed_records = []
        dynamic_month, dynamic_rolling = get_dynamic_date_meta(selected_week_code, target_year)

        for stats_df in stats_list:
            if len(stats_df) == 0:
                continue

            game_title = str(stats_df['Game Name'].iloc[0]).strip() if 'Game Name' in stats_df.columns else "Open Tournament"
            game_key = game_title.lower()

            bracket_df = brackets_by_game.get(game_key)
            roster_df = rosters_by_game.get(game_key)

            # Map bracket finishes directly to player emails
            placement_map = {}
            if bracket_df is not None:
                for _, row in bracket_df.iterrows():
                    place = str(row.get('Place', '0')).strip()
                    for p_idx in ['PlayerEmail1', 'PlayerEmail2', 'PlayerEmail3', 'PlayerEmail4']:
                        if p_idx in bracket_df.columns:
                            email = str(row.get(p_idx, '')).strip().lower()
                            if email and email != 'nan' and email != '':
                                placement_map[email] = place

            # Map club memberships to emails
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
            resolved_location = compute_dynamic_location(game_title)

            # Loop over stats rows to structure data
            for _, row in stats_df.iterrows():
                try:
                    p_email = str(row.get('Email', '')).strip().lower()
                    d_name = str(row.get('Display Name', '')).strip()
                    if not d_name or p_email == 'nan' or p_email == '':
                        continue

                    f_name = str(row.get('First Name', '')).strip()
                    l_name = str(row.get('Last Name', '')).strip()
                    
                    # Track down the tournament result
                    assigned_place = placement_map.get(p_email, "0")
                    assigned_club = club_map.get(p_email, "")
                    
                    podium_int = int(assigned_place) if str(assigned_place).isdigit() else 0
                    is_podium_finish = 1 if podium_int in [1, 2, 3] else 0

                    # Convert raw numeric stats values safely
                    ppr_val = float(pd.to_numeric(row.get('PPR', 0), errors='coerce') or 0.0)
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

                    # Create layout dict containing your requested "Finish Place" column
                    flat_record = {
                        'Display Name': d_name, 'First Name': f_name, 'Last Name': l_name, 'Email': p_email,
                        'PPR': ppr_val, 'DPR': dpr_val, 'OPP PPR': opp_ppr_val,
                        '4IN': val_4in, '4IN %': pct_4in, 'IN': val_in, 'IN %': pct_in,
                        'ON': val_on, 'ON %': pct_on, 'OFF': val_off, 'OFF %': pct_off,
                        'Rounds': tot_rounds, 'Total Points': pts_total, 'Opp Points': pts_opp,
                        'Game Name': game_title, 'Year': int(target_year), 'Month': str(selected_week_code),
                        'Location': resolved_location, 'Event': resolved_event, 'Season': f"Summer {target_year}",
                        'Level': "Open", 'Name Check': "", 'Podiums': is_podium_finish,
                        'Month 2': dynamic_month, 'Club': assigned_club, 'Rolling Year': dynamic_rolling,
                        'Finish Place': int(assigned_place) if assigned_place.isdigit() else assigned_place
                    }
                    all_processed_records.append(flat_record)
                except Exception:
                    continue

        if all_processed_records:
            df_final = pd.DataFrame(all_processed_records)
            
            # Explicitly layout your absolute final Power BI structural column order
            pbi_cols = [
                'Display Name', 'First Name', 'Last Name', 'Email', 'PPR', 'DPR', 
                'OPP PPR', '4IN', '4IN %', 'IN', 'IN %', 'ON', 'ON %', 'OFF', 'OFF %', 
                'Rounds', 'Total Points', 'Opp Points', 'Game Name', 'Year', 'Month', 
                'Location', 'Event', 'Season', 'Level', 'Name Check', 'Podiums', 
                'Month 2', 'Club', 'Rolling Year', 'Finish Place'
            ]
            df_final = df_final.reindex(columns=pbi_cols).fillna("")

            # Display Preview Data table
            st.success(f"Processing Successful! Parsed `{len(df_final)}` total performance records.")
            st.dataframe(df_final, use_container_width=True)

            # Direct Export Block (No complex loops or internal buttons to break states)
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_final.to_excel(writer, sheet_name='PPR Data', index=False)
            
            st.download_button(
                label="📥 Download Power BI Master File (.xlsx)",
                data=buffer.getvalue(),
                file_name=f"PowerBI_Import_Week_{selected_week_code}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
        else:
            st.warning("No data found matching formatting logic. Check that the columns match your source files.")
else:
    st.info("Upload your raw weekly files above to instantly process your Power BI document.")