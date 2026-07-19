import pandas as pd

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

    east = (
        final[final["Division"] == "East"]
        .sort_values(["Points", "Wins"], ascending=False)
        .reset_index(drop=True)
    )

    west = (
        final[final["Division"] == "West"]
        .sort_values(["Points", "Wins"], ascending=False)
        .reset_index(drop=True)
    )

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
    # Games Back
    # -------------------------------------------------

    gb = {}

    for division in ["East", "West"]:

        div = standings[standings["Division"] == division]

        leader_wins = div["Wins"].max()

        leader_losses = (
            div.loc[
                div["Wins"] == leader_wins,
                "Losses"
            ].min()
        )

        for _, row in div.iterrows():

            gb[row["Team"]] = round(
                (
                    (leader_wins - row["Wins"])
                    + (row["Losses"] - leader_losses)
                ) / 2,
                1
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

        rows.append({

            "Team": team,
            "Division": stats["division"][team],
            "Status": status,

            "Record": record_str,

            "Elo": round(ratings[team], 0),

            "GB": gb[team],
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