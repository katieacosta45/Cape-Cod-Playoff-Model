import pandas as pd
from simulator import simulate_game

def run_remaining_season(standings, schedule):
    standings = standings.copy()

    for _, game in schedule.iterrows():
        winner = simulate_game(game["Home"], game["Away"])

        if winner == game["Home"]:
            standings.loc[standings["Team"] == game["Home"], "Wins"] += 1
            standings.loc[standings["Team"] == game["Away"], "Losses"] += 1
        else:
            standings.loc[standings["Team"] == game["Away"], "Wins"] += 1
            standings.loc[standings["Team"] == game["Home"], "Losses"] += 1

    standings["Points"] = standings["Wins"] * 2 + standings["Ties"]
    return standings