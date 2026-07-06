import pandas as pd

from simulator import simulate_season
from ratings import build_ratings
from stats import (
    initialize_stats,
    update_regular_season_stats,
    compute_sos,
    build_results
)
from playoffs import simulate_playoffs

# =====================================================
# SETTINGS
# =====================================================

N_SIMULATIONS = 1000
CUTOFF_DATE = "2026-07-05"

# =====================================================
# LOAD DATA
# =====================================================

standings = pd.read_csv("Data/standings.csv")
schedule = pd.read_csv("Data/schedule.csv")

# =====================================================
# CLEAN DATE
# =====================================================

schedule["CleanDate"] = (
    schedule["Date"]
    .astype(str)
    .str.extract(r"(\d{2}/\d{2}/\d{4})")[0]
)

schedule["CleanDate"] = pd.to_datetime(
    schedule["CleanDate"],
    format="%m/%d/%Y",
    errors="coerce"
)

# =====================================================
# SPLIT PLAYED VS REMAINING
# =====================================================

cutoff_date = pd.to_datetime(CUTOFF_DATE)

remaining_games = schedule[
    schedule["CleanDate"] > cutoff_date
]

print("Remaining games:", len(remaining_games))

if len(remaining_games) == 0:
    raise ValueError(
        "No remaining games found — check date parsing or cutoff date."
    )

# =====================================================
# INITIALIZE STATS
# =====================================================

stats = initialize_stats(standings)

# =====================================================
# MONTE CARLO LOOP
# =====================================================

for sim in range(N_SIMULATIONS):

    ratings = build_ratings(standings)

    final = simulate_season(
        standings,
        remaining_games,
        ratings
    )

    update_regular_season_stats(
        stats,
        final
    )

    stats = simulate_playoffs(
        final,
        ratings,
        stats
    )

# =====================================================
# COMPUTE SOS
# =====================================================

sos = compute_sos(
    remaining_games,
    ratings
)

# =====================================================
# BUILD RESULTS
# =====================================================

results = build_results(
    stats,
    N_SIMULATIONS,
    sos,
    standings,
    remaining_games
)

print("\nPLAYOFF ODDS\n")
print(results)

results.to_csv(
    "Outputs/playoff_odds.csv",
    index=False
)