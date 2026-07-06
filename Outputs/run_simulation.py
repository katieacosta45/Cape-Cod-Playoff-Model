import pandas as pd
import random

# =====================================================
# SETTINGS
# =====================================================

N_SIMULATIONS = 10000
CUTOFF_DATE = pd.Timestamp("2026-07-01")

# =====================================================
# LOAD DATA
# =====================================================

standings = pd.read_csv("Data/standings.csv")
schedule = pd.read_csv("Data/schedule.csv")

# =====================================================
# PARSE DATES
# =====================================================

# Extract the MM/DD/YYYY portion from:
# "Sat 06/13/2026 (4:30 p.m.)"

schedule["CleanDate"] = (
    schedule["Date"]
    .astype(str)
    .str.extract(r"(\d{2}/\d{2}/\d{4})")[0]
)

schedule["CleanDate"] = pd.to_datetime(
    schedule["CleanDate"],
    format="%m/%d/%Y"
)

# =====================================================
# KEEP ONLY REMAINING GAMES
# =====================================================

remaining_games = schedule[schedule["CleanDate"] > CUTOFF_DATE].copy()

print(f"Played games: {len(schedule) - len(remaining_games)}")
print(f"Remaining games: {len(remaining_games)}")

# =====================================================
# GAME SIMULATOR
# =====================================================

def simulate_game(home, away):
    """
    Currently every game is 54/46.
    Later we'll replace this with team ratings.
    """

    HOME_WIN_PROB = 0.54

    if random.random() < HOME_WIN_PROB:
        return "HOME"
    else:
        return "AWAY"

# =====================================================
# SIMULATE ONE SEASON
# =====================================================

def simulate_season(base_standings):

    sim = base_standings.copy()

    for _, game in remaining_games.iterrows():

        result = simulate_game(game["Home"], game["Away"])

        home = game["Home"]
        away = game["Away"]

        if result == "HOME":

            sim.loc[sim.Team == home, "Wins"] += 1
            sim.loc[sim.Team == away, "Losses"] += 1

        else:

            sim.loc[sim.Team == away, "Wins"] += 1
            sim.loc[sim.Team == home, "Losses"] += 1

    sim["Points"] = sim["Wins"] * 2 + sim["Ties"]

    return sim

# =====================================================
# MONTE CARLO
# =====================================================

playoff_counts = {
    team: 0
    for team in standings["Team"]
}

print("\nRunning Monte Carlo...\n")

for sim_num in range(N_SIMULATIONS):

    final = simulate_season(standings)

    east = (
        final[final["Division"] == "East"]
        .sort_values(
            ["Points", "Wins"],
            ascending=False
        )
        .head(4)
    )

    west = (
        final[final["Division"] == "West"]
        .sort_values(
            ["Points", "Wins"],
            ascending=False
        )
        .head(4)
    )

    playoff_teams = list(east["Team"]) + list(west["Team"])

    for team in playoff_teams:
        playoff_counts[team] += 1

# =====================================================
# RESULTS
# =====================================================

results = pd.DataFrame({
    "Team": playoff_counts.keys(),
    "Playoff Odds": [
        playoff_counts[t] / N_SIMULATIONS
        for t in playoff_counts
    ]
})

results = results.sort_values(
    "Playoff Odds",
    ascending=False
)

results["Playoff Odds"] = (
    results["Playoff Odds"] * 100
).round(1)

print("\n===========================")
print("PLAYOFF ODDS")
print("===========================\n")

print(results)

results.to_csv(
    "Outputs/playoff_odds.csv",
    index=False
)

print("\nSaved to Outputs/playoff_odds.csv")