-- Step 3: SQL questions we ask the database.
-- Each query starts with a "name" line, for example the one just below.
-- The Python file 03_run_sql.py reads this file, runs each query,
-- and saves the answer as outputs/<query name>.csv

-- name: yearly_avg_prices
-- Q1. What was the average price of each benchmark in each year?
SELECT
    substr(month, 1, 4)        AS year,        -- '2024-05-01' -> '2024'
    benchmark,
    ROUND(AVG(price), 2)       AS avg_price,
    ROUND(MIN(price), 2)       AS min_price,
    ROUND(MAX(price), 2)       AS max_price
FROM prices
GROUP BY year, benchmark
ORDER BY year, benchmark;

-- name: brent_wti_spread
-- Q2. How much more expensive is Brent than WTI each month? (the "spread")
-- We put Brent and WTI side by side using a self-join on the same month.
SELECT
    b.month,
    b.price                    AS brent,
    w.price                    AS wti,
    ROUND(b.price - w.price, 2) AS spread_usd
FROM prices AS b
JOIN prices AS w
    ON  w.month = b.month
    AND w.benchmark = 'WTI'
WHERE b.benchmark = 'Brent'
ORDER BY b.month;

-- name: biggest_brent_moves
-- Q3. Which 10 months had the biggest % change in Brent price?
-- LAG() looks at the previous row (the previous month) in time order.
WITH brent AS (
    SELECT
        month,
        price,
        LAG(price) OVER (ORDER BY month) AS prev_price
    FROM prices
    WHERE benchmark = 'Brent'
)
SELECT
    month,
    prev_price,
    price,
    ROUND(100.0 * (price - prev_price) / prev_price, 1) AS pct_change
FROM brent
WHERE prev_price IS NOT NULL
ORDER BY ABS(price - prev_price) / prev_price DESC
LIMIT 10;

-- name: india_mix_change
-- Q4. How did India's electricity mix change between 2000 and 2025?
SELECT
    source,
    ROUND(MAX(CASE WHEN year = 2000 THEN share_pct END), 1) AS share_2000,
    ROUND(MAX(CASE WHEN year = 2025 THEN share_pct END), 1) AS share_2025,
    ROUND(MAX(CASE WHEN year = 2025 THEN share_pct END)
        - MAX(CASE WHEN year = 2000 THEN share_pct END), 1) AS change_pct_points
FROM india_mix
GROUP BY source
ORDER BY share_2025 DESC;

-- name: india_demand_growth
-- Q5. How fast is India's electricity demand growing each year?
SELECT
    year,
    ROUND(demand_twh, 0) AS demand_twh,
    ROUND(100.0 * (demand_twh - LAG(demand_twh) OVER (ORDER BY year))
          / LAG(demand_twh) OVER (ORDER BY year), 1) AS growth_pct
FROM india_demand
ORDER BY year;
