-- Social media links shown in the storefront footer (PRD ТЗ№2 §7).
ALTER TABLE site_settings
    ADD COLUMN facebook_url VARCHAR(255) NULL,
    ADD COLUMN instagram_url VARCHAR(255) NULL,
    ADD COLUMN telegram_url VARCHAR(255) NULL,
    ADD COLUMN youtube_url VARCHAR(255) NULL;

-- FAQ sections can be grouped by topic (PRD ТЗ№2 §39).
ALTER TABLE page_sections ADD COLUMN category VARCHAR(30) NULL;

-- Category page content and its per-language overrides (PRD ТЗ№2 §10).
ALTER TABLE categories
    ADD COLUMN description TEXT NULL,
    ADD COLUMN seo_content TEXT NULL,
    ADD COLUMN image_url VARCHAR(500) NULL;
ALTER TABLE category_translations
    ADD COLUMN description TEXT NULL,
    ADD COLUMN seo_content TEXT NULL;

-- Audit rows record the caller's IP and the request id (PRD ТЗ№3 §81).
ALTER TABLE audit_logs
    ADD COLUMN ip_address VARCHAR(45) NULL,
    ADD COLUMN request_id VARCHAR(64) NULL;

-- Background job queue and inbound webhook idempotency (PRD ТЗ№3 §88-89, ТЗ№4 §50-54).
CREATE TABLE jobs (
	id BIGINT NOT NULL AUTO_INCREMENT,
	queue VARCHAR(30) NOT NULL,
	job_type VARCHAR(60) NOT NULL,
	payload TEXT NOT NULL,
	status VARCHAR(12) NOT NULL,
	attempts INTEGER NOT NULL,
	max_attempts INTEGER NOT NULL,
	run_at DATETIME NOT NULL DEFAULT now(),
	locked_by VARCHAR(64),
	locked_at DATETIME,
	last_error TEXT,
	dedupe_key VARCHAR(120),
	created_at DATETIME NOT NULL DEFAULT now(),
	finished_at DATETIME,
	PRIMARY KEY (id),
	UNIQUE (dedupe_key)
)CHARSET=utf8mb4 ENGINE=InnoDB;
CREATE INDEX ix_jobs_status ON jobs (status);
CREATE INDEX ix_jobs_run_at ON jobs (run_at);

CREATE TABLE webhook_events (
	id BIGINT NOT NULL AUTO_INCREMENT,
	provider VARCHAR(50) NOT NULL,
	event_id VARCHAR(120) NOT NULL,
	job_id BIGINT,
	received_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id),
	CONSTRAINT uq_webhook_events_provider_event UNIQUE (provider, event_id)
)CHARSET=utf8mb4 ENGINE=InnoDB;

-- Outside-system id mapping (PRD ТЗ№4 §3-5).
CREATE TABLE external_ids (
	id BIGINT NOT NULL AUTO_INCREMENT,
	`system` VARCHAR(40) NOT NULL,
	entity VARCHAR(40) NOT NULL,
	internal_id BIGINT NOT NULL,
	external_id VARCHAR(120) NOT NULL,
	created_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id),
	CONSTRAINT uq_external_ids_internal UNIQUE (`system`, entity, internal_id),
	CONSTRAINT uq_external_ids_external UNIQUE (`system`, entity, external_id)
)CHARSET=utf8mb4 ENGINE=InnoDB;

