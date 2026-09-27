-- Incremental migration for this session's backend work, to run against an
-- existing MariaDB database that already has app/migration_new_tables.sql
-- applied. For a brand-new database, use app/schema_mariadb.sql instead
-- (it already includes everything below).
--
-- Not run against a real MariaDB instance (unreachable from this dev
-- machine — see TODO.md); verified only by compiling equivalent DDL via
-- SQLAlchemy's MySQL dialect and by running the full test suite against
-- SQLite. Re-verify on staging before production.

ALTER TABLE orders
    ADD COLUMN reservation_expires_at DATETIME NULL,
    ADD COLUMN tax_amount DECIMAL(12, 2) NOT NULL DEFAULT 0;

ALTER TABLE users
    ADD COLUMN email_verified BOOL NOT NULL DEFAULT FALSE,
    ADD COLUMN mfa_secret VARCHAR(32) NULL,
    ADD COLUMN mfa_enabled BOOL NOT NULL DEFAULT FALSE;

ALTER TABLE quote_requests
    ADD COLUMN order_id BIGINT NULL,
    ADD FOREIGN KEY (order_id) REFERENCES orders (id);

CREATE TABLE refunds (
	id BIGINT NOT NULL AUTO_INCREMENT,
	order_id BIGINT NOT NULL,
	amount DECIMAL(12, 2) NOT NULL,
	currency VARCHAR(3) NOT NULL,
	reason TEXT,
	status VARCHAR(20) NOT NULL,
	provider VARCHAR(20) NOT NULL,
	provider_refund_id VARCHAR(255),
	failure_reason TEXT,
	created_by_user_id BIGINT,
	created_at DATETIME NOT NULL DEFAULT now(),
	completed_at DATETIME,
	PRIMARY KEY (id),
	FOREIGN KEY(order_id) REFERENCES orders (id),
	FOREIGN KEY(created_by_user_id) REFERENCES users (id)
)ENGINE=InnoDB CHARSET=utf8mb4;

CREATE TABLE email_verification_tokens (
	id BIGINT NOT NULL AUTO_INCREMENT,
	user_id BIGINT NOT NULL,
	token_hash VARCHAR(64) NOT NULL,
	expires_at DATETIME NOT NULL,
	used_at DATETIME,
	created_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id),
	UNIQUE (token_hash)
)ENGINE=InnoDB CHARSET=utf8mb4;

CREATE TABLE notification_templates (
	id BIGINT NOT NULL AUTO_INCREMENT,
	event VARCHAR(50) NOT NULL,
	locale VARCHAR(5) NOT NULL,
	channel VARCHAR(20) NOT NULL,
	subject VARCHAR(255),
	body TEXT NOT NULL,
	is_active BOOL NOT NULL,
	created_at DATETIME NOT NULL DEFAULT now(),
	updated_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id),
	CONSTRAINT uq_notification_template_event_locale_channel UNIQUE (event, locale, channel)
)ENGINE=InnoDB CHARSET=utf8mb4;

CREATE TABLE tax_rules (
	id BIGINT NOT NULL AUTO_INCREMENT,
	country VARCHAR(100) NOT NULL,
	customer_type VARCHAR(20) NOT NULL,
	tax_type VARCHAR(30) NOT NULL,
	rate DECIMAL(5, 2) NOT NULL,
	is_active BOOL NOT NULL,
	created_at DATETIME NOT NULL DEFAULT now(),
	updated_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id),
	CONSTRAINT uq_tax_rules_country_customer_type_tax_type UNIQUE (country, customer_type, tax_type)
)ENGINE=InnoDB CHARSET=utf8mb4;

CREATE TABLE warehouses (
	id BIGINT NOT NULL AUTO_INCREMENT,
	name VARCHAR(255) NOT NULL,
	country VARCHAR(100) NOT NULL,
	address TEXT,
	priority INTEGER NOT NULL,
	is_active BOOL NOT NULL,
	created_at DATETIME NOT NULL DEFAULT now(),
	updated_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id)
)ENGINE=InnoDB CHARSET=utf8mb4;

-- Seed one warehouse so existing `inventory` rows (currently one per SKU,
-- with no warehouse concept) have somewhere to point at.
INSERT INTO warehouses (name, country, priority, is_active, created_at, updated_at)
VALUES ('Main Warehouse', 'Uzbekistan', 1, 1, NOW(), NOW());

ALTER TABLE inventory ADD COLUMN warehouse_id BIGINT NULL;
UPDATE inventory SET warehouse_id = (SELECT id FROM warehouses ORDER BY id LIMIT 1) WHERE warehouse_id IS NULL;
ALTER TABLE inventory MODIFY COLUMN warehouse_id BIGINT NOT NULL;
ALTER TABLE inventory ADD CONSTRAINT fk_inventory_warehouse FOREIGN KEY (warehouse_id) REFERENCES warehouses (id);
-- The old `inventory.sku_id` UNIQUE constraint must be dropped before adding
-- the new (sku_id, warehouse_id) one below, or every row will collide on
-- the still-present old constraint. Run `SHOW INDEX FROM inventory;` first
-- to find its actual name on your database (auto-generated names vary) —
-- not run against a real MariaDB instance from here, so it isn't hardcoded
-- below as a guess.
-- ALTER TABLE inventory DROP INDEX <old_sku_id_unique_index_name>;
ALTER TABLE inventory ADD CONSTRAINT uq_inventory_sku_warehouse UNIQUE (sku_id, warehouse_id);

-- order_items: purely additive, records which warehouse fulfilled each line
-- (app/services/order_service.py::_reserve_stock()).
ALTER TABLE order_items ADD COLUMN warehouse_id BIGINT NULL;
ALTER TABLE order_items ADD CONSTRAINT fk_order_items_warehouse FOREIGN KEY (warehouse_id) REFERENCES warehouses (id);

CREATE TABLE analytics_events (
	id BIGINT NOT NULL AUTO_INCREMENT,
	event_name VARCHAR(50) NOT NULL,
	user_id BIGINT,
	session_id VARCHAR(64),
	properties TEXT,
	created_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id)
)ENGINE=InnoDB CHARSET=utf8mb4;

CREATE TABLE integration_logs (
	id BIGINT NOT NULL AUTO_INCREMENT,
	integration VARCHAR(50) NOT NULL,
	operation VARCHAR(50) NOT NULL,
	direction VARCHAR(10) NOT NULL,
	internal_entity VARCHAR(50) NOT NULL,
	internal_id BIGINT NOT NULL,
	external_id VARCHAR(255),
	request_id VARCHAR(64),
	status VARCHAR(20) NOT NULL,
	error_code VARCHAR(100),
	error_message TEXT,
	attempt INTEGER NOT NULL,
	created_at DATETIME NOT NULL DEFAULT now(),
	completed_at DATETIME,
	PRIMARY KEY (id)
)ENGINE=InnoDB CHARSET=utf8mb4;
