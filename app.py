import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
from stats import _sort_with_tiebreak

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


df["Points"] = df["Points"].astype(int)


# =====================================================
# SORT BY RECORD (points-based: win = 2, tie = 1)
# =====================================================
# Note: "Points" now comes directly from the simulation output (stats.py),
# so we don't recompute it here -- just pull Wins/Losses/Ties out of
# Record for the magic-number tiebreak logic further down.
#
# Sorting uses the same head-to-head tiebreak logic (TIEBREAK_WINNERS in
# stats.py) as the simulation itself, so the displayed order always
# matches what actually determined playoff qualification.

record_parts = df["Record"].str.split("-")
df["Wins"] = record_parts.str[0].astype(int)
df["Losses"] = record_parts.str[1].astype(int)
df["Ties"] = record_parts.apply(lambda parts: int(parts[2]) if len(parts) > 2 else 0)

df = pd.concat(
    [
        _sort_with_tiebreak(df[df["Division"] == "East"]),
        _sort_with_tiebreak(df[df["Division"] == "West"]),
    ],
    ignore_index=True
)


# =====================================================
# MAGIC NUMBER (CLINCH / ELIMINATION TRACKER)
# =====================================================
# For each team, finds the key rival at the 4-vs-5 cutoff line in their
# division and computes how many more POINTS are needed (win = 2, tie = 1,
# matching the league's standings system) so that even if that rival wins
# out the rest of their games, the team still finishes ahead. "Clinched" =
# already mathematically guaranteed a spot. Blank = can't catch the
# 4th-place team even by winning out.

def compute_magic_numbers(df):

    df = df.copy()
    df["Magic Number"] = None

    for division in df["Division"].unique():

        div = _sort_with_tiebreak(df[df["Division"] == division])

        if len(div) < 5:
            continue  # need a clean 5-team cutoff for this logic

        fourth = div.iloc[3]
        fifth = div.iloc[4]

        for i, row in div.iterrows():

            games_remaining = row["GR"]
            rival = fifth if i < 4 else fourth

            # Rival's best case: they win every remaining game (2 points each)
            rival_max_points = rival["Points"] + rival["GR"] * 2
            needed = rival_max_points - row["Points"] + 1

            # This team's best case: they also win every remaining game
            max_possible_gain = games_remaining * 2

            if needed <= 0:
                magic = "Clinched"
            elif needed > max_possible_gain:
                magic = ""
            else:
                magic = int(needed)

            df.loc[df["Team"] == row["Team"], "Magic Number"] = magic

    return df


df = compute_magic_numbers(df)

# Once a team has mathematically clinched, show a clean 100% instead of
# the 99.9% cap applied above (that cap exists to avoid implying false
# certainty from simulation variance -- but a clinched team IS certain).
df.loc[df["Magic Number"] == "Clinched", "Playoff Odds"] = 100.0

df = df.drop(columns=["Wins", "Losses", "Ties"])


# =====================================================
# SPLIT DIVISIONS
# =====================================================

