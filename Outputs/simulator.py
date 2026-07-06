import random

def simulate_game(home, away):
    # placeholder strength model (we improve later)
    home_adv = 0.54

    if random.random() < home_adv:
        return home
    else:
        return away