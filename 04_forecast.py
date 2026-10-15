"""
Step 4: Forecast the Brent oil price for the next 12 months,
and prepare clean files for the Power BI dashboard.

Plan
  1. Take monthly Brent prices from the database.
  2. Work with log(price). Oil moves in % terms, and logs turn % moves into
     plain differences, which models handle better.
  3. Pick an ARIMA model using AIC (lower AIC = better balance of fit and simplicity).
  4. Backtest: for each of the last 36 months, train on everything before it
     and forecast just that month. Compare against a "naive" forecast
     (next month = this month). If ARIMA can't beat naive, we say so honestly.
     We also check if the "80% range" really contains the real price ~80% of the time.
  5. Fit on all data and forecast 12 months ahead, with 80% and 95% ranges.
  6. Export CSV files into powerbi_data/ for Power BI.

Input : data/energy.db
Output: powerbi_data/*.csv
"""

import sqlite3
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

warnings.filterwarnings("ignore")      # hide statsmodels' noisy fitting messages

DB_PATH = Path("data/energy.db")
OUT_DIR = Path("powerbi_data")
TEST_MONTHS = 36        # how many recent months to use for the backtest
HORIZON = 12            # how many months ahead to forecast


# ---------------------------------------------------------------------------
# 1. Load data
# ---------------------------------------------------------------------------
def load_brent():
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(
            "SELECT month, price FROM prices WHERE benchmark = 'Brent' ORDER BY month",
            conn,
        )
    df["month"] = pd.to_datetime(df["month"])
    # Make "month" the index and tell pandas the data is monthly ("MS" = month start)
    series = df.set_index("month")["price"].asfreq("MS")
    return series


# ---------------------------------------------------------------------------
# 2-3. Choose the ARIMA order with AIC
# ---------------------------------------------------------------------------
def choose_order(log_train):
    """Try small ARIMA(p,1,q) models and return the (p,1,q) with the lowest AIC.
    d=1 means we model month-to-month changes, because prices themselves
    keep drifting (they are not stationary)."""
    best_order, best_aic = None, np.inf
    for p in range(0, 3):
        for q in range(0, 3):
            aic = ARIMA(log_train, order=(p, 1, q)).fit().aic
            if aic < best_aic:
                best_order, best_aic = (p, 1, q), aic
    print(f"Best model by AIC: ARIMA{best_order} (AIC = {best_aic:.1f})")
    return best_order


# ---------------------------------------------------------------------------
# 4. Backtest against the naive forecast
# ---------------------------------------------------------------------------
def backtest(prices, order):
    log_prices = np.log(prices)
    rows = []
    # Walk forward one month at a time through the last TEST_MONTHS months
    for i in range(len(prices) - TEST_MONTHS, len(prices)):
        train = log_prices.iloc[:i]                      # everything before month i
        model = ARIMA(train, order=order).fit()
        fc = model.get_forecast(1)
        arima_pred = float(np.exp(fc.predicted_mean.iloc[0]))   # back from log to USD
        low, high = np.exp(fc.conf_int(alpha=0.20).iloc[0])     # the 80% range
        naive_pred = float(prices.iloc[i - 1])          # naive: same as last month
        rows.append({
            "month": prices.index[i],
            "actual": float(prices.iloc[i]),
            "arima": arima_pred,
            "naive": naive_pred,
            "low_80": low,
            "high_80": high,
        })
    bt = pd.DataFrame(rows)

    # Range check: an "80% range" should contain the real price about 80% of the time.
    inside = (bt["actual"] >= bt["low_80"]) & (bt["actual"] <= bt["high_80"])
    coverage = float(inside.mean() * 100)

    # MAPE = average size of the error, as a % of the real price
    def mape(pred):
        return float(np.mean(np.abs(bt[pred] - bt["actual"]) / bt["actual"]) * 100)

    scores = pd.DataFrame({
        "model": [f"ARIMA{order}", "Naive (last month)"],
        "mape_pct": [round(mape("arima"), 2), round(mape("naive"), 2)],
        "coverage_80_pct": [round(coverage, 1), None],   # naive has no range, so blank
        "test_months": TEST_MONTHS,
    })
    print("\nBacktest, 1-month-ahead, last", TEST_MONTHS, "months")
    print(scores.to_string(index=False))
    return bt, scores


# ---------------------------------------------------------------------------
# 5. Forecast the next 12 months with ranges
# ---------------------------------------------------------------------------
def forecast_future(prices, order):
    model = ARIMA(np.log(prices), order=order).fit()
    fc = model.get_forecast(HORIZON)
    mean = np.exp(fc.predicted_mean)          # middle forecast in USD
    ci80 = np.exp(fc.conf_int(alpha=0.20))    # 80% range (alpha = 1 - 0.80)
    ci95 = np.exp(fc.conf_int(alpha=0.05))    # 95% range
    return pd.DataFrame({
        "month": mean.index,
        "forecast": mean.values.round(2),
        "low_80": ci80.iloc[:, 0].values.round(2),
        "high_80": ci80.iloc[:, 1].values.round(2),
        "low_95": ci95.iloc[:, 0].values.round(2),
        "high_95": ci95.iloc[:, 1].values.round(2),
    })


# ---------------------------------------------------------------------------
# 6. Export everything Power BI needs
# ---------------------------------------------------------------------------
def export_for_powerbi(prices, bt, scores, future):
    OUT_DIR.mkdir(exist_ok=True)

    # One table for the forecast chart: history + backtest + future, in one shape.
    history = pd.DataFrame({"month": prices.index, "actual": prices.values})
    chart = history.merge(bt[["month", "arima"]], on="month", how="left")
    chart = chart.rename(columns={"arima": "backtest_forecast"})
    chart = pd.concat([chart, future], ignore_index=True)
    chart = chart[chart["month"] >= "2015-01-01"]          # last ~10 years looks cleaner
    chart.to_csv(OUT_DIR / "brent_forecast.csv", index=False, date_format="%Y-%m-%d")

    scores.to_csv(OUT_DIR / "model_scores.csv", index=False)

    # Copy the database tables Power BI will use, as plain CSV files
    with sqlite3.connect(DB_PATH) as conn:
        for table in ["prices", "india_mix", "india_demand"]:
            pd.read_sql_query(f"SELECT * FROM {table}", conn).to_csv(
                OUT_DIR / f"{table}.csv", index=False
            )
    print(f"\nPower BI files saved in {OUT_DIR}/")


if __name__ == "__main__":
    brent = load_brent()
    train_part = np.log(brent.iloc[:-TEST_MONTHS])    # choose the model on training data only
    order = choose_order(train_part)
    bt, scores = backtest(brent, order)
    future = forecast_future(brent, order)
    print("\nNext 12 months (USD per barrel):")
    print(future.to_string(index=False))
    export_for_powerbi(brent, bt, scores, future)
