-- Create the complete database schema for Bloomberg ticker discovery and curve management

-- Table for storing all discovered Bloomberg tickers
CREATE TABLE IF NOT EXISTS bloomberg_tickers (
    id SERIAL PRIMARY KEY,
    bloomberg_ticker VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    currency VARCHAR(3),
    tenor VARCHAR(10),
    tenor_numeric INTEGER, -- Days to maturity
    category VARCHAR(50), -- e.g., 'money_market', 'swap', 'bond', 'cds'
    subcategory VARCHAR(50), -- More specific classification
    properties JSONB, -- Additional metadata
    is_active BOOLEAN DEFAULT true,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_validated_at TIMESTAMP,
    validation_status VARCHAR(20) DEFAULT 'pending' -- 'valid', 'invalid', 'pending'
);

-- Table for rate curve definitions
CREATE TABLE IF NOT EXISTS rate_curve_definitions (
    id SERIAL PRIMARY KEY,
    curve_name VARCHAR(100) NOT NULL UNIQUE,
    currency_code VARCHAR(3) NOT NULL,
    curve_type VARCHAR(50) NOT NULL, -- 'OIS', 'IRS', 'GOVT', 'CORPORATE', 'CDS', 'INFLATION'
    methodology TEXT, -- Description of curve construction
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for mapping tickers to curves
CREATE TABLE IF NOT EXISTS rate_curve_mappings (
    id SERIAL PRIMARY KEY,
    curve_name VARCHAR(100) NOT NULL,
    bloomberg_ticker VARCHAR(50) NOT NULL,
    sorting_order INTEGER, -- For ordering tickers within a curve
    weight DECIMAL(5,4) DEFAULT 1.0, -- For weighted curve construction
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (curve_name) REFERENCES rate_curve_definitions(curve_name),
    FOREIGN KEY (bloomberg_ticker) REFERENCES bloomberg_tickers(bloomberg_ticker),
    UNIQUE(curve_name, bloomberg_ticker)
);

-- Table for ticker reference (centralized ticker repository)
CREATE TABLE IF NOT EXISTS ticker_reference (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    asset_class VARCHAR(50), -- 'rates', 'credit', 'fx', 'equity', 'commodity'
    currency VARCHAR(3),
    country VARCHAR(3),
    sector VARCHAR(50),
    maturity_date DATE,
    tenor_years DECIMAL(10,4),
    instrument_type VARCHAR(50), -- 'govt_bond', 'corporate_bond', 'swap', 'future', 'option'
    rating VARCHAR(10), -- For corporate bonds/CDS
    properties JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_bloomberg_tickers_currency ON bloomberg_tickers(currency);
CREATE INDEX IF NOT EXISTS idx_bloomberg_tickers_category ON bloomberg_tickers(category);
CREATE INDEX IF NOT EXISTS idx_bloomberg_tickers_tenor_numeric ON bloomberg_tickers(tenor_numeric);
CREATE INDEX IF NOT EXISTS idx_bloomberg_tickers_validation_status ON bloomberg_tickers(validation_status);
CREATE INDEX IF NOT EXISTS idx_rate_curve_definitions_currency ON rate_curve_definitions(currency_code);
CREATE INDEX IF NOT EXISTS idx_rate_curve_definitions_type ON rate_curve_definitions(curve_type);
CREATE INDEX IF NOT EXISTS idx_rate_curve_mappings_curve ON rate_curve_mappings(curve_name);
CREATE INDEX IF NOT EXISTS idx_rate_curve_mappings_ticker ON rate_curve_mappings(bloomberg_ticker);
CREATE INDEX IF NOT EXISTS idx_ticker_reference_currency ON ticker_reference(currency);
CREATE INDEX IF NOT EXISTS idx_ticker_reference_asset_class ON ticker_reference(asset_class);
CREATE INDEX IF NOT EXISTS idx_ticker_reference_instrument_type ON ticker_reference(instrument_type);

-- Create a view for easy curve analysis
CREATE OR REPLACE VIEW curve_summary AS
SELECT 
    rcd.curve_name,
    rcd.currency_code,
    rcd.curve_type,
    COUNT(rcm.bloomberg_ticker) as ticker_count,
    MIN(bt.tenor_numeric) as min_tenor_days,
    MAX(bt.tenor_numeric) as max_tenor_days,
    rcd.is_active
FROM rate_curve_definitions rcd
LEFT JOIN rate_curve_mappings rcm ON rcd.curve_name = rcm.curve_name AND rcm.is_active = true
LEFT JOIN bloomberg_tickers bt ON bt.bloomberg_ticker = rcm.bloomberg_ticker AND bt.is_active = true
WHERE rcd.is_active = true
GROUP BY rcd.curve_name, rcd.currency_code, rcd.curve_type, rcd.is_active
ORDER BY rcd.currency_code, rcd.curve_type;