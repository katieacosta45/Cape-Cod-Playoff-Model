import random


# ----------------------------
# SINGLE GAME SIM
# ----------------------------
def simulate_game(team_a, team_b, ratings):
    prob_a = ratings[team_a] / (ratings[team_a] + ratings[team_b])

    return team_a if random.random() < prob_a else team_b


# ----------------------------
# BEST OF 3 SERIES
# ----------------------------
def simulate_series(team1, team2, ratings):

    wins1 = 0
    wins2 = 0

    while wins1 < 2 and wins2 < 2:

        winner = simulate_game(team1, team2, ratings)

        if winner == team1:
            wins1 += 1
        else:
            wins2 += 1

    return team1 if wins1 > wins2 else team2


# ----------------------------
# BUILD PLAYOFF BRACKET
# ----------------------------
def get_top_4(div_df):
    return div_df.sort_values(
        ["Points", "Wins"],
        ascending=False
    ).head(4)["Team"].tolist()


# ----------------------------
# RUN FULL PLAYOFFS
# ----------------------------
def simulate_playoffs(final, ratings, stats):

    east = final[final["Division"] == "East"]
    west = final[final["Division"] == "West"]

    east_teams = get_top_4(east)
    west_teams = get_top_4(west)

    # ------------------------
    # SEMIFINALS
    # (1 vs 4, 2 vs 3)
    # ------------------------

    east_sf1 = simulate_series(east_teams[0], east_teams[3], ratings)
    east_sf2 = simulate_series(east_teams[1], east_teams[2], ratings)

    west_sf1 = simulate_series(west_teams[0], west_teams[3], ratings)
    west_sf2 = simulate_series(west_teams[1], west_teams[2], ratings)

    stats["semis"][east_sf1] += 1
    stats["semis"][east_sf2] += 1
    stats["semis"][west_sf1] += 1
    stats["semis"][west_sf2] += 1

    # ------------------------
    # FINALS (DIVISIONAL)
    # ------------------------

    east_champ = simulate_series(east_sf1, east_sf2, ratings)
    west_champ = simulate_series(west_sf1, west_sf2, ratings)

    stats["finals"][east_champ] += 1
    stats["finals"][west_champ] += 1

    # ------------------------
    # CHAMPIONSHIP
    # ------------------------

    champ = simulate_series(east_champ, west_champ, ratings)

    stats["titles"][champ] += 1

    return stats