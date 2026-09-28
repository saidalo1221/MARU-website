-- Incremental migration for this session's backend work. Run against an
-- existing MariaDB database that already has app/migration_new_tables.sql
-- through app/migration_2026_session6.sql applied. For a brand-new
-- database, use app/schema_mariadb.sql instead (already includes
-- everything below).
--
-- Not run against a real MariaDB instance (unreachable from this dev
-- machine — see TODO.md); verified by running the equivalent ALTER TABLE
-- against SQLite. Re-verify on staging before production.

-- Per-locale blog post slugs (falls back to blog_posts.slug when NULL).
ALTER TABLE blog_post_translations ADD COLUMN slug VARCHAR(255);

-- Account lockout after repeated failed logins (customer + admin), and
-- new-device email verification for customer login.
ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER NOT NULL DEFAULT 0;
ALTER TABLE users ADD COLUMN locked_until DATETIME;

CREATE TABLE trusted_devices (
	id BIGINT NOT NULL AUTO_INCREMENT,
	user_id BIGINT NOT NULL,
	device_id VARCHAR(64) NOT NULL,
	created_at DATETIME NOT NULL DEFAULT now(),
	last_used_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id),
	CONSTRAINT uq_trusted_devices_user_device UNIQUE (user_id, device_id),
	FOREIGN KEY(user_id) REFERENCES users (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE login_device_codes (
	id BIGINT NOT NULL AUTO_INCREMENT,
	user_id BIGINT NOT NULL,
	device_id VARCHAR(64) NOT NULL,
	code_hash VARCHAR(64) NOT NULL,
	expires_at DATETIME NOT NULL,
	used_at DATETIME,
	created_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;

-- Admin-editable free-form content sections for the Delivery/Payment/
-- Returns/FAQ/Contact support pages (same pattern as about_sections).
CREATE TABLE page_sections (
	id BIGINT NOT NULL AUTO_INCREMENT,
	page VARCHAR(30) NOT NULL,
	title VARCHAR(255) NOT NULL,
	body TEXT NOT NULL,
	sort_order INTEGER NOT NULL,
	created_at DATETIME NOT NULL DEFAULT now(),
	updated_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE page_section_translations (
	id BIGINT NOT NULL AUTO_INCREMENT,
	section_id BIGINT NOT NULL,
	locale VARCHAR(10) NOT NULL,
	title VARCHAR(255) NOT NULL,
	body TEXT NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_page_section_translations_section_locale UNIQUE (section_id, locale),
	FOREIGN KEY(section_id) REFERENCES page_sections (id) ON DELETE CASCADE
)CHARSET=utf8mb4 ENGINE=InnoDB;
