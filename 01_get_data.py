"""
Step 1: Download the raw data.

We download 4 public CSV files from GitHub and save them in the folder data/raw/.
We do not change anything here. Cleaning happens in step 2.
"""

from pathlib import Path        # Path makes it easy to work with folders and file names
import urllib.request           # Built into Python; used to download files from the internet

# Where the raw files will be saved
RAW_DIR = Path("data/raw")

# A dictionary: file name we want  ->  web address (URL) to download it from
SOURCES = {
    "brent_monthly.csv": "https://raw.githubusercontent.com/datasets/oil-prices/main/data/brent-monthly.csv",
    "wti_monthly.csv":   "https://raw.githubusercontent.com/datasets/oil-prices/main/data/wti-monthly.csv",
    "gas_monthly.csv":   "https://raw.githubusercontent.com/datasets/natural-gas/main/data/monthly.csv",
    "owid_energy.csv":   "https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv",
}


def download_all():
    # Create the folder if it does not exist yet (parents=True also creates "data/")
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # Go through each (file name, URL) pair in the dictionary
    for file_name, url in SOURCES.items():
        target = RAW_DIR / file_name                 # full path, for example data/raw/brent_monthly.csv
        print(f"Downloading {file_name} ...")
        urllib.request.urlretrieve(url, target)      # download the URL and save it to that path
        size_kb = target.stat().st_size / 1024       # file size in KB, just to show it worked
        print(f"  saved to {target} ({size_kb:,.0f} KB)")


# This line means: run download_all() only when we run this file directly
# (python 01_get_data.py), not when another file imports it.
if __name__ == "__main__":
    download_all()
