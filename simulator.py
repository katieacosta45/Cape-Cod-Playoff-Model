import random

# =====================================================
# SETTINGS
# =====================================================

HOME_FIELD_ADVANTAGE = 35
K_FACTOR = 20
TIE_PROBABILITY = 0.07   # 7% chance of a tie


# =====================================================
# ELO WIN PROBABILITY
# =====================================================

def win_probability(home_rating, away_rating):
    """
    Returns the probability the home team wins using Elo.
    """

    rating_diff = (home_rating + HOME_FIELD_ADVANTAGE) - away_rating

    return 1 / (1 + 10 ** (-rating_diff / 400))


# =====================================================
# SIMULATE ONE GAME
# =====================================================

def simulate_game(home, away, ratings):
    """
    Simulate one game.
    Returns:
        HOME
        AWAY
        TIE
    """

    home_prob = win_probability(
        ratings[home],
        ratings[away]
    )

    r = random.random()

    # Tie
    if r < TIE_PROBABILITY:
        return "TIE"

    # Home win
    elif r < TIE_PROBABILITY + (1 - TIE_PROBABILITY) * home_prob:
        return "HOME"

    # Away win
    else:
        return "AWAY"


# =====================================================
# UPDATE ELO
# =====================================================

def update_elo(home, away, result, ratings):
    """
    Update Elo ratings after one simulated game.
    """

    expected_home = win_probability(
        ratings[home],
        ratings[away]
    )

    expected_away = 1 - expected_home

    if result == "HOME":
        actual_home = 1
        actual_away = 0

    elif result == "AWAY":
        actual_home = 0
        actual_away = 1

    else:   # Tie
        actual_home = 0.5
        actual_away = 0.5

    ratings[home] += K_FACTOR * (actual_home - expected_home)
    ratings[away] += K_FACTOR * (actual_away - expected_away)


# =====================================================
# SIMULATE ENTIRE SEASON
# =====================================================

def simulate_season(standings, schedule, ratings):
    """
    Simulate the remainder of the season.
    """

    # Convert standings into dictionaries (much faster than DataFrames)
    wins = dict(zip(standings["Team"], standings["Wins"]))
    losses = dict(zip(standings["Team"], standings["Losses"]))
    ties = dict(zip(standings["Team"], standings["Ties"]))

    # Simulate every remaining game
    for _, game in schedule.iterrows():

        home = game["Home"]
        away = game["Away"]

        result = simulate_game(
            home,
            away,
            ratings
        )

        if result == "HOME":

            wins[home] += 1
            losses[away] += 1

        elif result == "AWAY":

            wins[away] += 1
            losses[home] += 1

        else:

            ties[home] += 1
            ties[away] += 1

        # Update Elo ratings after every simulated game
        update_elo(
            home,
            away,
            result,
            ratings
        )

    # Build final standings
    final = standings.copy()

    final["Wins"] = final["Team"].map(wins)
    final["Losses"] = final["Team"].map(losses)
    final["Ties"] = final["Team"].map(ties)
    final["Points"] = final["Wins"] * 2 + final["Ties"]

    return final