import pandas as pd

BASE_ELO = 1500
SCALE = 300


def build_ratings(standings):
    """
    Build starting Elo ratings from current winning percentage.
    """

    ratings = {}

    for _, team in standings.iterrows():

        games = team["Wins"] + team["Losses"] + team["Ties"]

        if games == 0:
            win_pct = 0.500
        else:
            win_pct = (team["Wins"] + 0.5 * team["Ties"]) / games

        rating = BASE_ELO + (win_pct - 0.500) * SCALE

        ratings[team["Team"]] = rating

    return ratings