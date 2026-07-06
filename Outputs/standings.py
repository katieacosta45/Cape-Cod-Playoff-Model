import pandas as pd

def load_standings():
    standings = pd.read_csv("Data/standings.csv")

cutoff_date = "2026-07-01"  # your last completed game

played = schedule[schedule["Date"] <= cutoff_date]
remaining = schedule[schedule["Date"] > cutoff_date]

    standings["Points"] = standings["Wins"] * 2 + standings["Ties"]

    return standings


def update_standings(standings, home_team, away_team, result):

    home = standings["Team"] == home_team
    away = standings["Team"] == away_team

    if result == "HOME":
        standings.loc[home, "Wins"] += 1
        standings.loc[away, "Losses"] += 1
        standings.loc[home, "Points"] += 2

    elif result == "AWAY":
        standings.loc[away, "Wins"] += 1
        standings.loc[home, "Losses"] += 1
        standings.loc[away, "Points"] += 2

    elif result == "TIE":
        standings.loc[home, "Ties"] += 1
        standings.loc[away, "Ties"] += 1
        standings.loc[home, "Points"] += 1
        standings.loc[away, "Points"] += 1

    return standings