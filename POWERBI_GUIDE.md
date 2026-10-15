# Power BI Guide: building the 2-page dashboard

You need **Power BI Desktop** (free, Windows only). Install it from the Microsoft Store.
Run the Python steps first, so the folder `powerbi_data/` has these 5 files:

| File | What is in it |
|---|---|
| `prices.csv` | month, benchmark (Brent / WTI / Henry Hub Gas), price, unit |
| `brent_forecast.csv` | month, actual, backtest_forecast, forecast, low_80, high_80, low_95, high_95 |
| `model_scores.csv` | model, mape_pct, coverage_80_pct, test_months |
| `india_mix.csv` | year, source (Coal, Solar ...), share_pct |
| `india_demand.csv` | year, demand_twh |

The finished dashboard has 2 pages:
- **Page 1, Oil & Gas Markets:** 3 number cards, a price history chart, and the Brent forecast chart
- **Page 2, India Power:** 3 number cards, the electricity mix chart, and the demand chart

---

## Part 1: Load the data (about 10 minutes)

1. Open Power BI Desktop and choose **Blank report**.
2. Go to **Home → Get data → Text/CSV**, pick `prices.csv`, then click **Transform Data**. This opens the Power Query editor.
3. In Power Query, check the small icon on the left of each column header:
   - `month` should be a **calendar icon (Date)**. If it shows "ABC" (text), click the icon and choose **Date**.
   - `price` should be **1.2 (Decimal number)**.
4. Click **Close & Apply**.
5. Repeat steps 2 to 4 for the other 4 files. In `india_mix` and `india_demand`, set `year` to **Whole number**.

You don't need to link the tables to each other. Each chart uses one table.

## Part 2: Pick a theme (2 minutes)

Go to **View → Themes** and pick a clean one, like "Executive" or "Frontier". Use the same theme for both pages so the dashboard looks like one piece.

## Part 3: Create measures (about 10 minutes)

A **measure** is a small formula that Power BI recalculates for you. To make one, right-click a table in the **Data** pane on the right → **New measure**, paste the formula, and press Enter.

In the `prices` table:

```DAX
Latest Brent =
VAR lastMonth = CALCULATE ( MAX ( prices[month] ), prices[benchmark] = "Brent" )
RETURN
    CALCULATE ( MAX ( prices[price] ), prices[benchmark] = "Brent", prices[month] = lastMonth )
```
This finds the newest month for Brent, then returns the Brent price for that month.

```DAX
Brent 12m Change % =
VAR lastMonth = CALCULATE ( MAX ( prices[month] ), prices[benchmark] = "Brent" )
VAR nowPrice = CALCULATE ( MAX ( prices[price] ), prices[benchmark] = "Brent", prices[month] = lastMonth )
VAR yearAgo  = CALCULATE ( MAX ( prices[price] ), prices[benchmark] = "Brent", prices[month] = EDATE ( lastMonth, -12 ) )
RETURN
    DIVIDE ( nowPrice - yearAgo, yearAgo )
```
`EDATE(date, -12)` means "the same date, 12 months earlier". `DIVIDE` is a safe division that won't crash if the bottom number is 0. After creating it, select the measure and click the **%** button under **Measure tools** to show it as a percentage.

In the `india_mix` table:

```DAX
Coal Share 2025 % = CALCULATE ( SUM ( india_mix[share_pct] ), india_mix[source] = "Coal", india_mix[year] = 2025 )
```
```DAX
Solar Share 2025 % = CALCULATE ( SUM ( india_mix[share_pct] ), india_mix[source] = "Solar", india_mix[year] = 2025 )
```

In the `india_demand` table:

```DAX
Demand 2025 TWh = CALCULATE ( SUM ( india_demand[demand_twh] ), india_demand[year] = 2025 )
```

---

## Part 4: Page 1, Oil & Gas Markets (about 25 minutes)

