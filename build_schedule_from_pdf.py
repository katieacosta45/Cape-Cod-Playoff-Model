from pypdf import PdfReader
import re
import pandas as pd

pdf_path = "Data/2026-cape-cod-baseball-league-schedule.pdf"

reader = PdfReader(pdf_path)
text = "\n".join(page.extract_text() or "" for page in reader.pages)

lines = text.split("\n")

games = []
current_date = None

team_map = {
    "BOU": "Bourne",
    "BRE": "Brewster",
    "CHA": "Chatham",
    "COT": "Cotuit",
    "FAL": "Falmouth",
    "HAR": "Harwich",
    "HYA": "Hyannis",
    "ORL": "Orleans",
    "WAR": "Wareham",
    "Y-O": "Y-D",
    "Y-D": "Y-D"
}

date_pattern = re.compile(r"(JUN|JUL|AUG)\s+\d+")

game_pattern = re.compile(r"([A-Z\-]+)\s*@\s*([A-Z\-]+)|([A-Z\-]+)@([A-Z\-]+)")

for line in lines:
    line = line.strip()

    # detect date
    if date_pattern.match(line):
        current_date = line
        continue

    # skip junk
    if any(x in line for x in ["OFF", "ASG", "DIVISIONAL", "CHAMPIONSHIP", "MAKE UP"]):
        continue

    matches = re.findall(r"([A-Z\-]+)\s*@\s*([A-Z\-]+)", line)

    for away, home in matches:
        if away in team_map and home in team_map:
            games.append([
                current_date,
                team_map[home],
                team_map[away]
            ])

# clean dataframe
df = pd.DataFrame(games, columns=["Date", "Home", "Away"])

df.to_csv("Data/schedule.csv", index=False)

print(df.head(20))
print("\nTotal games:", len(df))