-- Tax rules: optional region and order-value tiers; orders remember the region.
-- Existing rows keep working: region defaults to '*' (any) and min_order_amount to 0.
ALTER TABLE tax_rules
    ADD COLUMN region VARCHAR(100) NOT NULL DEFAULT '*' AFTER country,
    ADD COLUMN min_order_amount DECIMAL(12, 2) NOT NULL DEFAULT 0 AFTER tax_type,
    DROP INDEX uq_tax_rules_country_customer_type_tax_type,
    ADD CONSTRAINT uq_tax_rules_lookup UNIQUE (country, region, customer_type, tax_type, min_order_amount);

ALTER TABLE orders ADD COLUMN region VARCHAR(100) NULL AFTER country;
