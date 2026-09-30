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
