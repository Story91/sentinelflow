-- PostgreSQL reference schema. Store tokens, not raw customer PII.
CREATE TABLE IF NOT EXISTS transaction_events (
    transaction_id TEXT PRIMARY KEY,
    customer_token TEXT NOT NULL,
    event_time TIMESTAMPTZ NOT NULL,
    amount NUMERIC(18, 2) NOT NULL CHECK (amount > 0),
    currency CHAR(3) NOT NULL,
    merchant_category TEXT NOT NULL,
    country CHAR(2) NOT NULL,
    device_trust_score DOUBLE PRECISION NOT NULL CHECK (device_trust_score BETWEEN 0 AND 1),
    account_age_days INTEGER NOT NULL CHECK (account_age_days >= 0),
    is_new_device BOOLEAN NOT NULL,
    velocity_1h INTEGER NOT NULL CHECK (velocity_1h >= 0),
    distance_km DOUBLE PRECISION NOT NULL CHECK (distance_km >= 0),
    chargeback_history INTEGER NOT NULL CHECK (chargeback_history >= 0),
    label SMALLINT CHECK (label IN (0, 1)),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_transaction_events_event_time ON transaction_events (event_time);
CREATE INDEX IF NOT EXISTS idx_transaction_events_customer_time ON transaction_events (customer_token, event_time);

CREATE TABLE IF NOT EXISTS model_decisions (
    request_id TEXT PRIMARY KEY,
    transaction_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    risk_score DOUBLE PRECISION NOT NULL CHECK (risk_score BETWEEN 0 AND 1),
    decision TEXT NOT NULL CHECK (decision IN ('approve', 'review')),
    decided_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

