import pandas as pd
import re

file_path = "Data/raw_schedule.txt"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

games = []

for line in lines:
    parts = line.strip().split("\t")

    for cell in parts:
        if "@" not in cell and not any(x in cell for x in ["BOU","BRE","CHA","COT","FAL","HAR","HYA","ORL","WAR","Y-D"]):
            continue

        match = re.search(r"@?([A-Z-]+)", cell)

        if match:
            team = match.group(1)

            # we will refine logic after first run
            games.append(team)

print(games[:20])