"""
Step 5 (optional): Make 3 preview charts as PNG images for the GitHub README.

The real dashboard is built in Power BI. These images let people see the
results on GitHub without opening Power BI.

Input : powerbi_data/*.csv
Output: charts/*.png
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

DATA = Path("powerbi_data")
OUT = Path("charts")

# One small colour palette, used everywhere so the charts look like one set
NAVY, ORANGE, TEAL, GREY = "#1f3a5f", "#e8833a", "#2a9d8f", "#8d99ae"

# Simple, clean style for all charts
plt.rcParams.update({
    "figure.dpi": 150,
    "axes.spines.top": False,       # remove the top border line
    "axes.spines.right": False,     # remove the right border line
    "axes.grid": True,
    "grid.alpha": 0.25,
    "font.size": 10,
})


def chart_prices():
    """Chart 1: Brent, WTI and gas prices over time."""
    prices = pd.read_csv(DATA / "prices.csv", parse_dates=["month"])
    # pivot: one column per benchmark, months as rows -> easy to plot
    wide = prices.pivot(index="month", columns="benchmark", values="price")

    fig, ax1 = plt.subplots(figsize=(10, 4))
    ax1.plot(wide.index, wide["Brent"], color=NAVY, label="Brent (USD/barrel)")
    ax1.plot(wide.index, wide["WTI"], color=TEAL, label="WTI (USD/barrel)", alpha=0.8)
    ax1.set_ylabel("Oil price, USD per barrel")

    # Gas uses a different unit, so it gets its own axis on the right
    ax2 = ax1.twinx()
    ax2.plot(wide.index, wide["Henry Hub Gas"], color=ORANGE, label="Henry Hub gas (USD/MMBtu)", alpha=0.8)
    ax2.set_ylabel("Gas price, USD per MMBtu")
    ax2.grid(False)

    # Put both axes' lines in one legend
    lines = ax1.get_lines() + ax2.get_lines()
    ax1.legend(lines, [l.get_label() for l in lines], loc="upper left", frameon=False)
    ax1.set_title("Oil and gas prices, monthly, 1997 to 2026", loc="left", fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUT / "1_prices.png")
    plt.close(fig)


def chart_forecast():
    """Chart 2: Brent history, backtest forecasts, and the 12-month forecast with ranges."""
    df = pd.read_csv(DATA / "brent_forecast.csv", parse_dates=["month"])
    future = df[df["forecast"].notna()]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df["month"], df["actual"], color=NAVY, label="Actual Brent price")
    ax.plot(df["month"], df["backtest_forecast"], color=TEAL, linestyle="--",
            label="Backtest: 1-month-ahead forecast")
    # fill_between shades the area between the low and high lines
    ax.fill_between(future["month"], future["low_95"], future["high_95"],
                    color=ORANGE, alpha=0.15, label="95% range")
    ax.fill_between(future["month"], future["low_80"], future["high_80"],
                    color=ORANGE, alpha=0.30, label="80% range")
    ax.plot(future["month"], future["forecast"], color=ORANGE, label="Forecast")
    ax.set_ylabel("USD per barrel")
    ax.legend(loc="upper left", frameon=False)
    ax.set_title("Brent oil: 12-month forecast with uncertainty ranges", loc="left", fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUT / "2_brent_forecast.png")
    plt.close(fig)


def chart_india_mix():
    """Chart 3: India's electricity mix as a stacked area chart."""
    mix = pd.read_csv(DATA / "india_mix.csv")
    wide = mix.pivot(index="year", columns="source", values="share_pct")
    order = ["Coal", "Gas", "Oil", "Nuclear", "Hydro", "Wind", "Solar", "Other renewables"]
    colours = ["#3d3d3d", "#8d99ae", "#b5838d", "#6d597a", "#2a9d8f", "#90be6d", "#f4a261", "#c9ada7"]
    wide = wide[order]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.stackplot(wide.index, wide.T.values, labels=order, colors=colours)
    ax.set_ylim(0, 100)
    ax.set_xlim(wide.index.min(), wide.index.max())
    ax.set_ylabel("Share of electricity, %")
    ax.legend(loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False)
    ax.set_title("India's electricity mix, 2000 to 2025", loc="left", fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUT / "3_india_mix.png")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    chart_prices()
    chart_forecast()
    chart_india_mix()
    print(f"Charts saved in {OUT}/")
