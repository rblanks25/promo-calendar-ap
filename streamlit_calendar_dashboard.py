import streamlit as st
import pandas as pd
import calendar
import sqlite3
from datetime import datetime

DB_PATH = "data/promo_calendar.db"

# Load calendar data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM events", conn)
    conn.close()
    df['event_date'] = pd.to_datetime(df['event_date'])
    return df

# Streamlit App Layout
st.set_page_config(layout="wide")

# Global Style Override
st.markdown("""
<style>
body, html, .stApp {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
    -webkit-font-smoothing: antialiased !important;
    -moz-osx-font-smoothing: grayscale !important;
    font-size: 16px !important;
}
.floating-box {
    position: fixed;
    top: 80px;
    right: 30px;
    width: 320px;
    max-height: 85vh;
    overflow-y: auto;
    padding: 10px;
    background-color: #f7f7f7;
    border: 2px solid #ccc;
    border-radius: 12px;
    box-shadow: 2px 2px 8px rgba(0,0,0,0.2);
    font-size: 14px;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}
</style>
""", unsafe_allow_html=True)

st.title("📅 Live Monthly Promo Calendar")

df = load_data()
today = datetime.today()

col1, col2 = st.columns([1, 2])
with col1:
    year = st.selectbox("Year", range(2023, 2031), index=today.year - 2023)
    month = st.selectbox("Month", list(calendar.month_name)[1:], index=today.month - 1)
    selected_month = list(calendar.month_name).index(month)

    # Filters
    promo_options = ["All"] + sorted(df["promo_name"].dropna().unique())
    selected_promo = st.selectbox("Promo Filter", promo_options)
    if selected_promo != "All":
        df = df[df["promo_name"] == selected_promo]

    item_options = ["All"] + sorted(df["item_name"].dropna().unique())
    selected_item = st.selectbox("Item Filter", item_options)
    if selected_item != "All":
        df = df[df["item_name"] == selected_item]

    st.button("🔄 Refresh")

# Sidebar data (promo colors and item data grouped)
promo_colors = {}
color_palette = ["#FF9999", "#99CCFF", "#99FF99", "#FFCC99", "#CCCCFF", "#FFD700", "#FFB6C1", "#ADFF2F", "#FFA07A"]
sidebar_df = df[(df['event_date'].dt.month == selected_month) & (df['event_date'].dt.year == year)]
for i, promo in enumerate(sidebar_df['promo_name'].dropna().unique()):
    promo_colors[promo] = color_palette[i % len(color_palette)]

# Floating Sidebar Summary
with st.container():
    st.markdown("""
    <div class='floating-box'>
    <h4>📌 Promo Summary</h4>
    """, unsafe_allow_html=True)

    for promo, group in sidebar_df.groupby("promo_name"):
        color = promo_colors.get(promo, "#DDDDDD")
        st.markdown(f"<details><summary style='margin-bottom:6px'><b style='color:black'>{promo}</b></summary>", unsafe_allow_html=True)
        for _, row in group.iterrows():
            st.markdown(f"<div style='background-color:{color};padding:4px;border-radius:4px;margin-bottom:2px'>"
                        f"<b>{row['item_name']}</b> – {row['item_code']} – {row['quantity']}"
                        f"</div>", unsafe_allow_html=True)
        st.markdown("</details>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# Render calendar grid with interactive cells
def render_interactive_calendar(df, year, month):
    cal = calendar.Calendar(firstweekday=6)
    month_grid = cal.monthdatescalendar(year, month)

    for week in month_grid:
        cols = st.columns(7)
        for i, date in enumerate(week):
            in_month = date.month == month
            day_events = df[df['event_date'].dt.date == date]

            with cols[i]:
                st.markdown(f"### {' ' if not in_month else date.day}", help="Click to expand")

                if not day_events.empty:
                    visible = day_events['promo_name'].unique()[:2]
                    for promo in visible:
                        color = promo_colors.get(promo, "#DDDDDD")
                        st.markdown(f"<div style='background-color:{color};padding:4px;border-radius:4px;margin-bottom:2px'>"
                                    f"<b>{promo}</b>"
                                    f"</div>", unsafe_allow_html=True)

                    if len(day_events['promo_name'].unique()) > 2:
                        expand_key = f"expand_{date}"
                        if st.button(f"+{len(day_events['promo_name'].unique()) - 2} more", key=expand_key):
                            st.session_state["expanded_date"] = str(date)

                if "expanded_date" in st.session_state and st.session_state["expanded_date"] == str(date):
                    with st.expander(f"Events for {date.strftime('%B %d, %Y')}"):
                        for promo, group in day_events.groupby("promo_name"):
                            color = promo_colors.get(promo, "#DDDDDD")
                            st.markdown(f"<div style='background-color:{color};padding:4px;border-radius:4px;margin-bottom:2px'><b>{promo}</b></div>", unsafe_allow_html=True)
                            for _, row in group.iterrows():
                                st.markdown(f"  - {row['item_name']} – {row['item_code']} – {row['quantity']}")

with col2:
    render_interactive_calendar(df, year, selected_month)
