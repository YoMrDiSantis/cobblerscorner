import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="DE Cornhole Analytics Operating System", layout="wide")
st.title("🌽 Delaware Cornhole League OS & Narrative Suite")

# --- INITIALIZATION STATES ---
if 'processed_all_data' not in st.session_state:
    st.session_state['processed_all_data'] = None

# --- SIDEBAR: TIMEFRAME CONFIGURATION ---
st.sidebar.header("📆 Narrative Summary Scope")
timeframe_type = st.sidebar.radio(
    "Select Breakdown Scope",
    options=["Weekly", "Monthly", "Mid-Year (Jan - June)", "End of Year / Annual"]
)

# Mocked/Predefined standard operational bounds from historical records
target_year = st.sidebar.selectbox("Select Target Year", [2026, 2025, 2024, 2023])

selected_week = "W.22"
selected_months = ["June"]

if timeframe_type == "Weekly":
    # Let user input exact tracking week string formatting matching your Power BI structures
    week_int = st.sidebar.number_input("League Week Number", min_value=1, max_value=52, value=22)
    selected_week = f"W.{int(week_int):02d}"
    st.sidebar.caption(f"Filtering dataset specifically for row marker: `{selected_week}`")

elif timeframe_type == "Monthly":
    selected_months = st.sidebar.multiselect(
        "Select Target Month(s)",
        ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
        default=["June"]
    )

# --- CENTRAL STORAGE REFERENCE LOADING ---
st.header("🛡️ Reference Master Database Lists")
col_db1, col_db2 = st.columns(2)
with col_db1:
    uploaded_members = st.file_uploader("Upload Club / Valid Members Email List CSV", type=["csv"])
with col_db2:
    uploaded_master_data = st.file_uploader("Upload Historical Master Dataset (PPR Data CSV)", type=["csv"])

st.write("---")

# Helper keyword function 
def find_col_by_keyword(cols, keyword):
    for c in cols:
        if keyword.lower() in str(c).lower(): return c
    return None

# --- CORE CALCULATION PIPELINE ENGINE ---
if st.button("🚀 Process Historical Streams & Compile Scope Narrative"):
    if not uploaded_members:
        st.error("Please provide your Master Verified Members List before continuing.")
    elif not uploaded_master_data:
        st.error("Please load your primary Historical Record Sheet (e.g., PPR Data Master CSV) to analyze previous ranges.")
    else:
        # Load Baseline Configurations
        member_df = pd.read_csv(uploaded_members)
        member_df.columns = member_df.columns.str.strip()
        mem_email_col = find_col_by_keyword(member_df.columns, 'email') or member_df.columns[0]
        valid_member_emails = set(member_df[mem_email_col].dropna().astype(str).str.strip().str.lower().unique())

        # Load Master Analytics Sheet
        master_df = pd.read_csv(uploaded_master_data)
        master_df.columns = master_df.columns.str.strip()

        # Step 1: Apply Timeframe Slicing Logic Based on Selection
        # Establish base global year restriction filter matching standard format
        sliced_df = master_df[master_df['Year'].astype(str) == str(target_year)]
        
        scope_title_text = ""
        
        if timeframe_type == "Weekly":
            # Match layout format 'W.XX' in Month column metric row fields
            sliced_df = sliced_df[sliced_df['Month'].astype(str) == selected_week]
            scope_title_text = f"WEEK {selected_week.replace('W.', '')} ({target_year})"
            
        elif timeframe_type == "Monthly":
            # Match target strings inside structural column 'Month 2' (e.g. 'June')
            sliced_df = sliced_df[sliced_df['Month 2'].astype(str).isin(selected_months)]
            scope_title_text = f"MONTHLY RECAP ({', '.join(selected_months)} {target_year})"
            
        elif timeframe_type == "Mid-Year (Jan - June)":
            mid_year_months = ["January", "February", "March", "April", "May", "June"]
            sliced_df = sliced_df[sliced_df['Month 2'].astype(str).isin(mid_year_months)]
            scope_title_text = f"MID-YEAR REVIEW (Jan - June {target_year})"
            
        elif timeframe_type == "End of Year / Annual":
            # Retains the complete year dataset untouched
            scope_title_text = f"ANNUAL WRAP-UP & REVIEW ({target_year} FULL SEASON)"

        if sliced_df.empty:
            st.warning(f"No records matching the timeframe conditions found for {scope_title_text}. Double check columns 'Year', 'Month', or 'Month 2' inside your spreadsheet layout.")
        else:
            # Step 2: Ensure data parsing numbers are formatted cleanly for math metrics
            for num_col in ['PPR', 'OPP PPR', 'OFF %', 'Rounds']:
                if num_col in sliced_df.columns:
                    sliced_df[num_col] = pd.to_numeric(sliced_df[num_col], errors='coerce').fillna(0)

            # Map Membership Verification inline
            email_key = find_col_by_keyword(sliced_df.columns, 'email') or 'Email'
            sliced_df['Is_Member'] = sliced_df[email_key].astype(str).str.strip().str.lower().apply(lambda x: x in valid_member_emails)
            
            # Group rows to ensure stats consolidate players who played multiple tournaments across that duration
            # Weighted average formulas for calculations:
            player_stats = sliced_df.groupby('Name Check').agg(
                Total_Rounds=('Rounds', 'sum'),
                Avg_PPR=('PPR', 'mean'),
                Avg_Opp_PPR=('OPP PPR', 'mean'),