import pandas as pd


def load_standings():

    standings = pd.read_csv("Data/standings.csv")

    standings["Points"] = (
        standings["Wins"] * 2
        + standings["Ties"]
    )

    return standings


def update_standings(standings, home, away, result):

    if result == "HOME":

        standings.loc[
            standings.Team == home,
            "Wins"
        ] += 1

        standings.loc[
            standings.Team == away,
            "Losses"
        ] += 1

    else:

        standings.loc[
            standings.Team == away,
            "Wins"
        ] += 1

        standings.loc[
            standings.Team == home,
            "Losses"
        ] += 1

    standings["Points"] = (
        standings["Wins"] * 2
        + standings["Ties"]
    )

    return standings