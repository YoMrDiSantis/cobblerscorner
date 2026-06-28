import streamlit as st
import pandas as pd
import numpy as np

# Set up page configurations
st.set_page_config(
    page_title="Delaware Cornhole Analytics Operating System", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🌽 Delaware Cornhole League OS & Narrative Suite")
st.write("Upload your data, choose your specific operational scope, and let the engine aggregate stats and draft community content.")

# --- SIDEBAR CONFIGURATION (OPTION 1 PRESET SCOPES) ---
st.sidebar.header("🎛️ Scope Configurator")

timeframe_type = st.sidebar.radio(
    "Select Breakdown Scope",
    options=["Weekly", "Monthly", "Mid-Year (Jan - June)", "End of Year / Annual"],
    index=0
)

# Base Operational Year (Maps directly to 'Year' column in PPR Data)
target_year = st.sidebar.selectbox("Select Target Year", [2026, 2025, 2024, 2023], index=0)

# Context-dependent dynamic parameters
if timeframe_type == "Weekly":
    # Captures inputs targeting column 'Month' containing codes like 'W.22'
    week_number = st.sidebar.number_input("League Week Number", min_value=1, max_value=52, value=22)
    selected_week_code = f"W.{int(week_number):02d}"
    
    # Establish a dynamic lower threshold for a single tournament window 
    min_rounds_cutoff = st.sidebar.number_input("Minimum Rounds to Qualify", min_value=1, max_value=30, value=8)
    st.sidebar.caption(f"Slicing rows where `Year` == {target_year} and `Month` == '{selected_week_code}'")

elif timeframe_type == "Monthly":
    # Captures target metrics inside column 'Month 2' containing full text names (e.g., 'June')
    selected_months = st.sidebar.multiselect(
        "Select Target Month(s)",
        ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
        default=["June"]
    )
    
    # Mid-tier round threshold for a complete monthly aggregate
    min_rounds_cutoff = st.sidebar.number_input("Minimum Rounds to Qualify", min_value=5, max_value=150, value=30)
    st.sidebar.caption(f"Slicing rows where `Year` == {target_year} and `Month 2` matches selection")

elif timeframe_type == "Mid-Year (Jan - June)":
    # Automatic calendar slicing bounds
    mid_year_months = ["January", "February", "March", "April", "May", "June"]
    
    # High threshold targeting long-term season consistency
    min_rounds_cutoff = st.sidebar.number_input("Minimum Rounds to Qualify", min_value=20, max_value=500, value=100)
    st.sidebar.caption(f"Slicing rows where `Year` == {target_year} and `Month 2` is between Jan-Jun")

elif timeframe_type == "End of Year / Annual":
    # Full seasonal evaluation bounds
    min_rounds_cutoff = st.sidebar.number_input("Minimum Rounds to Qualify", min_value=50, max_value=1500, value=250)
    st.sidebar.caption(f"Evaluating ALL records logged for the entire {target_year} operational season")


# --- DATA UPLOAD CHANNELS ---
st.header("📥 Central Database References")
col_upload1, col_upload2 = st.columns(2)

with col_upload1:
    uploaded_master_data = st.file_uploader("Upload Historical Master Dataset (PPR Data CSV)", type=["csv"])
with col_upload2:
    uploaded_members = st.file_uploader("Upload Club / Valid Members Email List CSV", type=["csv"])

st.write("---")


# --- CORE PIPELINE HELPER FUNCTIONS ---
def find_col_by_keyword(cols, keyword):
    """Safely locates columns by checking for text keywords to handle slight header variances."""
    for c in cols:
        if keyword.lower() in str(c).lower(): 
            return c
    return None


# --- COMPUTATION AND RENDERING EXECUTION ---
if st.button("🚀 Process Historical Streams & Compile Scope Narrative"):
    if not uploaded_master_data or not uploaded_members:
        st.error("Missing Files! Please supply both your Master Historical PPR Data file and your Valid Members Email List to proceed.")
    else:
        # Load baseline references cleanly
        master_df = pd.read_csv(uploaded_master_data)
        master_df.columns = master_df.columns.str.strip()
        
        member_df = pd.read_csv(uploaded_members)
        member_df.columns = member_df.columns.str.strip()

        # Step 1: Map and verify official registered email sets
        mem_email_col = find_col_by_keyword(member_df.columns, 'email') or member_df.columns[0]
        valid_member_emails = set(member_df[mem_email_col].dropna().astype(str).str.strip().str.lower().unique())

        master_email_col = find_col_by_keyword(master_df.columns, 'email') or 'Email'
        master_df['Is_Member'] = master_df[master_email_col].fillna('').astype(str).str.strip().str.lower().apply(lambda x: x in valid_member_emails)

        # Step 2: Slice primary DataFrame records according to our chosen Option 1 logic
        master_df['Year_Str'] = master_df['Year'].astype(str)
        year_filtered = master_df[master_df['Year_Str'] == str(target_year)]
        
        context_label = ""
        
        if timeframe_type == "Weekly":
            # Target row codes like 'W.22' inside the 'Month' field
            sliced_df = year_filtered[year_filtered['Month'].astype(str) == selected_week_code]
            context_label = f"Week {week_number} ({target_year})"
            
        elif timeframe_type == "Monthly":
            # Target raw names like 'June' inside the 'Month 2' field
            sliced_df = year_filtered[year_filtered['Month 2'].astype(str).isin(selected_months)]
            context_label = f"the Month of {', '.join(selected_months)} {target_year}"
            
        elif timeframe_type == "Mid-Year (Jan - June)":
            sliced_df = year_filtered[year_filtered['Month 2'].astype(str).isin(mid_year_months)]
            context_label = f"the Mid-Year {target_year} Stretch (Jan - June)"
            
        else: # End of Year / Annual
            sliced_df = year_filtered
            context_label = f"the Complete {target_year} Annual Campaign"

        # Check for matching structural records before invoking mathematical operations
        if sliced_df.empty:
            st.warning(f"No records matching the timeframe conditions found for {context_label}. Ensure column parameters and years match data rows.")
        else:
            # Clean and parse string numbers to float types to prevent analytical errors
            for num_col in ['PPR', 'OPP PPR', 'OFF %', 'Rounds', 'Podiums']:
                if num_col in sliced_df.columns:
                    sliced_df[num_col] = pd.to_numeric(sliced_df[num_col], errors='coerce').fillna(0)

            # Step 3: Group entries to consolidate performance metrics over the scope duration
            player_stats = sliced_df.groupby(['Name Check', 'Is_Member']).agg(
                Total_Rounds=('Rounds', 'sum'),
                Total_Podiums=('Podiums', 'sum'),
                Avg_PPR=('PPR', 'mean'),
                Avg_Opp_PPR=('OPP PPR', 'mean'),
                Avg_Off_Pct=('OFF %', 'mean')
            ).reset_index()

            # Filter metrics down explicitly to our valid club members
            club_rankings = player_stats[player_stats['Is_Member'] == True]
            qualified_leaders = club_rankings[club_rankings['Total_Rounds'] >= min_rounds_cutoff]

            # Step 4: Build automated Social/Newsletter copy narrative
            narrative = f"## 📰 DELAWARE CORNHOLE OFFICIAL LEADERSHIP RECAP\n"
            narrative += f"**Timeframe Scope:** *{context_label}*\n"
            narrative += f"**Qualification Threshold:** *Minimum of {int(min_rounds_cutoff)} total rounds logged.*\n\n"
            narrative += f"The data entries have been pulled and calculated! Across this target tracking window, our players ground out intense frames on the boards. Let's look at who set the pace on our player matrix:\n\n"

            # 🥇 Leader 1: PPR King
            if not qualified_leaders.empty:
                top_ppr_player = qualified_leaders.sort_values(by='Avg_PPR', ascending=False).iloc[0]
                narrative += f"🔥 **THE BOARD CRUSHER (Highest Average PPR):** Consistency was unmatched for **{top_ppr_player['Name Check']}**. Fighting through heavy tournament lineups over {int(top_ppr_player['Total_Rounds'])} rounds, they anchored the fields with an amazing **{top_ppr_player['Avg_PPR']:.2f} PPR** average!\n\n"
            else:
                narrative += "🔥 **THE BOARD CRUSHER:** *No players cleared the round minimum requirement to qualify across this timeframe block.*\n\n"

            # 🥈 Leader 2: Defensive Lockdown Artist
            if not qualified_leaders.empty:
                top_def_player = qualified_leaders.sort_values(by='Avg_Opp_PPR', ascending=True).iloc[0]
                narrative += f"🔒 **DEFENSIVE LOCKDOWN ARTIST:** Taking home titles requires playing clinical lane defense. **{top_def_player['Name Check']}** successfully silenced opposing brackets, suppressing opponents to a stingy **{top_def_player['Avg_Opp_PPR']:.2f} PPR** average against them!\n\n"

            # 🥉 Leader 3: Canvas Sniper
            if not qualified_leaders.empty:
                top_sniper = qualified_leaders.sort_values(by='Avg_Off_Pct', ascending=True).iloc[0]
                narrative += f"🎯 **THE CANVAS SNIPER (Precision Throwing):** Dropping a bag short onto the concrete wasn't an option for **{top_sniper['Name Check']}**. They minimized structural unforced errors, tracking an elite, low **{top_sniper['Avg_Off_Pct']:.1f}% OFF-the-board mark**!\n\n"

            # 🏅 Leader 4: Podium Streak Master
            if not club_rankings.empty and club_rankings['Total_Podiums'].sum() > 0:
                top_podium_player = club_rankings.sort_values(by='Total_Podiums', ascending=False).iloc[0]
                narrative += f"🏆 **PODIUM STREAK MASTER:** When tournament fields thinned out to money matches, **{top_podium_player['Name Check']}** practically owned the stage. They secured a grand total of **{int(top_podium_player['Total_Podiums'])} podium finishes** during this phase!\n\n"

            narrative += f"*Incredible work by all of our Delaware Cornhole verified club athletes. Keep dialing in those performance statistics and we'll see you out inside the circles next frame!* 🌽🕳"

            # Render calculations onto layout
            st.success(f"Calculations compiled successfully for {context_label}!")
            
            st.subheader("📋 Copy-Paste Ready Text Output")
            st.info("You can copy the generated markdown copy below for Facebook, email distributions, or newsletters:")
            st.markdown(narrative)
            
            st.write("---")
            st.subheader("📊 Performance Evaluation Context Table")
            st.dataframe(
                club_rankings.sort_values(by='Avg_PPR', ascending=False).rename(
                    columns={
                        'Name Check': 'Player Name',
                        'Total_Rounds': 'Rounds Logged',
                        'Avg_PPR': 'Points Per Round (PPR)',
                        'Avg_Opp_PPR': 'Opponent PPR',
                        'Avg_Off_Pct': 'Off-Board %',
                        'Total_Podiums': 'Podiums'
                    }
                ),
                use_container_width=True
            )