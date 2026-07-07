import os
from datetime import datetime, timedelta

import pandas as pd
import requests
from bs4 import BeautifulSoup

# =====================================================
# SETTINGS
# =====================================================

START_DATE = "2026-06-13"
END_DATE = "2026-07-07"

OUTPUT_FOLDER = "Data/Historical"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# =====================================================
# LOOP THROUGH EACH DATE
# =====================================================

current = datetime.strptime(START_DATE, "%Y-%m-%d")
end = datetime.strptime(END_DATE, "%Y-%m-%d")

while current <= end:

    date_str = current.strftime("%Y-%m-%d")

    url = f"https://www.capecodleague.com/standings/?date={date_str}"

    print(f"\nDownloading {date_str}...")

    try:

        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        tables = soup.find_all("table")

        print(f"Found {len(tables)} tables")

        # Save the raw tables so we can inspect them
        for i, table in enumerate(tables):

            try:

                df = pd.read_html(str(table))[0]

                print(f"\nTABLE {i}")
                print(df.head())

                df.to_csv(
                    os.path.join(
                        OUTPUT_FOLDER,
                        f"{date_str}_table{i}.csv"
                    ),
                    index=False
                )

            except Exception:
                pass

    except Exception as e:

        print(e)

    current += timedelta(days=1)

print("\nDone!")