"""
Step 2: Clean the raw data, check its quality, and load it into a SQL database.

Input : the CSV files in data/raw/ (made by step 1)
Output: one SQLite database file, data/energy.db, with 3 tables:
    prices        -> monthly prices of Brent oil, WTI oil and US natural gas
    india_mix     -> share of India's electricity from each source, per year
    india_demand  -> India's total electricity demand, per year

SQLite is a small SQL database that lives in a single file. It comes with Python,
so nothing extra needs to be installed. The SQL we write works the same way in
SQL Server or PostgreSQL.
"""

import sqlite3                  # Python's built-in SQL database
from pathlib import Path
import pandas as pd             # pandas = tables (DataFrames) in Python

RAW_DIR = Path("data/raw")
DB_PATH = Path("data/energy.db")


# ---------------------------------------------------------------------------
# Part A: prices
# ---------------------------------------------------------------------------
def load_price_file(file_name, date_col, benchmark, unit):
    """Read one price file and return it in a standard shape:
    columns = month, benchmark, price, unit"""
    df = pd.read_csv(RAW_DIR / file_name)

    # Turn the text date into a real date, then move every date to the
    # first day of its month (1987-05-15 -> 1987-05-01). This makes the
    # three price series line up on the same months.
    df["month"] = pd.to_datetime(df[date_col]).dt.to_period("M").dt.to_timestamp()

    df = df.rename(columns={"Price": "price"})
    df["benchmark"] = benchmark          # which price this is, e.g. "Brent"
    df["unit"] = unit                    # e.g. "USD per barrel"
    return df[["month", "benchmark", "price", "unit"]]


def build_prices():
    brent = load_price_file("brent_monthly.csv", "Date", "Brent", "USD per barrel")
    wti = load_price_file("wti_monthly.csv", "Date", "WTI", "USD per barrel")
    gas = load_price_file("gas_monthly.csv", "Month", "Henry Hub Gas", "USD per MMBtu")

    # Stack the three tables on top of each other ("long" format).
    # Power BI likes this shape: one column tells which line a row belongs to.
    prices = pd.concat([brent, wti, gas], ignore_index=True)

    # Keep the same time window for all three, so charts are fair to compare
    prices = prices[prices["month"] >= "1997-01-01"]
    return prices


# ---------------------------------------------------------------------------
# Part B: India electricity
# ---------------------------------------------------------------------------
# Column in the OWID file  ->  short, readable name we want to show
MIX_COLUMNS = {
    "coal_share_elec": "Coal",
    "gas_share_elec": "Gas",
    "oil_share_elec": "Oil",
    "nuclear_share_elec": "Nuclear",
    "hydro_share_elec": "Hydro",
    "solar_share_elec": "Solar",
    "wind_share_elec": "Wind",
    "other_renewables_share_elec": "Other renewables",
}


def build_india_tables():
    owid = pd.read_csv(RAW_DIR / "owid_energy.csv")

    # Keep only India, and only the years 2000 onwards
    india = owid[(owid["country"] == "India") & (owid["year"] >= 2000)]

    # Table 1: electricity mix.
    # melt() turns many columns (coal, gas, solar ...) into two columns:
    # "source" (which fuel) and "share_pct" (its % of electricity).
    mix = india[["year"] + list(MIX_COLUMNS)].melt(
        id_vars="year", var_name="source", value_name="share_pct"
    )
    mix["source"] = mix["source"].map(MIX_COLUMNS)    # coal_share_elec -> Coal
    mix = mix.dropna(subset=["share_pct"])            # drop years with no value

    # Table 2: total demand in terawatt-hours (TWh)
    demand = india[["year", "electricity_demand"]].rename(
        columns={"electricity_demand": "demand_twh"}
    ).dropna()

    return mix, demand


# ---------------------------------------------------------------------------
# Part C: data quality checks
# ---------------------------------------------------------------------------
def check_quality(prices, mix, demand):
    """Print simple checks. Stop the program if something is badly wrong."""
    print("\nData quality checks")

    # 1. Missing prices
    missing = prices["price"].isna().sum()
    print(f"  missing prices            : {missing}")

    # 2. Prices should never be zero or negative in monthly averages
    bad = (prices["price"] <= 0).sum()
    print(f"  zero/negative prices      : {bad}")

    # 3. Each benchmark should have only one row per month
    dupes = prices.duplicated(subset=["month", "benchmark"]).sum()
    print(f"  duplicate months          : {dupes}")

    # 4. For each year, the shares of all sources should add up to about 100%
    totals = mix.groupby("year")["share_pct"].sum()
    off = totals[(totals < 98) | (totals > 102)]
    print(f"  years where mix != ~100%  : {len(off)}")

    # assert = "this must be true, otherwise stop with an error"
    assert missing == 0 and bad == 0 and dupes == 0, "Price data failed checks"
    assert len(off) == 0, "Electricity mix does not add up to 100%"
    print("  all checks passed")


# ---------------------------------------------------------------------------
# Part D: write everything into the database
# ---------------------------------------------------------------------------
def save_to_db(prices, mix, demand):
    # Store dates as plain text "YYYY-MM-DD" so any SQL tool can read them
    prices = prices.assign(month=prices["month"].dt.strftime("%Y-%m-%d"))

    with sqlite3.connect(DB_PATH) as conn:              # opens (or creates) the database file
        # if_exists="replace" -> running the script again rebuilds the table cleanly
        prices.to_sql("prices", conn, if_exists="replace", index=False)
        mix.to_sql("india_mix", conn, if_exists="replace", index=False)
        demand.to_sql("india_demand", conn, if_exists="replace", index=False)

    print(f"\nSaved to {DB_PATH}:")
    print(f"  prices       : {len(prices):,} rows "
          f"({prices['month'].min()} to {prices['month'].max()})")
    print(f"  india_mix    : {len(mix):,} rows ({mix['year'].min()}-{mix['year'].max()})")
    print(f"  india_demand : {len(demand):,} rows")


if __name__ == "__main__":
    prices = build_prices()
    mix, demand = build_india_tables()
    check_quality(prices, mix, demand)
    save_to_db(prices, mix, demand)
