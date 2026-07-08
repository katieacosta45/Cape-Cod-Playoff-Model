"""
build_playoff_history.py

Runs the Monte Carlo playoff simulation once for EACH historical standings
snapshot (6/15, 6/22, 6/29, 7/6) and rebuilds Outputs/playoff_history.csv
from scratch, so the "Playoff Odds Over Time" chart in app.py has real
trend data instead of a single point.

WHERE TO PUT THIS FILE:
    Same folder as your existing run_simulation.py, so the imports below
    (simulator, ratings, stats, playoffs) resolve the same way they do there.

WHERE TO PUT THE 4 CSVs:
    Data/historical/standings_2026-06-15.csv
    Data/historical/standings_2026-06-22.csv
    Data/historical/standings_2026-06-29.csv
    Data/historical/standings_2026-07-06.csv
    (adjust SNAPSHOTS below if you name/place them differently)

WHAT IT ASSUMES:
    - Data/schedule.csv is the FULL season schedule and doesn't change
      across snapshots (only which games are "remaining" changes, based
      on cutoff date).
    - Each historical standings CSV has the same columns your main
      Data/standings.csv uses (Team, Division, Wins, Losses, Ties, ...).

Run it with:  python build_playoff_history.py
"""

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

# (label shown on chart x-axis, cutoff date for "remaining games", standings csv)
# cutoff_date is the day BEFORE the snapshot date, so games played ON the
# snapshot date are already baked into that day's win-loss record and are
# NOT re-simulated. This mirrors how CUTOFF_DATE = "2026-07-05" was used
# for the 7/6 standings in your original run_simulation.py.
SNAPSHOTS = [
    ("2026-06-15", "2026-06-14", "Data/historical/standings_2026-06-15.csv"),
    ("2026-06-22", "2026-06-21", "Data/historical/standings_2026-06-22.csv"),
    ("2026-06-29", "2026-06-28", "Data/historical/standings_2026-06-29.csv"),
    ("2026-07-06", "2026-07-05", "Data/historical/standings_2026-07-06.csv"),
]

# The historical standings CSVs use shorthand team names in a few cases
# (e.g. "Y-D") while schedule.csv / the ratings dict use full names
# (e.g. "Yarmouth-Dennis"). Map any mismatches here so lookups don't
# KeyError. Add more entries if other teams hit the same issue.
TEAM_NAME_MAP = {
    "Y-D": "Yarmouth-Dennis",
}


# =====================================================
# LOAD SCHEDULE (shared across all snapshots)
# =====================================================

schedule = pd.read_csv("Data/schedule.csv")

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
# RUN ONE SNAPSHOT
# =====================================================

def run_one_snapshot(standings_path, cutoff_date_str):

    standings = pd.read_csv(standings_path)

    standings["Team"] = standings["Team"].replace(TEAM_NAME_MAP)

    cutoff_date = pd.to_datetime(cutoff_date_str)

    remaining_games = schedule[
        schedule["CleanDate"] > cutoff_date
    ]

    if len(remaining_games) == 0:
        raise ValueError(
            f"No remaining games found for cutoff {cutoff_date_str} "
            f"(standings file: {standings_path}). Check date parsing."
        )

    stats = initialize_stats(standings)

    elo_total = {
        team: 0
        for team in standings["Team"]
    }

    for _ in range(N_SIMULATIONS):

        ratings = build_ratings(standings)

        final = simulate_season(
            standings,
            remaining_games,
            ratings
        )

        for team in ratings:
            elo_total[team] += ratings[team]

        update_regular_season_stats(stats, final)

        stats = simulate_playoffs(final, ratings, stats)

    average_elo = {
        team: round(elo_total[team] / N_SIMULATIONS, 0)
        for team in elo_total
    }

    sos = compute_sos(remaining_games, average_elo)

    results = build_results(
        stats,
        N_SIMULATIONS,
        sos,
        standings,
        remaining_games,
        average_elo
    )

    return results


# =====================================================
# LOOP OVER ALL 4 SNAPSHOTS
# =====================================================

all_history = []

for snapshot_date, cutoff_date_str, standings_path in SNAPSHOTS:

    print(f"Running simulation for {snapshot_date} (cutoff {cutoff_date_str})...")

    results = run_one_snapshot(standings_path, cutoff_date_str)

    snapshot_history = results[
        [
            "Team",
            "Playoff Odds",
            "Semis Odds",
            "Finals Odds",
            "Championship Odds",
            "Elo"
        ]
    ].copy()

    snapshot_history["Date"] = snapshot_date

    all_history.append(snapshot_history)

    print(f"  -> done, {len(snapshot_history)} teams recorded.\n")


# =====================================================
# SAVE
# =====================================================

history = pd.concat(all_history, ignore_index=True)

history.to_csv(
    "Outputs/playoff_history.csv",
    index=False
)

print(
    f"Done! Outputs/playoff_history.csv rebuilt with "
    f"{len(history)} rows across {len(SNAPSHOTS)} dates."
)