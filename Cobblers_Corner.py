import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="DE Cornhole Automation Engine", layout="wide")
st.title("🌽 Delaware Cornhole Ultimate Stats Engine")
st.write("Drop your raw weekly files here. The app handles Member Validation, Placement Points, Performance Bonuses, and Matrix Formatting instantly.")

# App Mode Selector
tab1, tab2 = st.tabs(["1. Process Weekly League Night", "2. Update DEPotY Seasonal Ledger"])

with tab1:
    st.header("Step 1: Upload Weekly Tournament Data")
    
    colA, colB = st.columns(2)
    with colA:
        uploaded_magic = st.file_uploader("1. Upload ScoreMagic Player Stats CSV", type=["csv"])
        uploaded_bracket = st.file_uploader("2. Upload Bracket Standings CSV (Provides Finish Placements)", type=["csv"])
    with colB:
        uploaded_members = st.file_uploader("3. Upload Club / Valid Members Email List CSV", type=["csv"])
        
    st.header("Step 2: Tourney Parameters")
    c1, c2, c3 = st.columns(3)
    with c1:
        location = st.text_input("Tournament Location", value="Birdies")
        level = st.selectbox("Division / Tier", ["Open", "Competitive Tier 2", "Advanced", "Tier 1"])
    with c2:
        event_type = st.text_input("Event Style", value="Switch / BD")
        season = st.text_input("Current Season", value="Summer 2026")
    with c3:
        week_num = st.number_input("League Week (e.g., 22)", min_value=1, max_value=52, value=22)
        game_date = st.date_input("Tournament Date", datetime.date.today())

    # Generate timeline metadata automatically
    week_code = f"W.{int(week_num):02d}"
    year_val = game_date.year
    month_2_val = game_date.strftime("%B")
    month_to_num_map = {"January": 101, "February": 102, "March": 103, "April": 104, "May": 105, "June": 106, "July": 107, "August": 108, "September": 109, "October": 110, "November": 111, "December": 112}
    rolling_num = month_to_num_map.get(month_2_val, 100)

    if st.button("🚀 Process & Calculate Everything"):
        if not (uploaded_magic and uploaded_bracket and uploaded_members):
            st.error("Please upload all three requested files above to run the cross-reference engine.")
        else:
            # Load Dataframes
            magic_df = pd.read_csv(uploaded_magic)
            bracket_df = pd.read_csv(uploaded_bracket)
            member_df = pd.read_csv(uploaded_members)
            
            # Clean Columns
            magic_df.columns = magic_df.columns.str.strip()
            bracket_df.columns = bracket_df.columns.str.strip()
            member_df.columns = member_df.columns.str.strip()
            
            # 1. Map Member Database via Email
            # Assuming member list has an 'Email' or 'Player Email' column
            member_email_col = 'Email' if 'Email' in member_df.columns else (
                'Player Email' if 'Player Email' in member_df.columns else member_df.columns[0]
            )
            valid_member_emails = set(member_df[member_email_col].dropna().str.strip().str.lower().unique())
            
            # 2. Extract Tournament Placements from Bracket file
            # Map Player Emails to their absolute Finish Place from the Bracket Table
            player_placements = {}
            for _, row in bracket_df.iterrows():
                place = int(row['Place'])
                # Look across all possible player email slots in a team row
                for email_col in ['PlayerEmail1', 'PlayerEmail2', 'PlayerEmail3', 'PlayerEmail4']:
                    if email_col in bracket_df.columns and pd.notna(row[email_col]):
                        email_str = str(row[email_col]).strip().lower()
                        if email_str:
                            player_placements[email_str] = place

            # 3. Process the Master Throw Statistics File
            processed = magic_df.copy()
            processed['Name Check'] = processed['First Name'].fillna('') + ' ' + processed['Last Name'].fillna('')
            processed['Email_Lower'] = processed['Email'].fillna('').str.strip().str.lower()
            
            # Check Membership Status
            processed['Is_Member'] = processed['Email_Lower'].apply(lambda x: x in valid_member_emails)
            
            # Pull Placement from Bracket Mapping
            processed['Bracket Place'] = processed['Email_Lower'].map(player_placements).fillna(99).astype(int)
            
            # 4. Calculate Points using your Official DEPotY Point Matrix
            def calc_points(row):
                # RULE: Only reward verified Delaware Cornhole Members
                if not row['Is_Member']:
                    return 0, 0, 0, 0, 0
                
                # A. Tournament Placing Base Points
                place = row['Bracket Place']
                placement_pts = 0
                podium_flag = 0
                if place == 1: 
                    placement_pts = 20
                    podium_flag = 1
                elif place == 2: 
                    placement_pts = 15
                    podium_flag = 1
                elif place == 3: 
                    placement_pts = 12
                    podium_flag = 1
                elif place == 4: 
                    placement_pts = 10
                elif place == 5: 
                    placement_pts = 8
                
                # B. PPR Bonus Points
                ppr = row['PPR']
                ppr_bonus = 0
                if ppr >= 8.5: ppr_bonus = 10
                elif ppr >= 8.0: ppr_bonus = 5
                
                # C. OFF% Bonus Points (Lower OFF% = higher precision)
                off_pct = row['OFF %']
                off_bonus = 0
                if off_pct <= 4.0: off_bonus = 10
                elif off_pct <= 6.0: off_bonus = 5
                
                total_pts = placement_pts + ppr_bonus + off_bonus
                return total_pts, placement_pts, ppr_bonus, off_bonus, podium_flag

            points_breakdown = processed.apply(calc_points, axis=1)
            processed['Total DEPotY Points'] = [x[0] for x in points_breakdown]
            processed['Placement Points'] = [x[1] for x in points_breakdown]
            processed['PPR Bonus'] = [x[2] for x in points_breakdown]
            processed['OFF% Bonus'] = [x[3] for x in points_breakdown]
            processed['Podiums'] = [x[4] for x in points_breakdown]
            
            # Store calculated results globally for Tab 2
            st.session_state['weekly_scores'] = processed[['Name Check', 'Total DEPotY Points']]
            st.session_state['target_week'] = str(int(week_num))
            
            # 5. Build Final Power BI Master Sheet Row Appendices
            processed['Location'] = location
            processed['Level'] = level
            processed['Event'] = event_type
            processed['Season'] = season
            processed['Month'] = week_code
            processed['Year'] = year_val
            processed['Month 2'] = month_2_val
            processed[''] = rolling_num
            processed['Rolling Year'] = f"{year_val} {rolling_num} {month_2_val}"
            
            master_columns = [
                'Display Name', 'First Name', 'Last Name', 'Email', 'PPR', 'DPR', 
                'OPP PPR', '4IN', '4IN %', 'IN', 'IN %', 'ON', 'ON %', 'OFF', 'OFF %', 
                'Rounds', 'Total Points', 'Opp Points', 'Game Name', 'Year', 'Month', 
                'Location', 'Event', 'Season', 'Level', 'Name Check', 'Podiums', 
                'Month 2', '', 'Rolling Year'
            ]
            for col in master_columns:
                if col not in processed.columns: processed[col] = ""
            
            pbi_output = processed[master_columns]
            
            st.success("🎉 Calculations and Cross-Referencing Complete!")
            
            # Render a summary table splits for quick checking
            st.subheader("Leaderboard Preview for this Week:")
            display_cols = ['Name Check', 'Is_Member', 'Bracket Place', 'Placement Points', 'PPR Bonus', 'OFF% Bonus', 'Total DEPotY Points']
            st.dataframe(processed[display_cols].sort_values(by='Total DEPotY Points', ascending=False))
            
            # Download link for Power BI data injection
            csv_pbi = pbi_output.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Power BI Upload File", data=csv_pbi, file_name=f"PBI_Upload_{week_code}_{location}.csv", mime="text/csv")

