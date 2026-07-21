import stats
print(stats.__file__)

import pandas as pd
import random
import numpy as np

random.seed(42)
np.random.seed(42)

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
CUTOFF_DATE = "2026-07-20"


# =====================================================
# LOAD DATA
# =====================================================

standings = pd.read_csv("Data/standings.csv")
print("Columns:", standings.columns.tolist())
print(standings[["Team", "Wins", "Losses", "Ties"]].head())

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

# ---- DIAGNOSTIC: flag any rows that failed to parse a date ----
bad_dates = schedule[schedule["CleanDate"].isna()]
if len(bad_dates) > 0:
    print(f"\n⚠️  {len(bad_dates)} schedule row(s) failed date parsing "
          f"and will be silently excluded from the simulation:")
    print(bad_dates[["Date"]])
    print()
# -----------------------------------------------------------------


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
# TRACK AVERAGE ELO
# =====================================================

elo_total = {
    team: 0
    for team in standings["Team"]
}


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


    # Track Elo after simulated season
    for team in ratings:
        elo_total[team] += ratings[team]


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
# COMPUTE AVERAGE ELO
# =====================================================

average_elo = {
    team: round(
        elo_total[team] / N_SIMULATIONS,
        0
    )
    for team in elo_total
}


# =====================================================
# COMPUTE SOS
# =====================================================

sos = compute_sos(
    remaining_games,
    average_elo
)


# =====================================================
# BUILD RESULTS
# =====================================================

results = build_results(
    stats,
    N_SIMULATIONS,
    sos,
    standings,
    remaining_games,
    average_elo
)


# =====================================================
# OUTPUT
# =====================================================

print("\nPLAYOFF ODDS\n")
print(results)

print(results[["Team", "Record"]])


results.to_csv(
    "Outputs/playoff_odds.csv",
    index=False
)
# =====================================================
# SAVE HISTORICAL RESULTS
# =====================================================

from datetime import datetime

history = results[
    [
        "Team",
        "Playoff Odds",
        "Semis Odds",
        "Finals Odds",
        "Championship Odds",
        "Elo"
    ]
].copy()

history["Date"] = datetime.now().strftime("%Y-%m-%d")

today_str = history["Date"].iloc[0]

history_file = "Outputs/playoff_history.csv"

try:
    old_history = pd.read_csv(history_file)

    # Drop any existing row(s) for today's date so re-running the
    # simulation multiple times in one day overwrites today's point
    # instead of stacking duplicate dots on the chart
    old_history = old_history[old_history["Date"] != today_str]

    history = pd.concat(
        [old_history, history],
        ignore_index=True
    )

except FileNotFoundError:
    pass


history.to_csv(
    history_file,
    index=False
)