-- Order documents: invoices, fiscal receipts, shipping and return documents (PRD ТЗ№4 §81-83).
CREATE TABLE order_documents (
	id BIGINT NOT NULL AUTO_INCREMENT,
	order_id BIGINT NOT NULL,
	doc_type VARCHAR(30) NOT NULL,
	status VARCHAR(20) NOT NULL,
	external_id VARCHAR(120),
	filename VARCHAR(255) NOT NULL,
	storage_name VARCHAR(80) NOT NULL,
	content_type VARCHAR(100) NOT NULL,
	size_bytes INTEGER NOT NULL,
	created_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id),
	FOREIGN KEY(order_id) REFERENCES orders (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;
CREATE INDEX ix_order_documents_order_id ON order_documents (order_id);

-- Payments ledger (PRD ТЗ№3 §31, ТЗ№4 §23): one row per payment attempt, orders.payment_status mirrors the latest.
-- NOTE: enum columns store the member NAME in upper case (SQLAlchemy Enum default), e.g. 'CREATED'.
ALTER TABLE orders ADD COLUMN payment_status VARCHAR(24) NOT NULL DEFAULT 'CREATED';

CREATE TABLE payments (
	id BIGINT NOT NULL AUTO_INCREMENT,
	order_id BIGINT NOT NULL,
	provider VARCHAR(50) NOT NULL,
	provider_transaction_id VARCHAR(255),
	amount DECIMAL(12, 2) NOT NULL,
	currency VARCHAR(3) NOT NULL,
	status VARCHAR(24) NOT NULL,
	idempotency_key VARCHAR(80) NOT NULL,
	paid_at DATETIME,
	created_at DATETIME NOT NULL DEFAULT now(),
	updated_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id),
	UNIQUE (idempotency_key),
	FOREIGN KEY(order_id) REFERENCES orders (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;
CREATE INDEX ix_payments_order_id ON payments (order_id);

-- Backfill for orders that exist before the ledger: one payment each, status derived from the order status.
-- (Order paid then cancelled/returned keeps 'paid' - refunds below correct it.)
INSERT INTO payments (order_id, provider, amount, currency, status, idempotency_key, paid_at, created_at, updated_at)
SELECT o.id, o.payment_method, o.total_amount, o.currency,
       CASE o.status
         WHEN 'NEW' THEN 'CREATED'
         WHEN 'PAYMENT_PENDING' THEN 'PENDING'
         WHEN 'PAYMENT_FAILED' THEN 'FAILED'
         WHEN 'CANCELLED' THEN IF(EXISTS(SELECT 1 FROM order_status_history h WHERE h.order_id = o.id AND h.to_status = 'PAID'), 'PAID', 'CANCELLED')
         WHEN 'REFUNDED' THEN 'REFUNDED'
         WHEN 'PARTIALLY_REFUNDED' THEN 'PARTIALLY_REFUNDED'
         ELSE 'PAID'
       END,
       CONCAT('order-', o.id, '-1'),
       (SELECT MIN(h.created_at) FROM order_status_history h WHERE h.order_id = o.id AND h.to_status = 'PAID'),
       o.created_at, o.created_at
FROM orders o
WHERE NOT EXISTS (SELECT 1 FROM payments p WHERE p.order_id = o.id);

UPDATE orders o JOIN payments p ON p.order_id = o.id SET o.payment_status = p.status;

-- WhatsApp updates: checkout language and the customer's opt-in (PRD ТЗ№4 §40-44).
ALTER TABLE orders
    ADD COLUMN language VARCHAR(5) NULL,
    ADD COLUMN whatsapp_opt_in TINYINT(1) NOT NULL DEFAULT 0;

-- Product-level tax classes, promo targeting and per-customer promo limits, per-line tax/discount
-- (PRD ТЗ№3 §74, §23).
ALTER TABLE products ADD COLUMN tax_class VARCHAR(20) NOT NULL DEFAULT 'standard';

ALTER TABLE tax_rules ADD COLUMN tax_class VARCHAR(20) NOT NULL DEFAULT '*';
ALTER TABLE tax_rules DROP INDEX uq_tax_rules_lookup;
ALTER TABLE tax_rules ADD CONSTRAINT uq_tax_rules_lookup
    UNIQUE (country, region, customer_type, tax_type, tax_class, min_order_amount);

ALTER TABLE promo_codes
    ADD COLUMN product_ids TEXT NULL,
    ADD COLUMN category_ids TEXT NULL,
    ADD COLUMN max_uses_per_customer INTEGER NULL;

CREATE TABLE promo_redemptions (
	id BIGINT NOT NULL AUTO_INCREMENT,
	promo_code_id BIGINT NOT NULL,
	order_id BIGINT NOT NULL,
	user_id BIGINT,
	email VARCHAR(255),
	created_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id),
	FOREIGN KEY(promo_code_id) REFERENCES promo_codes (id),
	FOREIGN KEY(order_id) REFERENCES orders (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;
CREATE INDEX ix_promo_redemptions_promo_code_id ON promo_redemptions (promo_code_id);
CREATE INDEX ix_promo_redemptions_user_id ON promo_redemptions (user_id);
CREATE INDEX ix_promo_redemptions_email ON promo_redemptions (email);

ALTER TABLE order_items
    ADD COLUMN discount_amount DECIMAL(12, 2) NOT NULL DEFAULT 0,
    ADD COLUMN tax_amount DECIMAL(12, 2) NOT NULL DEFAULT 0;

-- Existing orders: the whole order tax/discount was not split per line; leave the lines at 0
-- (orders.tax_amount / discount_amount stay authoritative for them).

-- Dashboard inputs: SKU cost (gross profit) and manual marketing spend (CAC / ROAS) (PRD ТЗ№1 §59-60).
ALTER TABLE skus ADD COLUMN cost_price DECIMAL(12, 2) NULL;
ALTER TABLE order_items ADD COLUMN unit_cost_usd DECIMAL(12, 4) NULL;
CREATE TABLE marketing_spend (
	id BIGINT NOT NULL AUTO_INCREMENT,
	month DATE NOT NULL,
	channel VARCHAR(60) NOT NULL,
	amount_usd DECIMAL(12, 2) NOT NULL,
	created_by_user_id BIGINT,
	created_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id),
	FOREIGN KEY(created_by_user_id) REFERENCES users (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;
CREATE INDEX ix_marketing_spend_month ON marketing_spend (month);
