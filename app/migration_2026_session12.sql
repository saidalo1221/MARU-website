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