Rename the page: double-click "Page 1" at the bottom and type **Oil & Gas Markets**.

**a) Title.** Insert → **Text box**: "Oil & Gas Markets, 1997 to 2026". Make it bold, size 20.

**b) Three cards in a row at the top.** For each one, click the **Card** visual, then drag the field into it:
- `Latest Brent` → in Format, set the title to "Latest Brent (USD/barrel)"
- `Brent 12m Change %`
- From `model_scores`: drag `mape_pct`, set it to **Minimum**, and title it "Best forecast error (MAPE %)"

**c) Price history chart (left, large).**
- Visual: **Line chart**
- X-axis: `prices[month]`. If you see "Year, Quarter, Month, Day", click the small arrow next to it and choose `month` instead of **Date Hierarchy**.
- Y-axis: `prices[price]` (Sum is fine, since there is one value per month)
- Legend: `prices[benchmark]`
- Add a **Slicer** with `prices[benchmark]`, so the user can show only Brent, WTI or gas. Gas is in a different unit (USD/MMBtu), so it looks flat next to oil. That's why the slicer helps.

**d) Brent forecast chart (right, large).**
- Visual: **Line chart**
- X-axis: `brent_forecast[month]` (not the hierarchy)
- Y-axis: add these 7 fields: `actual`, `backtest_forecast`, `forecast`, `low_80`, `high_80`, `low_95`, `high_95`
- Format → **Lines**, styled one series at a time:
  - `actual`: dark blue, solid, 2px
  - `backtest_forecast`: teal, **dashed**
  - `forecast`: orange, solid, 2px
  - `low_80` and `high_80`: light orange, **dotted**
  - `low_95` and `high_95`: very light orange or grey, **dotted**
- Title: "Brent: 12-month forecast with 80% and 95% ranges"

**e) Model scores table (small, under the forecast).**
- Visual: **Table** with `model`, `mape_pct`, `coverage_80_pct`
- Add a text box next to it: *"ARIMA beats the naive forecast only slightly (6.33% vs 6.65%). Its 80% range held the real price 91.7% of the time, so it is too cautious."*

## Part 5: Page 2, India Power (about 15 minutes)

Click **+** at the bottom to add a page and name it **India Power**.

**a) Title:** "India's Electricity: Demand and Mix, 2000 to 2025"

**b) Three cards:** `Coal Share 2025 %`, `Solar Share 2025 %`, `Demand 2025 TWh`

**c) Electricity mix chart (large).**
- Visual: **100% Stacked area chart**
- X-axis: `india_mix[year]`. In Format → X-axis, set **Type = Continuous** so the years are evenly spaced.
- Y-axis: `india_mix[share_pct]`
- Legend: `india_mix[source]`
- Colours (Format → Lines/Colors): Coal dark grey, Solar orange, Wind green, Hydro teal, and the rest in soft colours. With coal dark and solar bright, the main story is easy to see.

**d) Demand chart.**
- Visual: **Clustered column chart**
- X-axis: `india_demand[year]`, Y-axis: `india_demand[demand_twh]`
- Title: "Electricity demand, TWh"

**e) One insight text box:**
*"Coal still gives about 71% of India's power, but solar grew from 0% to 9.4% since 2000 while demand grew about 3.6 times."*

---

## Part 6: Finish (5 minutes)

1. **File → Save as** `Energy_Market_Pulse.pbix` in the project folder.
2. Take a screenshot of each page and save them as `charts/powerbi_page1.png` and `charts/powerbi_page2.png`.
3. Add them to the top of `README.md`:
   ```markdown
   ![Power BI page 1](charts/powerbi_page1.png)
   ![Power BI page 2](charts/powerbi_page2.png)
   ```
4. Push everything to GitHub.

**Tidy-up tips that make it look professional:** line up the cards to the same size (select them all → Format → Align), keep 2 or 3 colours per page, and give every chart a clear title that says what it shows.
