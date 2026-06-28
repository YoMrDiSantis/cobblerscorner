import streamlit as st
import pandas as pd
import numpy as np

# --- SYSTEM WIDE CONFIGURATION ---
st.set_page_config(
    page_title="Delaware Cornhole League OS Master", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CENTRAL SIDEBAR NAVIGATION ---
st.sidebar.image("https://via.placeholder.com/150x50.png?text=DE+Cornhole", use_container_width=True) # Optional placeholder logo link
st.sidebar.title("🎮 Operating System Menu")
app_mode = st.sidebar.selectbox(
    "Choose Active Workspace Module:",
    ["📊 Preset Timeframe Stats Generator", "⚙️ League OS Core Operations"]
)

st.sidebar.write("---")

# --- UTILITY PIPELINE HELPER FUNCTIONS ---
def find_col_by_keyword(cols, keyword):
    """Safely locates columns by checking for text keywords to handle slight header variances."""
    for c in cols:
        if keyword.lower() in str(c).lower(): 
            return c
    return None


# ==============================================================================
# MODULE 1: PRESET TIMEFRAME STATS GENERATOR (OPTION 1)
# ==============================================================================
if app_mode == "📊 Preset Timeframe Stats Generator":
    st.title("🎛️ Dynamic Preset Timeframe Analytics Suite")
    st.write("Slices historical data frameworks down to specialized preset time horizons to auto-generate community narratives.")
    
    st.sidebar.header("📅 Timeframe Target Scope")
    timeframe_type = st.sidebar.radio(
        "Select Breakdown Scope",
        options=["Weekly", "Monthly", "Mid-Year (Jan - June)", "End of Year / Annual"],
        index=0
    )

    # Operational Target Year matching column 'Year'
    target_year = st.sidebar.selectbox("Select Target Year", [2026, 2025, 2024, 2023], index=0)

    # Context-dependent preset controls matching master file column constraints
    if timeframe_type == "Weekly":
        week_number = st.sidebar.number_input("League Week Number", min_value=1, max_value=52, value=22)
        selected_week_code = f"W.{int(week_number):02d}"
        min_rounds_cutoff = st.sidebar.number_input("Minimum Rounds to Qualify", min_value=1, max_value=30, value=8)
        st.sidebar.caption(f"Targeting: `Year` == {target_year} and `Month` == '{selected_week_code}'")

    elif timeframe_type == "Monthly":
        selected_months = st.sidebar.multiselect(
            "Select Target Month(s)",
            ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
            default=["June"]
        )
        min_rounds_cutoff = st.sidebar.number_input("Minimum Rounds to Qualify", min_value=5, max_value=150, value=30)
        st.sidebar.caption(f"Targeting: `Year` == {target_year} and `Month 2` rows")

    elif timeframe_type == "Mid-Year (Jan - June)":
        mid_year_months = ["January", "February", "March", "April", "May", "June"]
        min_rounds_cutoff = st.sidebar.number_input("Minimum Rounds to Qualify", min_value=20, max_value=500, value=100)
        st.sidebar.caption(f"Targeting: Jan-Jun windows for {target_year}")

    elif timeframe_type == "End of Year / Annual":
        min_rounds_cutoff = st.sidebar.number_input("Minimum Rounds to Qualify", min_value=50, max_value=1500, value=250)
        st.sidebar.caption(f"Evaluating complete season dataset records for {target_year}")

    # Central file input streams
    st.header("📥 Central Database References")
    col_upload1, col_upload2 = st.columns(2)
    with col_upload1:
        uploaded_master_data = st.file_uploader("Upload Historical Master Dataset (PPR Data CSV)", type=["csv"], key="preset_master")
    with col_upload2:
        uploaded_members = st.file_uploader("Upload Club / Valid Members Email List CSV", type=["csv"], key="preset_members")

    st.write("---")

    # Processing Loop
    if st.button("🚀 Process Historical Streams & Compile Scope Narrative"):
        if not uploaded_master_data or not uploaded_members:
            st.error("Missing Files! Please supply both your Master Historical PPR Data file and your Valid Members Email List to proceed.")
        else:
            master_df = pd.read_csv(uploaded_master_data)
            master_df.columns = master_df.columns.str.strip()
            
            member_df = pd.read_csv(uploaded_members)
            member_df.columns = member_df.columns.str.strip()

            mem_email_col = find_col_by_keyword(member_df.columns, 'email') or member_df.columns[0]
            valid_member_emails = set(member_df[mem_email_col].dropna().astype(str).str.strip().str.lower().unique())

            master_email_col = find_col_by_keyword(master_df.columns, 'email') or 'Email'
            master_df['Is_Member'] = master_df[master_email_col].fillna('').astype(str).str.strip().str.lower().apply(lambda x: x in valid_member_emails)

            master_df['Year_Str'] = master_df['Year'].astype(str)
            year_filtered = master_df[master_df['Year_Str'] == str(target_year)]
            
            context_label = ""
            if timeframe_type == "Weekly":
                sliced_df = year_filtered[year_filtered['Month'].astype(str) == selected_week_code]
                context_label = f"Week {week_number} ({target_year})"
            elif timeframe_type == "Monthly":
                sliced_df = year_filtered[year_filtered['Month 2'].astype(str).isin(selected_months)]
                context_label = f"the Month of {', '.join(selected_months)} {target_year}"
            elif timeframe_type == "Mid-Year (Jan - June)":
                sliced_df = year_filtered[year_filtered['Month 2'].astype(str).isin(mid_year_months)]
                context_label = f"the Mid-Year {target_year} Stretch (Jan - June)"
            else:
                sliced_df = year_filtered
                context_label = f"the Complete {target_year} Annual Campaign"

            if sliced_df.empty:
                st.warning(f"No records matching timeframe conditions found for {context_label}.")
            else:
                for num_col in ['PPR', 'OPP PPR', 'OFF %', 'Rounds', 'Podiums']:
                    if num_col in sliced_df.columns:
                        sliced_df[num_col] = pd.to_numeric(sliced_df[num_col], errors='coerce').fillna(0)

                player_stats = sliced_df.groupby(['Name Check', 'Is_Member']).agg(
                    Total_Rounds=('Rounds', 'sum'),
                    Total_Podiums=('Podiums', 'sum'),
                    Avg_PPR=('PPR', 'mean'),
                    Avg_Opp_PPR=('OPP PPR', 'mean'),
                    Avg_Off_Pct=('OFF %', 'mean')
                ).reset_index()

                club_rankings = player_stats[player_stats['Is_Member'] == True]
                qualified_leaders = club_rankings[club_rankings['Total_Rounds'] >= min_rounds_cutoff]

                # Draft Narrative Generation Layout Block
                narrative = f"## 📰 DELAWARE CORNHOLE OFFICIAL LEADERSHIP RECAP\n"
                narrative += f"**Timeframe Scope:** *{context_label}*\n"
                narrative += f"**Qualification Threshold:** *Minimum of {int(min_rounds_cutoff)} total rounds logged.*\n\n"
                narrative += f"The data entries have been pulled and calculated! Across this target tracking window, our players ground out intense frames on the boards. Let's look at who set the pace on our player matrix:\n\n"

                if not qualified_leaders.empty:
                    top_ppr_player = qualified_leaders.sort_values(by='Avg_PPR', ascending=False).iloc[0]
                    narrative += f"🔥 **THE BOARD CRUSHER (Highest Average PPR):** Consistency was unmatched for **{top_ppr_player['Name Check']}**. Fighting through heavy tournament lineups over {int(top_ppr_player['Total_Rounds'])} rounds, they anchored the fields with an amazing **{top_ppr_player['Avg_PPR']:.2f} PPR** average!\n\n"
                else:
                    narrative += "🔥 **THE BOARD CRUSHER:** *No players cleared the round minimum requirement to qualify across this timeframe block.*\n\n"

                if not qualified_leaders.empty:
                    top_def_player = qualified_leaders.sort_values(by='Avg_Opp_PPR', ascending=True).iloc[0]
                    narrative += f"🔒 **DEFENSIVE LOCKDOWN ARTIST:** Taking home titles requires playing clinical lane defense. **{top_def_player['Name Check']}** successfully silenced opposing brackets, suppressing opponents to a stingy **{top_def_player['Avg_Opp_PPR']:.2f} PPR** average against them!\n\n"

                if not qualified_leaders.empty:
                    top_sniper = qualified_leaders.sort_values(by='Avg_Off_Pct', ascending=True).iloc[0]
                    narrative += f"🎯 **THE CANVAS SNIPER (Precision Throwing):** Dropping a bag short onto the concrete wasn't an option for **{top_sniper['Name Check']}**. They minimized structural unforced errors, tracking an elite, low **{top_sniper['Avg_Off_Pct']:.1f}% OFF-the-board mark**!\n\n"

                if not club_rankings.empty and club_rankings['Total_Podiums'].sum() > 0:
                    top_podium_player = club_rankings.sort_values(by='Total_Podiums', ascending=False).iloc[0]
                    narrative += f"🏆 **PODIUM STREAK MASTER:** When tournament fields thinned out to money matches, **{top_podium_player['Name Check']}** practically owned the stage. They secured a grand total of **{int(top_podium_player['Total_Podiums'])} podium finishes** during this phase!\n\n"

                narrative += f"*Incredible work by all of our Delaware Cornhole verified club athletes. Keep dialing in those performance statistics and we'll see you out inside the circles next frame!* 🌽🕳"

                st.success(f"Calculations compiled successfully for {context_label}!")
                st.subheader("📋 Copy-Paste Ready Text Output")
                st.markdown(narrative)
                
                st.write("---")
                st.subheader("📊 Performance Evaluation Context Table")
                st.dataframe(
                    club_rankings.sort_values(by='Avg_PPR', ascending=False).rename(
                        columns={
                            'Name Check': 'Player Name', 'Total_Rounds': 'Rounds Logged',
                            'Avg_PPR': 'Points Per Round (PPR)', 'Avg_Opp_PPR': 'Opponent PPR',
                            'Avg_Off_Pct': 'Off-Board %', 'Total_Podiums': 'Podiums'
                        }
                    ),
                    use_container_width=True
                )


# ==============================================================================
# MODULE 2: LEAGUE OS CORE OPERATIONS
# ==============================================================================
elif app_mode == "⚙️ League OS Core Operations":
    st.title("⚙️ League OS Operating Hub & Data Router")
    st.write("Manage tournament structure mapping, email validation cross-checking, and overall system parameters.")

    # Core System Controls Placeholder Layout
    st.sidebar.header("🔧 System Controls")
    op_mode = st.sidebar.selectbox("Active Operational Pipeline", ["Data Ingestion Matrix", "Roster Synchronization", "Venue & Location Map"])

    if op_mode == "Data Ingestion Matrix":
        st.subheader("📥 Operational File Router")
        st.info("Upload day-of bracket files or ScoreMagic arrays here to parse updates across the system records.")
        
        col_os1, col_os2 = st.columns(2)
        with col_os1:
            raw_bracket = st.file_uploader("Upload ScoreMagic / Bracket Export CSV", type=["csv"], key="os_bracket")
        with col_os2:
            raw_roster = st.file_uploader("Upload Event Player Roster CSV", type=["csv"], key="os_roster")
            
        if st.button("⚡ Run System Integrity Check"):
            if raw_bracket:
                test_df = pd.read_csv(raw_bracket)
                st.success(f"File connection healthy! Identified {len(test_df)} raw records ready for relational mapping.")
            else:
                st.warning("Please upload a file stream above to evaluate the validation routines.")

    elif op_mode == "Roster Synchronization":
        st.subheader("👥 Member Database Sync Station")
        st.write("Cross-reference your primary master directory parameters down to active active season fields.")
        st.caption("Active Configuration Module: Connected to Central Cloud Array")

    elif op_mode == "Venue & Location Map":
        st.subheader("📍 Venue Network Mapping")
        st.write("Configure tournament operational venues and associate localized geographical metadata filters here.")