import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
DATA_FOLDER = PROJECT_ROOT / "data"

import os
from dotenv import load_dotenv

from src.scrape import get_data

load_dotenv()

USER_AGENT = os.getenv("USER_AGENT")

dataframe = get_data(
        user_agent = USER_AGENT,
        countries = [
        'usa','uk','canada',
        'australia','austria','belgium','denmark','finland','france','germany',
        'new-zealand','norway','sweden','switzerland','netherlands','spain'
        ],
        tags = ['data-science','machine-learning','artificial-intelligence','data-engineering'],
        posted_since = 14,
        full_load = False,
        clicks_to_load = 5,
        sleep_time_load = 4.0
)

csv_path = DATA_FOLDER / "scraped_jobs.csv"
dataframe.to_csv(csv_path, index=False)
print(f"CSV saved to {csv_path}✅")