with tab2:
    st.header("Step 3: Update Year Standing Sheets")
    uploaded_master = st.file_uploader("Upload your Master Year Standing CSV (e.g., 2026 DEPotY.csv)", type=["csv"])
    
    if uploaded_master is not None:
        master_df = pd.read_csv(uploaded_master)
        master_df.columns = master_df.columns.str.strip()
        
        if 'weekly_scores' not in st.session_state:
            st.error("Go run Tab 1 processing calculations before doing ledger adjustments!")
        else:
            weekly_data = st.session_state['weekly_scores']
            target_week_num = st.session_state['target_week']
            
            # Identify the specific structural week column name in your tracker sheet
            matching_col = None
            for col in master_df.columns:
                if col == target_week_num or col.endswith(f"-{int(target_week_num):02d}") or f"Week {target_week_num}" in col:
                    matching_col = col
                    break
            
            if not matching_col:
                matching_col = target_week_num
                if matching_col not in master_df.columns:
                    master_df[matching_col] = 0
                    
            st.info(f"Targeting matrix alignment column: '{matching_col}'")
            
            if st.button("Apply Verified Scores directly to Seasonal Grid"):
                scores_dict = dict(zip(weekly_data['Name Check'], weekly_data['Total DEPotY Points']))
                
                # Determine the correct player name lookup key column index
                player_col_name = '2026 Players of the Year' if '2026 Players of the Year' in master_df.columns else (
                    '2024 Players of the Year' if '2024 Players of the Year' in master_df.columns else master_df.columns[1]
                )
                
                def apply_updates(row):
                    p_name = str(row[player_col_name]).strip()
                    if p_name in scores_dict:
                        return scores_dict[p_name]
                    return row[matching_col] if matching_col in row and pd.notna(row[matching_col]) else 0
                
                master_df[matching_col] = master_df.apply(apply_updates, axis=1)
                
                st.success("Standalone Ledger Updated Successfully!")
                st.dataframe(master_df.head(20))
                
                updated_master_csv = master_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Final Master Year Tracker", data=updated_master_csv, file_name="Updated_DEPotY_Standings.csv", mime="text/csv")