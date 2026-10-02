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

-- Outbound webhooks (PRD ТЗ№1 §37).
CREATE TABLE webhook_endpoints (
	id BIGINT NOT NULL AUTO_INCREMENT,
	url VARCHAR(500) NOT NULL,
	description VARCHAR(200),
	secret VARCHAR(64) NOT NULL,
	events TEXT NOT NULL,
	is_active TINYINT(1) NOT NULL,
	last_delivery_at DATETIME,
	last_status_code INTEGER,
	last_error VARCHAR(300),
	created_at DATETIME NOT NULL DEFAULT now(),
	updated_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;

-- Abandoned-cart reminder bookkeeping (PRD ТЗ№1 §39).
ALTER TABLE carts ADD COLUMN abandoned_email_sent_at DATETIME NULL;

-- Product page content and SEO fields (PRD ТЗ№1 §29-30), also per language.
ALTER TABLE products
    ADD COLUMN seo_title VARCHAR(255) NULL,
    ADD COLUMN meta_description VARCHAR(320) NULL,
    ADD COLUMN advantages TEXT NULL,
    ADD COLUMN usage_scenarios TEXT NULL,
    ADD COLUMN instructions TEXT NULL,
    ADD COLUMN material_info TEXT NULL;
ALTER TABLE product_translations
    ADD COLUMN seo_title VARCHAR(255) NULL,
    ADD COLUMN meta_description VARCHAR(320) NULL,
    ADD COLUMN advantages TEXT NULL,
    ADD COLUMN usage_scenarios TEXT NULL,
    ADD COLUMN instructions TEXT NULL,
    ADD COLUMN material_info TEXT NULL;

-- Photos attached to reviews (PRD ТЗ№1 §32): JSON list of image URLs.
ALTER TABLE reviews ADD COLUMN image_urls TEXT NULL;

-- Stock transfers between warehouses and manual corrections (PRD ТЗ№1 §33).
CREATE TABLE stock_movements (
	id BIGINT NOT NULL AUTO_INCREMENT,
	movement_type VARCHAR(20) NOT NULL,
	sku_id BIGINT NOT NULL,
	from_warehouse_id BIGINT,
	to_warehouse_id BIGINT,
	quantity INTEGER NOT NULL,
	note VARCHAR(300),
	created_by_user_id BIGINT,
	created_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id),
	FOREIGN KEY(sku_id) REFERENCES skus (id),
	FOREIGN KEY(from_warehouse_id) REFERENCES warehouses (id),
	FOREIGN KEY(to_warehouse_id) REFERENCES warehouses (id),
	FOREIGN KEY(created_by_user_id) REFERENCES users (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;
CREATE INDEX ix_stock_movements_sku_id ON stock_movements (sku_id);

-- Promo codes limited to delivery countries / named customers (PRD ТЗ№1 §23).
ALTER TABLE promo_codes
    ADD COLUMN countries TEXT NULL,
    ADD COLUMN customer_ids TEXT NULL;

-- Contents of set / pack SKUs (PRD ТЗ№1 §7).
CREATE TABLE sku_bundle_items (
	id BIGINT NOT NULL AUTO_INCREMENT,
	bundle_sku_id BIGINT NOT NULL,
	component_sku_id BIGINT NOT NULL,
	quantity INTEGER NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_sku_bundle_items_pair UNIQUE (bundle_sku_id, component_sku_id),
	FOREIGN KEY(bundle_sku_id) REFERENCES skus (id) ON DELETE CASCADE,
	FOREIGN KEY(component_sku_id) REFERENCES skus (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;
CREATE INDEX ix_sku_bundle_items_bundle_sku_id ON sku_bundle_items (bundle_sku_id);

-- Loyalty programme (PRD ТЗ№1 §11, §62).
ALTER TABLE orders
    ADD COLUMN loyalty_points_used INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN loyalty_discount_amount DECIMAL(12, 2) NOT NULL DEFAULT 0;
CREATE TABLE loyalty_settings (
	id BIGINT NOT NULL,
	enabled TINYINT(1) NOT NULL,
	earn_per_usd DECIMAL(8, 2) NOT NULL,
	point_value_usd DECIMAL(8, 4) NOT NULL,
	max_redeem_percent INTEGER NOT NULL,
	updated_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;
CREATE TABLE loyalty_transactions (
	id BIGINT NOT NULL AUTO_INCREMENT,
	user_id BIGINT NOT NULL,
	kind VARCHAR(20) NOT NULL,
	points INTEGER NOT NULL,
	order_id BIGINT,
	note VARCHAR(300),
	created_by_user_id BIGINT,
	created_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id),
	CONSTRAINT uq_loyalty_order_kind UNIQUE (order_id, kind),
	FOREIGN KEY(user_id) REFERENCES users (id),
	FOREIGN KEY(order_id) REFERENCES orders (id),
	FOREIGN KEY(created_by_user_id) REFERENCES users (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;
CREATE INDEX ix_loyalty_transactions_user_id ON loyalty_transactions (user_id);

-- Per-market product assortment (PRD ТЗ№1 §16): JSON lists of country names, NULL = no restriction.
ALTER TABLE products
    ADD COLUMN sold_in_countries TEXT NULL,
    ADD COLUMN hidden_in_countries TEXT NULL;

-- Web push subscriptions (PRD ТЗ№1 §38-39).
CREATE TABLE push_subscriptions (
	id BIGINT NOT NULL AUTO_INCREMENT,
	user_id BIGINT NOT NULL,
	endpoint VARCHAR(500) NOT NULL,
	p256dh VARCHAR(255) NOT NULL,
	auth VARCHAR(100) NOT NULL,
	user_agent VARCHAR(200),
	created_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id),
	UNIQUE (endpoint),
	FOREIGN KEY(user_id) REFERENCES users (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;
CREATE INDEX ix_push_subscriptions_user_id ON push_subscriptions (user_id);

-- Whether the visitor allowed analytics / ad measurement when ordering (purchase events to GA4 / Meta).
ALTER TABLE orders ADD COLUMN ads_consent TINYINT(1) NOT NULL DEFAULT 0;

-- Loyalty: which customer types take part, point expiry, and tiers (decided in Admin > Loyalty).
ALTER TABLE loyalty_settings
    ADD COLUMN eligible_customer_types VARCHAR(120) NOT NULL DEFAULT 'retail',
    ADD COLUMN expiry_days INTEGER NOT NULL DEFAULT 0;
CREATE TABLE loyalty_tiers (
	id BIGINT NOT NULL AUTO_INCREMENT,
	name VARCHAR(60) NOT NULL,
	min_points_earned INTEGER NOT NULL,
	earn_multiplier DECIMAL(4, 2) NOT NULL,
	PRIMARY KEY (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;

-- Newsletter campaigns sent from the admin panel.
CREATE TABLE newsletter_campaigns (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	subject VARCHAR(200) NOT NULL, 
	body TEXT NOT NULL, 
	locale VARCHAR(5), 
	recipients_total INTEGER NOT NULL, 
	sent_count INTEGER NOT NULL, 
	created_by_user_id BIGINT, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(created_by_user_id) REFERENCES users (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;

-- Admin-editable storefront text and per-page SEO tags (Admin > Landing page, Admin > SEO).
CREATE TABLE content_overrides (
	id BIGINT NOT NULL AUTO_INCREMENT,
	text_key VARCHAR(120) NOT NULL,
	locale VARCHAR(5) NOT NULL,
	value TEXT NOT NULL,
	updated_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id),
	CONSTRAINT uq_content_overrides_key_locale UNIQUE (text_key, locale)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE seo_meta (
	id BIGINT NOT NULL AUTO_INCREMENT,
	path VARCHAR(255) NOT NULL,
	locale VARCHAR(5) NOT NULL,
	title VARCHAR(255),
	description VARCHAR(500),
	image_url VARCHAR(500),
	noindex BOOL NOT NULL DEFAULT 0,
	updated_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id),
	CONSTRAINT uq_seo_meta_path_locale UNIQUE (path, locale)
)CHARSET=utf8mb4 ENGINE=InnoDB;
