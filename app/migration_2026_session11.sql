-- Region on saved addresses (selects region tax rules at checkout) and the
-- call duration of integration attempts (health latency metric).
-- Existing rows keep working: both columns are nullable.
ALTER TABLE addresses ADD COLUMN region VARCHAR(100) NULL AFTER country;
ALTER TABLE integration_logs ADD COLUMN duration_ms INTEGER NULL AFTER attempt;
