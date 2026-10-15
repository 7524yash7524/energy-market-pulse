"""
Step 3: Run every query in queries.sql and save each answer as a CSV file.

Input : data/energy.db and queries.sql
Output: one CSV per query in outputs/ (for example outputs/brent_wti_spread.csv)
"""

import sqlite3
from pathlib import Path
import pandas as pd

DB_PATH = Path("data/energy.db")
SQL_FILE = Path("queries.sql")
OUT_DIR = Path("outputs")


def read_queries():
    """Split queries.sql into a dictionary: {query name: SQL text}.
    Every query starts with a line like '-- name: yearly_avg_prices'."""
    text = SQL_FILE.read_text()
    queries = {}
    # split() cuts the file into pieces at every '-- name:'.
    # The first piece is the header comment at the top, so we skip it with [1:].
    for block in text.split("-- name:")[1:]:
        name, sql = block.split("\n", 1)     # first line = name, the rest = SQL
        queries[name.strip()] = sql.strip()
    return queries


def run_all():
    OUT_DIR.mkdir(exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        for name, sql in read_queries().items():
            result = pd.read_sql_query(sql, conn)    # run the SQL, get a table back
            result.to_csv(OUT_DIR / f"{name}.csv", index=False)
            print(f"\n=== {name} ({len(result)} rows) ===")
            print(result.head(5).to_string(index=False))   # show the first 5 rows


if __name__ == "__main__":
    run_all()
