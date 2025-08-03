-- Single query to retrieve all USD OIS curve tickers
SELECT 
    rcd.curve_name,
    rcd.currency,
    array_agg(
        bt.ticker ORDER BY rcm.sequence_order
    ) as tickers,
    array_agg(
        rcm.tenor ORDER BY rcm.sequence_order
    ) as tenors
FROM rate_curve_definitions rcd
JOIN rate_curve_memberships rcm ON rcd.id = rcm.curve_id
JOIN bloomberg_tickers bt ON rcm.ticker_id = bt.id
WHERE rcd.curve_name = 'USD_OIS'
GROUP BY rcd.curve_name, rcd.currency;

-- This returns one row with:
-- curve_name: 'USD_OIS'
-- currency: 'USD'
-- tickers: ['USSOA Curncy', 'USSOB Curncy', ..., 'USSO10 Curncy']
-- tenors: ['1M', '2M', ..., '10Y']

-- Alternative: Get all details in one query
SELECT 
    json_build_object(
        'curve_name', rcd.curve_name,
        'currency', rcd.currency,
        'tickers', json_agg(
            json_build_object(
                'ticker', bt.ticker,
                'tenor', rcm.tenor,
                'tenor_days', rcm.tenor_days
            ) ORDER BY rcm.sequence_order
        )
    ) as curve_data
FROM rate_curve_definitions rcd
JOIN rate_curve_memberships rcm ON rcd.id = rcm.curve_id
JOIN bloomberg_tickers bt ON rcm.ticker_id = bt.id
WHERE rcd.curve_name = 'USD_OIS'
GROUP BY rcd.curve_name, rcd.currency;

-- This returns JSON like:
-- {
--   "curve_name": "USD_OIS",
--   "currency": "USD",
--   "tickers": [
--     {"ticker": "USSOA Curncy", "tenor": "1M", "tenor_days": 30},
--     {"ticker": "USSOB Curncy", "tenor": "2M", "tenor_days": 60},
--     ...
--     {"ticker": "USSO10 Curncy", "tenor": "10Y", "tenor_days": 3650}
--   ]
-- }