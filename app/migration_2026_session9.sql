-- Incremental migration: shipments and order tracking. Run against an
-- existing MariaDB database that already has app/migration_new_tables.sql
-- through app/migration_2026_session8.sql applied. For a brand-new
-- database, use app/schema_mariadb.sql instead (already includes
-- everything below).
--
-- Not run against a real MariaDB instance (unreachable from this dev
-- machine); the tables mirror app/models/shipment.py and were created on
-- SQLite by SQLAlchemy. Re-verify on staging before production.

CREATE TABLE shipments (
	id BIGINT NOT NULL AUTO_INCREMENT,
	order_id BIGINT NOT NULL,
	carrier VARCHAR(100) NOT NULL,
	tracking_number VARCHAR(100),
	tracking_url VARCHAR(500),
	status VARCHAR(20) NOT NULL,
	shipped_at DATETIME,
	delivered_at DATETIME,
	created_by_user_id BIGINT,
	created_at DATETIME NOT NULL DEFAULT now(),
	updated_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id),
	FOREIGN KEY(order_id) REFERENCES orders (id),
	FOREIGN KEY(created_by_user_id) REFERENCES users (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;
CREATE INDEX ix_shipments_order_id ON shipments (order_id);

CREATE TABLE shipment_events (
	id BIGINT NOT NULL AUTO_INCREMENT,
	shipment_id BIGINT NOT NULL,
	status VARCHAR(20) NOT NULL,
	location VARCHAR(255),
	note TEXT,
	occurred_at DATETIME NOT NULL DEFAULT now(),
	created_by_user_id BIGINT,
	created_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id),
	FOREIGN KEY(shipment_id) REFERENCES shipments (id),
	FOREIGN KEY(created_by_user_id) REFERENCES users (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;
CREATE INDEX ix_shipment_events_shipment_id ON shipment_events (shipment_id);

-- Checkout idempotency: a retried POST /orders/ with the same Idempotency-Key
-- header returns the original order instead of failing on the used cart.
ALTER TABLE orders ADD COLUMN idempotency_key VARCHAR(64) NULL;
ALTER TABLE orders ADD CONSTRAINT uq_orders_idempotency_key UNIQUE (idempotency_key);

-- Marketing attribution (utm_*, referrer, landing page) captured at checkout.
ALTER TABLE orders ADD COLUMN attribution TEXT NULL;

-- Free-shipping threshold and delivery-time window per shipping rate.
ALTER TABLE shipping_rates ADD COLUMN free_shipping_threshold DECIMAL(12, 2) NULL;
ALTER TABLE shipping_rates ADD COLUMN min_delivery_days INTEGER NULL;
ALTER TABLE shipping_rates ADD COLUMN max_delivery_days INTEGER NULL;

CREATE TABLE newsletter_subscribers (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	email VARCHAR(255) NOT NULL, 
	locale VARCHAR(5) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	token VARCHAR(64) NOT NULL, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	confirmed_at DATETIME, 
	unsubscribed_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (email), 
	UNIQUE (token)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE stock_alerts (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	sku_id BIGINT NOT NULL, 
	user_id BIGINT, 
	email VARCHAR(255) NOT NULL, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	notified_at DATETIME, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_stock_alerts_sku_email UNIQUE (sku_id, email), 
	FOREIGN KEY(sku_id) REFERENCES skus (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;
CREATE INDEX ix_stock_alerts_sku_id ON stock_alerts (sku_id);

-- Save for later (cart lines kept out of totals and checkout).
ALTER TABLE cart_items ADD COLUMN saved_for_later BOOL NOT NULL DEFAULT false;
