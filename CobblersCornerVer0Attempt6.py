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

# --- CORE UTILITY PIPELINE FUNCTIONS ---
def find_col_by_keyword(cols, keyword):
    """Safely locates columns by checking for text keywords to handle header variances."""
    for c in cols:
        if keyword.lower() in str(c).lower(): 
            return c
    return None

def clean_player_name(name_val):
    """Sanitizes decorative badges, emojis, and extra white space from player names."""
    if pd.isna(name_val):
        return ""
    text = str(name_val).strip()
    text = re.sub(r'[^\w\s\.\-]', '', text)
    return " ".join(text.split())

# ==============================================================================
# MODULE 1: PRESET TIMEFRAME STATS GENERATOR (AUTOMATED PLAYOFF TRIGGERS)
# ==============================================================================
if app_mode == "📊 Preset Timeframe Stats Generator":
    st.title("🎛️ Delaware Cornhole Tournament-Weighted Matrix Suite")
    
    st.sidebar.header("📅 Timeframe Target Scope")
    timeframe_type = st.sidebar.radio("Select Breakdown Scope", options=["Weekly", "Monthly", "Annual / End of Year"], index=0)
    target_year = st.sidebar.selectbox("Select Target Year", [2026, 2025, 2024], index=0)

    if timeframe_type == "Weekly":
        week_number = st.sidebar.number_input("League Week Number", min_value=1, max_value=52, value=18)
        selected_week_code = f"W.{int(week_number):02d}"
    else:
        selected_week_code = "All"

    st.sidebar.write("---")
    st.sidebar.header("🏆 Season Format Phase Modifiers")
    season_stage = st.sidebar.selectbox(
        "Default Fallback Mode:",
        ["Standard Tournament Night", "Regular League Play (Stats Only)"]
    )

    # --- 50-FILE MASSIVE FILE UPLOADER UNDER 100MB ---
    st.header("📥 Central Data Stream Ingestion")
    st.info("💡 **Drop up to 50 Files:** Drag your historical sheets, rosters, and tournament exports together here.")
    
    uploaded_files = st.file_uploader(
        "Drag and drop ALL league files here at once (Supports up to 50 CSV files)", 
        type=["csv"], 
        accept_multiple_files=True
    )

    all_loaded_dfs = []
    member_df = None

    if uploaded_files:
        for file in uploaded_files:
            file_name = file.name.lower()
            if any(k in file_name for k in ["ppr", "master", "historical", "import", "data", "week", "tourney"]):
                try:
                    df_chunk = pd.read_csv(file)
                    all_loaded_dfs.append(df_chunk)
                except Exception as e:
                    st.error(f"Error loading file `{file.name}`: {e}")
            elif any(k in file_name for k in ["email", "member", "roster", "directory"]):
                member_df = pd.read_csv(file)
                st.success(f"👥 Ingested Club Roster Directory: `{file.name}`")

        if all_loaded_dfs:
            st.success(f"📂 Consolidated and queued **{len(all_loaded_dfs)} Statistics Files** into active processing memory.")

    st.write("---")

    if st.button("🚀 Process Streams & Compile 4-Output Matrix"):
        if not all_loaded_dfs or member_df is None:
            st.error("Missing critical data layers! Please drop your tournament/stats files and your 'Email List' roster together into the uploader box.")
        else:
            master_df = pd.concat(all_loaded_dfs, ignore_index=True)
            
            # Standardize headers
            master_df.columns = master_df.columns.str.strip()
            member_df.columns = member_df.columns.str.strip()

            # Cross-reference member verification emails
            mem_email_col = find_col_by_keyword(member_df.columns, 'email') or member_df.columns[0]
            valid_member_emails = set(member_df[mem_email_col].dropna().astype(str).str.strip().str.lower().unique())

            master_email_col = find_col_by_keyword(master_df.columns, 'email') or 'Email'
            master_df['Is_Member'] = master_df[master_email_col].fillna('').astype(str).str.strip().str.lower().apply(lambda x: x in valid_member_emails)
            master_df['Sanitized_Player_Name'] = master_df['Name Check'].apply(clean_player_name)
            
            # Format numbers safely
            for num_col in ['PPR', 'OPP PPR', 'OFF %', 'Rounds', 'DPR', '4Bagger %', 'PPR Bonus Pts', 'OFF% Bonus Points', 'Tournament Podium Bonus Pts', 'Round Bonus', 'Total']:
                actual_col = find_col_by_keyword(master_df.columns, num_col)
                if actual_col and actual_col in master_df.columns:
                    master_df[actual_col] = pd.to_numeric(master_df[actual_col], errors='coerce').fillna(0)

            # GHOST FILTER: Erase double bracket entries for same player on same night
            tourney_id_col = find_col_by_keyword(master_df.columns, 'tournament id') or find_col_by_keyword(master_df.columns, 'bracket') or 'Month'
            master_df = master_df.drop_duplicates(subset=['Sanitized_Player_Name', 'Year', tourney_id_col], keep='first')

            # Slice data by active timeframe
            master_df['Year_Str'] = master_df['Year'].astype(str)
            year_filtered = master_df[master_df['Year_Str'] == str(target_year)]
            
            if timeframe_type == "Weekly":
                sliced_df = year_filtered[year_filtered['Month'].astype(str) == selected_week_code].copy()
                context_label = f"Week {week_number}"
            else:
                sliced_df = year_filtered.copy()
                context_label = f"{target_year} Campaign"

            if sliced_df.empty:
                st.warning(f"No match criteria records located for {context_label} in your processed files.")
            else:
                # Dynamic column mapping strings
                ppr_b_col = find_col_by_keyword(sliced_df.columns, 'ppr bonus') or 'PPR Bonus Pts'
                off_b_col = find_col_by_keyword(sliced_df.columns, 'off% bonus') or 'OFF% Bonus Points'
                tou_b_col = find_col_by_keyword(sliced_df.columns, 'tournament podium') or 'Tournament Podium Bonus Pts'
                rou_b_col = find_col_by_keyword(sliced_df.columns, 'round bonus') or 'Round Bonus'
                rounds_col = find_col_by_keyword(sliced_df.columns, 'rounds') or 'Rounds'
                dpr_col = find_col_by_keyword(sliced_df.columns, 'dpr') or 'DPR'
                four_b_col = find_col_by_keyword(sliced_df.columns, '4bagger') or '4Bagger %'
                off_pct_col = find_col_by_keyword(sliced_df.columns, 'off the board') or find_col_by_keyword(sliced_df.columns, 'off %') or 'OFF %'
                div_col = find_col_by_keyword(sliced_df.columns, 'division') or find_col_by_keyword(sliced_df.columns, 'tier') or 'Division'

                # Fallback to Advanced if division tags are missing
                if div_col not in sliced_df.columns:
                    sliced_df[div_col] = "Advanced"

                # --- COLUMN Y DYNAMIC AUTOMATION MATCHING ENGINE ---
                # Column Y is typically mapped as index 24 (the 25th column) or via a specific keyword 
                col_y_target = master_df.columns[24] if len(master_df.columns) > 24 else 'Month'
                
                def dynamic_row_matrix_evaluator(row):
                    val_y = str(row[col_y_target]).strip().lower()
                    current_div = str(row[div_col]).strip().lower()
                    base_tou_points = row[tou_b_col] if tou_b_col in row else 0
                    current_ppr = row['PPR']
                    
                    # Target explicit League Championship string in Column Y
                    if "league championship" in val_y or "playoff" in val_y:
                        if "advanced" in current_div:
                            if current_ppr > 8.5:
                                return max(base_tou_points, 20)
                            return max(base_tou_points, 10)
                        return base_tou_points
                    
                    # Regular League Play (Zero out bracket bonuses)
                    if season_stage == "Regular League Play (Stats Only)":
                        return 0
                        
                    # Standard fallback tournament mode
                    return base_tou_points

                sliced_df[tou_b_col] = sliced_df.apply(dynamic_row_matrix_evaluator, axis=1)

                # Consolidated weekly statistics profile
                player_week_summary = sliced_df.groupby(['Sanitized_Player_Name', 'Is_Member', div_col]).agg(
                    Sum_of_Rounds=(rounds_col, 'sum'),
                    PPR_Average=('PPR', 'mean'),
                    OPP_PPR_Average=('OPP PPR', 'mean'),
                    DPR_Average=(dpr_col, 'mean' if dpr_col in sliced_df.columns else 'PPR'),
                    Four_Bagger_Average=(four_b_col, 'mean' if four_b_col in sliced_df.columns else 'PPR'),
                    Off_The_Board_Average=(off_pct_col, 'mean'),
                    PPF_Pts=(ppr_b_col, 'sum' if ppr_b_col in sliced_df.columns else 'PPR'),
                    OFF_Pts=(off_b_col, 'sum' if off_b_col in sliced_df.columns else 'PPR'),
                    Tou_Pts=(tou_b_col, 'sum' if tou_b_col in sliced_df.columns else 'PPR'),
                    Rou_Pts=(rou_b_col, 'sum' if rou_b_col in sliced_df.columns else 'PPR')
                ).reset_index()

                player_week_summary['Total_Points'] = (
                    player_week_summary['PPF_Pts'] + player_week_summary['OFF_Pts'] + 
                    player_week_summary['Tou_Pts'] + player_week_summary['Rou_Pts']
                )

                # Universal Round Filter 
                qualified_field = player_week_summary[player_week_summary['Sum_of_Rounds'] >= 30].copy()
                total_competitors_count = len(qualified_field)

                club_field = qualified_field[qualified_field['Is_Member'] == True].copy()
                top_10_leaders = club_field.sort_values(by='Total_Points', ascending=False).head(10)
                top_10_names = set(top_10_leaders['Sanitized_Player_Name'].unique())

                # Compute dynamic floating cutoff lines with inclusive tie support
                if len(club_field) >= 20:
                    ppr_cutoff_val = club_field['PPR_Average'].nsmallest(len(club_field)).iloc[-20]
                else:
                    ppr_cutoff_val = club_field['PPR_Average'].min() if not club_field.empty else 0.0

                if len(club_field) >= 10:
                    off_cutoff_val = club_field['Off_The_Board_Average'].nsmallest(10).iloc[-1]
                else:
                    off_cutoff_val = club_field['Off_The_Board_Average'].max() if not club_field.empty else 0.0

                # Separate honorable mention fields
                not_in_top_10 = club_field[~club_field['Sanitized_Player_Name'].isin(top_10_names)]
                honors_ppr_field = not_in_top_10[not_in_top_10['PPR_Average'] >= ppr_cutoff_val].sort_values(by='PPR_Average', ascending=False)
                honors_off_field = not_in_top_10[not_in_top_10['Off_The_Board_Average'] <= off_cutoff_val].sort_values(by='Off_The_Board_Average', ascending=True)

                # Superlative math summaries
                highest_ppr_row = club_field.sort_values(by='PPR_Average', ascending=False).iloc[0] if not club_field.empty else None
                highest_4b_row = club_field.sort_values(by='Four_Bagger_Average', ascending=False).iloc[0] if not club_field.empty else None
                most_rounds_row = club_field.sort_values(by='Sum_of_Rounds', ascending=False).iloc[0] if not club_field.empty else None
                top_5_dpr = club_field.sort_values(by='DPR_Average', ascending=False).head(5)

                st.balloons()

                # --- THE 4 SYSTEM OUTPUT CHANNELS ---
                out_col1, out_col2, out_col3 = st.columns(3)
                
                with out_col1:
                    st.subheader("📊 Output 1: Power BI")
                    csv_pbi = io.StringIO()
                    master_df.to_csv(csv_pbi, index=False)
                    st.download_button("📥 Download Power BI CSV", csv_pbi.getvalue().encode('utf-8'), f"PPR_PowerBI_Import_{target_year}.csv", "text/csv")
                
                with out_col2:
                    st.subheader("🎨 Output 2: Canva Bulk")
                    canva_df = top_10_leaders[['Total_Points', 'Sanitized_Player_Name', 'PPR_Average', 'Off_The_Board_Average']].copy()
                    canva_df.columns = ['POINTS', 'PLAYER', 'PPR', 'OFF_PCT']
                    csv_canva = io.StringIO()
                    canva_df.to_csv(csv_canva, index=False)
                    st.download_button("📥 Download Canva CSV", csv_canva.getvalue().encode('utf-8'), f"Canva_Data_W{week_number}.csv", "text/csv")
                
                with out_col3:
                    st.subheader("📈 Output 3: Weekly Ledger")
                    csv_ledger = io.StringIO()
                    player_week_summary.sort_values(by='Total_Points', ascending=False).to_csv(csv_ledger, index=False)
                    st.download_button("📥 Download Standings Ledger", csv_ledger.getvalue().encode('utf-8'), f"Weekly_Ledger_W{week_number}.csv", "text/csv")

                st.write("---")
                st.subheader("🔊 Output 4: Abbreviated Facebook Post Hype Text")
                
                # ABBREVIATED HIGHLIGHT FORMAT Focus completely matches your Canva card structures
                post_text = f"## 🌽 DELAWARE CORNHOLE CONNECTION • WEEK {week_number} RECAP\n\n"
                post_text += f"The brackets are locked, ghost entries are cleaned, and the numbers are official! Check out our weekly award winners and performance leaders below. Images are loading now! 📊👇\n\n"
                
                post_text += f"📸 **IMAGE 1: THE OPEN DIVISION TOP 10**\n"
                for rank, (_, row) in enumerate(top_10_leaders.iterrows(), 1):
                    post_text += f"{rank}. **{row['Sanitized_Player_Name']}** — {row['PPR_Average']:.2f} PPR | {int(row['Off_The_Board_Average'])}% OFF | **{int(row['Total_Points'])} Pts**\n"
                
                post_text += f"\n📸 **IMAGE 2: HONORS & WEEKLY SUPERLATIVES**\n\n"
                
                post_text += f"🔥 **HIGHEST PPR (Not in Top 10 • Cutoff: ≥ {ppr_cutoff_val:.2f}):**\n"
                post_text += f"{', '.join(honors_ppr_field['Sanitized_Player_Name'].unique()[:10])}\n\n"
                    
                post_text += f"🎯 **LOWEST OFF% (Not in Top 10 • Cutoff: ≤ {int(off_cutoff_val)}%):**\n"
                post_text += f"{', '.join(honors_off_field['Sanitized_Player_Name'].unique()[:10])}\n\n"

                post_text += f"👑 **WEEKLY PACE SETTERS:**\n"
                if highest_ppr_row is not None:
                    post_text += f"• **Highest PPR:** {highest_ppr_row['Sanitized_Player_Name']} ({highest_ppr_row['PPR_Average']:.2f})\n"
                if highest_4b_row is not None:
                    post_text += f"• **4Bagger of the Week:** {highest_4b_row['Sanitized_Player_Name']} ({int(highest_4b_row['Four_Bagger_Average'])}%)\n"
                if most_rounds_row is not None:
                    post_text += f"• **Most Rounds:** {most_rounds_row['Sanitized_Player_Name']} ({int(most_rounds_row['Sum_of_Rounds'])} Rounds)\n\n"

                post_text += f"📊 **PRECISION HOME DESIGNS • TOP 5 DPR**\n"
                for idx, (_, row) in enumerate(top_5_dpr.iterrows(), 1):
                    post_text += f"{idx}. {row['Sanitized_Player_Name']} ({row['DPR_Average']:.2f} DPR)\n"

                post_text += f"\nSee you all out on the boards next week! Get those bags ready! 🌽🕳"
                
                st.text_area("Copy and Paste Directly into Facebook Layout Engine", value=post_text, height=450)

# ==============================================================================
# MODULE 2: LEAGUE OS CORE OPERATIONS
# ==============================================================================
elif app_mode == "⚙️ League OS Core Operations":
    st.title("⚙️ League OS Operating Hub & Data Router")
    st.write("Manage day-of tournament configurations and sync active directories.")