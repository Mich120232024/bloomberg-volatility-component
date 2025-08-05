-- Insert USD OIS curve definition
INSERT INTO rate_curve_definitions (curve_name, curve_type, currency, description, active)
VALUES ('USD_OIS', 'OIS', 'USD', 'USD SOFR Overnight Index Swap Curve', true)
ON CONFLICT (curve_name) DO UPDATE SET active = true
RETURNING id;

-- Store the curve_id (you'll need to use the returned ID from above)
-- For this example, let's assume it returns id = 1

-- Insert bloomberg tickers for USD OIS
INSERT INTO bloomberg_tickers (ticker, description, currency, instrument_type, active)
VALUES 
    ('USSOA Curncy', 'USD SOFR OIS 1M', 'USD', 'OIS', true),
    ('USSOB Curncy', 'USD SOFR OIS 2M', 'USD', 'OIS', true),
    ('USSOC Curncy', 'USD SOFR OIS 3M', 'USD', 'OIS', true),
    ('USSOD Curncy', 'USD SOFR OIS 4M', 'USD', 'OIS', true),
    ('USSOE Curncy', 'USD SOFR OIS 5M', 'USD', 'OIS', true),
    ('USSOF Curncy', 'USD SOFR OIS 6M', 'USD', 'OIS', true),
    ('USSOG Curncy', 'USD SOFR OIS 7M', 'USD', 'OIS', true),
    ('USSOH Curncy', 'USD SOFR OIS 8M', 'USD', 'OIS', true),
    ('USSOI Curncy', 'USD SOFR OIS 9M', 'USD', 'OIS', true),
    ('USSOJ Curncy', 'USD SOFR OIS 10M', 'USD', 'OIS', true),
    ('USSOK Curncy', 'USD SOFR OIS 11M', 'USD', 'OIS', true),
    ('USSO1 Curncy', 'USD SOFR OIS 1Y', 'USD', 'OIS', true),
    ('USSO2 Curncy', 'USD SOFR OIS 2Y', 'USD', 'OIS', true),
    ('USSO3 Curncy', 'USD SOFR OIS 3Y', 'USD', 'OIS', true),
    ('USSO4 Curncy', 'USD SOFR OIS 4Y', 'USD', 'OIS', true),
    ('USSO5 Curncy', 'USD SOFR OIS 5Y', 'USD', 'OIS', true),
    ('USSO6 Curncy', 'USD SOFR OIS 6Y', 'USD', 'OIS', true),
    ('USSO7 Curncy', 'USD SOFR OIS 7Y', 'USD', 'OIS', true),
    ('USSO8 Curncy', 'USD SOFR OIS 8Y', 'USD', 'OIS', true),
    ('USSO9 Curncy', 'USD SOFR OIS 9Y', 'USD', 'OIS', true),
    ('USSO10 Curncy', 'USD SOFR OIS 10Y', 'USD', 'OIS', true)
ON CONFLICT (ticker) DO UPDATE SET active = true;

-- Insert curve memberships (linking tickers to curve)
-- This assumes curve_id = 1 from the first insert
INSERT INTO rate_curve_memberships (curve_id, ticker_id, tenor, tenor_days, sequence_order)
SELECT 
    1 as curve_id,  -- Replace with actual curve_id from first query
    bt.id as ticker_id,
    CASE 
        WHEN bt.ticker LIKE 'USSO%' THEN SUBSTRING(bt.ticker, 5, LENGTH(bt.ticker) - 12) || 'Y'
        WHEN bt.ticker LIKE 'USSO%' THEN SUBSTRING(bt.ticker, 5, 1) || 'M'
    END as tenor,
    CASE 
        WHEN bt.ticker = 'USSOA Curncy' THEN 30
        WHEN bt.ticker = 'USSOB Curncy' THEN 60
        WHEN bt.ticker = 'USSOC Curncy' THEN 90
        WHEN bt.ticker = 'USSOD Curncy' THEN 120
        WHEN bt.ticker = 'USSOE Curncy' THEN 150
        WHEN bt.ticker = 'USSOF Curncy' THEN 180
        WHEN bt.ticker = 'USSOG Curncy' THEN 210
        WHEN bt.ticker = 'USSOH Curncy' THEN 240
        WHEN bt.ticker = 'USSOI Curncy' THEN 270
        WHEN bt.ticker = 'USSOJ Curncy' THEN 300
        WHEN bt.ticker = 'USSOK Curncy' THEN 330
        WHEN bt.ticker = 'USSO1 Curncy' THEN 365
        WHEN bt.ticker = 'USSO2 Curncy' THEN 730
        WHEN bt.ticker = 'USSO3 Curncy' THEN 1095
        WHEN bt.ticker = 'USSO4 Curncy' THEN 1460
        WHEN bt.ticker = 'USSO5 Curncy' THEN 1825
        WHEN bt.ticker = 'USSO6 Curncy' THEN 2190
        WHEN bt.ticker = 'USSO7 Curncy' THEN 2555
        WHEN bt.ticker = 'USSO8 Curncy' THEN 2920
        WHEN bt.ticker = 'USSO9 Curncy' THEN 3285
        WHEN bt.ticker = 'USSO10 Curncy' THEN 3650
    END as tenor_days,
    CASE 
        WHEN bt.ticker = 'USSOA Curncy' THEN 1
        WHEN bt.ticker = 'USSOB Curncy' THEN 2
        WHEN bt.ticker = 'USSOC Curncy' THEN 3
        WHEN bt.ticker = 'USSOD Curncy' THEN 4
        WHEN bt.ticker = 'USSOE Curncy' THEN 5
        WHEN bt.ticker = 'USSOF Curncy' THEN 6
        WHEN bt.ticker = 'USSOG Curncy' THEN 7
        WHEN bt.ticker = 'USSOH Curncy' THEN 8
        WHEN bt.ticker = 'USSOI Curncy' THEN 9
        WHEN bt.ticker = 'USSOJ Curncy' THEN 10
        WHEN bt.ticker = 'USSOK Curncy' THEN 11
        WHEN bt.ticker = 'USSO1 Curncy' THEN 12
        WHEN bt.ticker = 'USSO2 Curncy' THEN 13
        WHEN bt.ticker = 'USSO3 Curncy' THEN 14
        WHEN bt.ticker = 'USSO4 Curncy' THEN 15
        WHEN bt.ticker = 'USSO5 Curncy' THEN 16
        WHEN bt.ticker = 'USSO6 Curncy' THEN 17
        WHEN bt.ticker = 'USSO7 Curncy' THEN 18
        WHEN bt.ticker = 'USSO8 Curncy' THEN 19
        WHEN bt.ticker = 'USSO9 Curncy' THEN 20
        WHEN bt.ticker = 'USSO10 Curncy' THEN 21
    END as sequence_order
FROM bloomberg_tickers bt
WHERE bt.ticker IN (
    'USSOA Curncy', 'USSOB Curncy', 'USSOC Curncy', 'USSOD Curncy', 'USSOE Curncy',
    'USSOF Curncy', 'USSOG Curncy', 'USSOH Curncy', 'USSOI Curncy', 'USSOJ Curncy',
    'USSOK Curncy', 'USSO1 Curncy', 'USSO2 Curncy', 'USSO3 Curncy', 'USSO4 Curncy',
    'USSO5 Curncy', 'USSO6 Curncy', 'USSO7 Curncy', 'USSO8 Curncy', 'USSO9 Curncy',
    'USSO10 Curncy'
)
ON CONFLICT (curve_id, ticker_id) DO UPDATE SET tenor_days = EXCLUDED.tenor_days;

-- Verify the insertion
SELECT 
    rcd.curve_name,
    bt.ticker,
    rcm.tenor,
    rcm.tenor_days,
    rcm.sequence_order
FROM rate_curve_definitions rcd
JOIN rate_curve_memberships rcm ON rcd.id = rcm.curve_id
JOIN bloomberg_tickers bt ON rcm.ticker_id = bt.id
WHERE rcd.curve_name = 'USD_OIS'
ORDER BY rcm.sequence_order;