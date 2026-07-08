import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime

# =====================================================
# PAGE SETTINGS
# =====================================================

st.set_page_config(
    page_title="Cape Cod League Playoff Simulator",
    page_icon="🏆",
    layout="wide"
)

# =====================================================
# TITLE + LAST UPDATED
# =====================================================

updated_date = datetime.now().strftime("%B %d, %Y")

st.title("🏆 Cape Cod League Playoff Simulator")

st.markdown(
    f"**Created by Katie Acosta**  \n"
    f"Monte Carlo playoff projections using 1,000 season simulations.  \n"
    f"**Last Updated: {updated_date}**"
)

st.divider()

# =====================================================
# TEAM COLORS
# =====================================================
# These are best-effort estimates, not scraped from an official source --
# capecodleague.com only exposes team logos as images (no CSS/text color
# values in the page), and there's no public verified brand-color database
# for CCBL teams. For exact hex codes: save a team's logo image and run it
# through a color picker tool (e.g. imagecolorpicker.com), then update below.

TEAM_COLORS = {
    "Bourne":          "#8B0000",
    "Brewster":        "#4FB8AF",
    "Chatham":         "#8B0000",
    "Cotuit":          "#B31942",
    "Falmouth":        "#002F6C",
    "Harwich":         "#D2691E",
    "Hyannis":         "#002868",
    "Orleans":         "#CC5500",
    "Wareham":         "#003087",
    "Yarmouth-Dennis": "#BA0C2F",
}


def color_team_names(val):
    """
    Colors the Team column text to match each franchise's color.
    Leaves non-team values (like the playoff cut line label) untouched
    so it doesn't clobber that row's existing black/white styling.
    """
    if val not in TEAM_COLORS:
        return ""
    return f"color: {TEAM_COLORS[val]}; font-weight: bold;"


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
        styles[0] = "font-weight:bold;"

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
        .map(
            color_team_names,
            subset=["Team"]
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
# PLAYOFF ODDS HISTORY
# =====================================================

st.divider()

st.subheader("📈 Playoff Odds Over Time")

history = pd.read_csv(
    "Outputs/playoff_history.csv"
)

# Drop early snapshot -- misleading this early in the season
history = history[history["Date"] != "2026-06-15"]

# Force proper chronological order regardless of string format
# (handles mixed date formats, e.g. "07/06/2026" vs "2026-07-07")
history["Date"] = pd.to_datetime(history["Date"], format="mixed")
history = history.sort_values("Date")

team_selected = st.multiselect(
    "Select Teams",
    history["Team"].unique(),
    default=list(history["Team"].unique())
)

filtered = history[history["Team"].isin(team_selected)]

# Only put tick marks on dates we actually have data for -- this stops a
# straight line drawn between, say, 6/29 and 7/6 from visually implying
# daily granularity that isn't there. Once daily updates are flowing,
# this will naturally show a tick per day.
actual_dates = sorted(filtered["Date"].unique())

chart = (
    alt.Chart(filtered)
    .mark_line(point=True)
    .encode(
        x=alt.X(
            "Date:T",
            axis=alt.Axis(values=actual_dates, format="%b %d", title="Date")
        ),
        y=alt.Y("Playoff Odds:Q", title="Playoff Odds (%)"),
        color=alt.Color(
            "Team:N",
            scale=alt.Scale(
                domain=list(TEAM_COLORS.keys()),
                range=list(TEAM_COLORS.values())
            ),
            legend=alt.Legend(title="Team")
        ),
        tooltip=["Team", "Date:T", "Playoff Odds"]
    )
    .properties(height=500)
)

st.altair_chart(chart, use_container_width=True)

st.caption(
    "Snapshots were taken weekly through July 6 — lines between those points "
    "are straight-line estimates, not daily data. Starting July 7, odds update daily."
)


# =====================================================
# PLAYOFF FORMAT EXPLANATION
# =====================================================

st.divider()

st.subheader("ℹ️ Playoff Format")

st.markdown(
    """
    The top four teams in each division qualify for the playoffs.

    All playoff rounds (Quarterfinals, Semifinals, and Championship Series) 
    are **best-of-three series**. The higher seed hosts **Games 1 and 3**, 
    while the lower seed hosts **Game 2**.

    Playoff projections are generated using Monte Carlo simulations based on 
    team Elo ratings, remaining regular season games, and playoff series outcomes.
    """
)