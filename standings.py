import pandas as pd

# =====================================================
# LOAD STANDINGS
# =====================================================

def load_standings():

    standings = pd.read_csv("Data/standings.csv")

    # Ensure required columns exist
    for col in ["Wins", "Losses", "Ties"]:
        if col not in standings.columns:
            standings[col] = 0

    standings["Wins"] = standings["Wins"].astype(int)
    standings["Losses"] = standings["Losses"].astype(int)
    standings["Ties"] = standings["Ties"].astype(int)

    # Points system (Cape Cod style)
    standings["Points"] = (
        standings["Wins"] * 2
        + standings["Ties"]
    )

    return standings


# =====================================================
# UPDATE STANDINGS AFTER GAME
# =====================================================

def update_standings(standings, home, away, result):

    # HOME WIN
    if result == "HOME":

        standings.loc[standings.Team == home, "Wins"] += 1
        standings.loc[standings.Team == away, "Losses"] += 1

    # AWAY WIN
    elif result == "AWAY":

        standings.loc[standings.Team == away, "Wins"] += 1
        standings.loc[standings.Team == home, "Losses"] += 1

    # TIE (NEW — FULL SUPPORT)
    elif result == "TIE":

        standings.loc[standings.Team == home, "Ties"] += 1
        standings.loc[standings.Team == away, "Ties"] += 1

    # Recalculate points after every update
    standings["Points"] = (
        standings["Wins"] * 2
        + standings["Ties"]
    )

    return standings