cols = [
    "Team",
    "Record",
    "Elo",
    "Points",
    "GR",
    "Magic Number",
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
        "Points": "",
        "GR": "",
        "Magic Number": "",
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
            "Points": "{}",
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

# Opening Day marker: before any games are played, each team's naive
# playoff odds are simply 4 of 5 divisional spots = 80%. This isn't a
# simulation output, just a sensible fixed starting point for the chart.
opening_day = pd.DataFrame({
    "Team": history["Team"].unique(),
    "Playoff Odds": 80.0,
    "Date": "2026-06-13"
})

history = pd.concat([opening_day, history], ignore_index=True)

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
            axis=alt.Axis(
                values=actual_dates,
                format="%b %d",
                title="Date",
                labelAngle=-45,
                labelOverlap=False
            )
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
# CHAMPIONSHIP ODDS HISTORY
# =====================================================

st.divider()

st.subheader("🏆 Championship Odds Over Time")

# Reuse the same underlying history data (already loaded above), just
# start the window at 7/11 rather than opening day -- championship odds
# are noisy/uninformative far out from the playoffs, so there's no value
# in charting them from June.
champ_history = history[history["Date"] >= "2026-07-11"]

champ_filtered = champ_history[champ_history["Team"].isin(team_selected)]

champ_dates = sorted(champ_filtered["Date"].unique())

champ_chart = (
    alt.Chart(champ_filtered)
    .mark_line(point=True)
    .encode(
        x=alt.X(
            "Date:T",
            axis=alt.Axis(
                values=champ_dates,
                format="%b %d",
                title="Date",
                labelAngle=-45,
                labelOverlap=False
            )
        ),
        y=alt.Y("Championship Odds:Q", title="Championship Odds (%)"),
        color=alt.Color(
            "Team:N",
            scale=alt.Scale(
                domain=list(TEAM_COLORS.keys()),
                range=list(TEAM_COLORS.values())
            ),
            legend=alt.Legend(title="Team")
        ),
        tooltip=["Team", "Date:T", "Championship Odds"]
    )
    .properties(height=500)
)

st.altair_chart(champ_chart, use_container_width=True)

st.caption(
    "Championship odds become meaningful closer to the playoffs, so this chart "
    "starts July 11 rather than from opening day."
)


# =====================================================
# PLAYOFF BRACKET (manual entry -- updates as real games are played)
# =====================================================
# Seeds are pulled automatically from final standings (top 4 per division,
# by Points then Wins -- same sort already applied to `east`/`west` above).
# Results are entered manually as best-of-3 win counts and persisted to
# Outputs/bracket_results.csv so they survive app restarts.

st.divider()
st.subheader("🏆 Playoff Bracket")
st.caption("Enter each team's win count (0-2) as playoff games are played. Winners advance automatically.")

BRACKET_FILE = "Outputs/bracket_results.csv"

BRACKET_SERIES = [
    "east_qf1", "east_qf2", "west_qf1", "west_qf2",
    "east_semi", "west_semi", "championship"
]


def load_bracket():
    try:
        saved = pd.read_csv(BRACKET_FILE).set_index("series_id")
        return {
            sid: (int(saved.loc[sid, "team1_wins"]), int(saved.loc[sid, "team2_wins"]))
            for sid in BRACKET_SERIES
        }
    except (FileNotFoundError, KeyError):
        return {sid: (0, 0) for sid in BRACKET_SERIES}


def save_bracket(bracket):
    rows = [
        {"series_id": sid, "team1_wins": w[0], "team2_wins": w[1]}
        for sid, w in bracket.items()
    ]
    pd.DataFrame(rows).to_csv(BRACKET_FILE, index=False)


if "bracket" not in st.session_state:
    st.session_state.bracket = load_bracket()


def series_winner(series_id, team1, team2):
    if team1 is None or team2 is None:
        return None
    w1, w2 = st.session_state.bracket[series_id]
    if w1 == 2:
        return team1
    if w2 == 2:
        return team2
    return None


def update_series(series_id, key1, key2):
    st.session_state.bracket[series_id] = (
        st.session_state[key1],
        st.session_state[key2]
    )
    save_bracket(st.session_state.bracket)


def render_series(series_id, team1, team2, label):
    st.markdown(f"**{label}**")

    if team1 is None or team2 is None:
        st.caption("Waiting on earlier round(s)")
        return

    w1, w2 = st.session_state.bracket[series_id]
    key1, key2 = f"{series_id}_t1", f"{series_id}_t2"

    c1, c2 = st.columns(2)
    with c1:
        color = TEAM_COLORS.get(team1, "#ffffff")
        st.markdown(f"<span style='color:{color}; font-weight:bold;'>{team1}</span>", unsafe_allow_html=True)
        st.number_input(
            "Wins", min_value=0, max_value=2, value=w1, step=1,
            key=key1, on_change=update_series, args=(series_id, key1, key2),
            label_visibility="collapsed"
        )
    with c2:
        color = TEAM_COLORS.get(team2, "#ffffff")
        st.markdown(f"<span style='color:{color}; font-weight:bold;'>{team2}</span>", unsafe_allow_html=True)
        st.number_input(
            "Wins", min_value=0, max_value=2, value=w2, step=1,
            key=key2, on_change=update_series, args=(series_id, key1, key2),
            label_visibility="collapsed"
        )

    winner = series_winner(series_id, team1, team2)
    if winner:
        st.success(f"✅ {winner} advances")


east_seeds = east["Team"].tolist()[:4]
west_seeds = west["Team"].tolist()[:4]

qf_col1, qf_col2 = st.columns(2)
with qf_col1:
    st.markdown("#### East Quarterfinals")
    render_series("east_qf1", east_seeds[0], east_seeds[3], f"(1) {east_seeds[0]} vs (4) {east_seeds[3]}")
    render_series("east_qf2", east_seeds[1], east_seeds[2], f"(2) {east_seeds[1]} vs (3) {east_seeds[2]}")
with qf_col2:
    st.markdown("#### West Quarterfinals")
    render_series("west_qf1", west_seeds[0], west_seeds[3], f"(1) {west_seeds[0]} vs (4) {west_seeds[3]}")
    render_series("west_qf2", west_seeds[1], west_seeds[2], f"(2) {west_seeds[1]} vs (3) {west_seeds[2]}")

st.write("")

east_semi_t1 = series_winner("east_qf1", east_seeds[0], east_seeds[3])
east_semi_t2 = series_winner("east_qf2", east_seeds[1], east_seeds[2])
west_semi_t1 = series_winner("west_qf1", west_seeds[0], west_seeds[3])
west_semi_t2 = series_winner("west_qf2", west_seeds[1], west_seeds[2])

semi_col1, semi_col2 = st.columns(2)
with semi_col1:
    st.markdown("#### East Semifinal (Division Championship)")
    render_series("east_semi", east_semi_t1, east_semi_t2, f"{east_semi_t1 or 'TBD'} vs {east_semi_t2 or 'TBD'}")
with semi_col2:
    st.markdown("#### West Semifinal (Division Championship)")
    render_series("west_semi", west_semi_t1, west_semi_t2, f"{west_semi_t1 or 'TBD'} vs {west_semi_t2 or 'TBD'}")

st.write("")
st.markdown("#### 🏆 Championship Series")

east_champ = series_winner("east_semi", east_semi_t1, east_semi_t2)
west_champ = series_winner("west_semi", west_semi_t1, west_semi_t2)

render_series("championship", east_champ, west_champ, f"{east_champ or 'TBD'} vs {west_champ or 'TBD'}")

league_champ = series_winner("championship", east_champ, west_champ)
if league_champ:
    st.balloons()
    st.markdown(f"### 🎉 {league_champ} — 2026 League Champions!")


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