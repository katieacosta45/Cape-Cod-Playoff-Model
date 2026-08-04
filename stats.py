import pandas as pd

# =====================================================
# MANUAL HEAD-TO-HEAD TIEBREAKERS
# =====================================================
# When two teams are tied on Points, the league breaks the tie by
# head-to-head record. There's no per-game results log in this pipeline
# (schedule.csv only has dates, not outcomes) to compute this
# automatically, so ties are recorded manually here as they're confirmed.
# Add a new entry as {frozenset({"Team A", "Team B"}): "Team A"} meaning
# Team A wins the tiebreaker over Team B.

TIEBREAK_WINNERS = {
    frozenset({"Cotuit", "Wareham"}): "Cotuit",
}


def _tiebreak_score(team, division_df):
    """
    Counts how many head-to-head tiebreaker wins `team` has against
    other teams it's currently tied with on Points. Used as a sort
    tiebreaker so a manually-confirmed head-to-head result overrides
    the arbitrary order pandas would otherwise fall back on.
    """
    points = division_df.loc[division_df["Team"] == team, "Points"].iloc[0]
    tied_teams = division_df.loc[division_df["Points"] == points, "Team"].tolist()

    score = 0
    for other in tied_teams:
        if other == team:
            continue
        pair = frozenset({team, other})
        if TIEBREAK_WINNERS.get(pair) == team:
            score += 1

    return score


def _sort_with_tiebreak(division_df):
    division_df = division_df.copy()
    division_df["TiebreakScore"] = division_df["Team"].apply(
        lambda t: _tiebreak_score(t, division_df)
    )
    return (
        division_df
        .sort_values(["Points", "TiebreakScore", "Wins"], ascending=False)
        .drop(columns=["TiebreakScore"])
        .reset_index(drop=True)
    )


# =====================================================
# INITIALIZE STATS
# =====================================================

def initialize_stats(standings):
    """Creates dictionaries to track simulation results."""

    teams = standings["Team"]

    return {
        "playoffs": {team: 0 for team in teams},
        "semis": {team: 0 for team in teams},
        "finals": {team: 0 for team in teams},
        "titles": {team: 0 for team in teams},
        "wins": {team: 0 for team in teams},
        "points": {team: 0 for team in teams},
        "seed_total": {team: 0 for team in teams},
        "division": dict(zip(standings["Team"], standings["Division"]))
    }


# =====================================================
# UPDATE REGULAR SEASON STATS
# =====================================================

def update_regular_season_stats(stats, final):

    east = _sort_with_tiebreak(final[final["Division"] == "East"])
    west = _sort_with_tiebreak(final[final["Division"] == "West"])

    for conference in [east, west]:

        for i, row in conference.iterrows():

            team = row["Team"]

            stats["wins"][team] += row["Wins"]
            stats["points"][team] += row["Points"]
            stats["seed_total"][team] += i + 1

            if i < 4:
                stats["playoffs"][team] += 1


# =====================================================
# STRENGTH OF SCHEDULE
# =====================================================

def compute_sos(schedule, ratings):

    sos = {}

    teams = set(schedule["Home"]).union(set(schedule["Away"]))

    for team in teams:

        opponents = []

        games = schedule[
            (schedule["Home"] == team)
            | (schedule["Away"] == team)
        ]

        for _, game in games.iterrows():

            opponent = (
                game["Away"]
                if game["Home"] == team
                else game["Home"]
            )

            opponents.append(ratings[opponent])

        sos[team] = round(sum(opponents) / len(opponents), 1) if opponents else 0

    return sos


# =====================================================
# BUILD RESULTS
# =====================================================

CLINCHED = {
    "Yarmouth-Dennis"
}

ELIMINATED = set()

def build_results(stats, n_simulations, sos, standings, remaining_games, ratings):

    rows = []

    standings_lookup = standings.set_index("Team")

    # -------------------------------------------------
    # Games Remaining
    # -------------------------------------------------

    games_remaining = {}

    for team in standings["Team"]:

        games_remaining[team] = len(
            remaining_games[
                (remaining_games["Home"] == team)
                | (remaining_games["Away"] == team)
            ]
        )

    # -------------------------------------------------
    # Build Results
    # -------------------------------------------------

    for team in stats["wins"]:

        playoff = stats["playoffs"][team] / n_simulations
        semis = stats["semis"][team] / n_simulations
        finals = stats["finals"][team] / n_simulations
        titles = stats["titles"][team] / n_simulations

        playoff_pct = round(playoff * 100, 1)
        semis_pct = round(semis * 100, 1)
        finals_pct = round(finals * 100, 1)
        titles_pct = round(titles * 100, 1)

        # -------------------------------------------------
        # Manual clinch / elimination overrides
        # -------------------------------------------------

        if team in CLINCHED:
            playoff_pct = 100.0
            status = "✓ Clinched"

        elif team in ELIMINATED:
            playoff_pct = 0.0
            status = "✗ Eliminated"

        elif playoff_pct >= 100.0:
            status = "✓ Clinched"

        elif playoff_pct <= 0.0:
            status = "✗ Eliminated"

        else:
            status = ""

        record = standings_lookup.loc[team]

        wins = int(record["Wins"])
        losses = int(record["Losses"])
        ties = int(record["Ties"]) if "Ties" in standings.columns else 0

        record_str = f"{wins}-{losses}-{ties}"

        current_points = wins * 2 + ties

        rows.append({

            "Team": team,
            "Division": stats["division"][team],
            "Status": status,

            "Record": record_str,

            "Elo": round(ratings[team], 0),

            "Points": current_points,
            "GR": games_remaining[team],

            "Playoff Odds": playoff_pct,
            "Semis Odds": semis_pct,
            "Finals Odds": finals_pct,
            "Championship Odds": titles_pct,

            "Expected Wins": round(
                stats["wins"][team] / n_simulations,
                2
            ),

            "Expected Points": round(
                stats["points"][team] / n_simulations,
                2
            ),

            "Average Seed": round(
                stats["seed_total"][team] / n_simulations,
                2
            ),

            "SOS": sos.get(team, 0)

        })

    df = pd.DataFrame(rows)

    df["Division"] = pd.Categorical(
        df["Division"],
        categories=["East", "West"],
        ordered=True
    )

    df = df.sort_values(
        ["Division", "Championship Odds"],
        ascending=[True, False]
    ).reset_index(drop=True)

    return df