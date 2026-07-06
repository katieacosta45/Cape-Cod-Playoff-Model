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

st.markdown(
    "**Created by Katie Acosta**  \n"
    "Monte Carlo playoff projections using 1,000 season simulations."
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
    df[col] = (
        df[col]
        .astype(float)
        .clip(upper=99.9)
    )


# Format Elo

if "Elo" in df.columns:
    df["Elo"] = (
        df["Elo"]
        .astype(float)
        .round(0)
        .astype(int)
    )


df["GB"] = (
    df["GB"]
    .astype(float)
    .round(1)
    .map(lambda x: "—" if x == 0 else f"{x:.1f}")
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
    "Elo",
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
# PLAYOFF CUT LINE + TABLE FORMATTING
# =====================================================

def add_cut_line(df):
    """
    Inserts a separator row after the playoff teams.
    """

    cut_row = pd.DataFrame([{
        "Team": "═ PLAYOFF CUT LINE ═",
        "Record": "",
        "Elo": "",
        "GB": "",
        "GR": "",
        "Playoff Odds": None,
        "Semis Odds": None,
        "Finals Odds": None,
        "Championship Odds": None
    }])

    return pd.concat(
        [df.iloc[:4], cut_row, df.iloc[4:]],
        ignore_index=True
    )


def highlight_rows(row):
    """
    Style playoff teams and cut line.
    """

    styles = [""] * len(row)

    if row["Team"] == "═ PLAYOFF CUT LINE ═":
        return [
            "background-color: black; color: white; font-weight:bold; text-align:center;"
        ] * len(row)


    if row.name < 4:
        styles[0] = (
            "background-color:#1b5e20;"
            "color:white;"
            "font-weight:bold;"
        )

    return styles



def format_table(df):

    df = add_cut_line(df)

    return (
        df.style
        .format({
            "Elo": "{}",
            "GB": "{}",
            "GR": "{}",
            "Playoff Odds": "{:.1f}%",
            "Semis Odds": "{:.1f}%",
            "Finals Odds": "{:.1f}%",
            "Championship Odds": "{:.1f}%"
        }, na_rep="")
        .background_gradient(
            subset=odds_cols,
            cmap="RdYlGn"
        )
        .apply(
            highlight_rows,
            axis=1
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

# =====================================================