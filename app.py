import streamlit as st
import pandas as pd
from datetime import datetime

# =====================================================
# PAGE SETTINGS
# =====================================================

st.set_page_config(
    page_title="Cape Cod League Playoff Simulator",
    page_icon="🏆",
    layout="wide"
)

st.title("🏆 Cape Cod League Playoff Simulator")

st.caption(
    f"Updated: {datetime.now().strftime('%B %d, %Y')} | "
    "1,000 Monte Carlo Simulations"
)

st.divider()

# =====================================================
# LOAD DATA
# =====================================================

df = pd.read_csv("Outputs/playoff_odds.csv")

# =====================================================
# FORMAT NUMBERS (CLEAN DISPLAY)
# =====================================================

odds_cols = [
    "Playoff Odds",
    "Semis Odds",
    "Finals Odds",
    "Championship Odds"
]

for col in odds_cols:
    df[col] = df[col].astype(float)

df["GB"] = df["GB"].apply(
    lambda x: "—" if float(x) == 0 else round(float(x), 1)
)

# =====================================================
# SORT BY RECORD
# =====================================================

df["Wins"] = df["Record"].str.split("-").str[0].astype(int)
df["Losses"] = df["Record"].str.split("-").str[1].astype(int)

df = df.sort_values(
    ["Division", "Wins", "Losses"],
    ascending=[True, False, True]
)

df = df.drop(columns=["Wins", "Losses"])

# =====================================================
# SPLIT DIVISIONS
# =====================================================

cols = [
    "Team",
    "Record",
    "GB",
    "GR",
    "Playoff Odds",
    "Semis Odds",
    "Finals Odds",
    "Championship Odds"
]

east = df[df["Division"] == "East"][cols].copy()
west = df[df["Division"] == "West"][cols].copy()

# =====================================================
# FORMAT DISPLAY (3 DECIMALS + PERCENT LOOK)
# =====================================================

def format_table(d):

    return (
        d.style
        .format({
            "Playoff Odds": "{:.3f}",
            "Semis Odds": "{:.3f}",
            "Finals Odds": "{:.3f}",
            "Championship Odds": "{:.3f}"
        })
        .background_gradient(
            subset=odds_cols,
            cmap="RdYlGn"
        )
    )

# =====================================================
# EAST
# =====================================================

st.subheader("Eastern Division")

st.dataframe(
    format_table(east),
    hide_index=True,
    use_container_width=True
)

# =====================================================
# WEST
# =====================================================

st.subheader("Western Division")

st.dataframe(
    format_table(west),
    hide_index=True,
    use_container_width=True
)

# =====================================================
# CHAMPIONSHIP ODDS CHART
# =====================================================

st.subheader("🏆 Championship Odds")

chart = df.set_index("Team")["Championship Odds"].sort_values(ascending=False)

st.bar_chart(chart, use_container_width=True)