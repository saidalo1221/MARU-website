-- Incremental migration for this session's backend work: admin-panel
-- email-code 2FA, site content management (About/Contact/Location), and
-- map-picked customer address coordinates. Run against an existing MariaDB
-- database that already has app/migration_new_tables.sql,
-- app/migration_2026_session2.sql, and app/migration_2026_session3.sql
-- applied. For a brand-new database, use app/schema_mariadb.sql instead (it
-- already includes everything below).
--
-- Not run against a real MariaDB instance (unreachable from this dev
-- machine — see TODO.md); DDL generated directly from the SQLAlchemy models
-- via CreateTable(...).compile(dialect=mysql.dialect()), and verified by
-- running Base.metadata.create_all() / ALTER TABLE against SQLite. Re-verify
-- on staging before production.

ALTER TABLE users ADD COLUMN admin_mfa_verified_until DATETIME;

ALTER TABLE addresses ADD COLUMN latitude FLOAT;
ALTER TABLE addresses ADD COLUMN longitude FLOAT;

CREATE TABLE admin_login_codes (
	id BIGINT NOT NULL AUTO_INCREMENT,
	user_id BIGINT NOT NULL,
	code_hash VARCHAR(64) NOT NULL,
	expires_at DATETIME NOT NULL,
	used_at DATETIME,
	created_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id)
)ENGINE=InnoDB CHARSET=utf8mb4;

CREATE TABLE site_settings (
	id BIGINT NOT NULL AUTO_INCREMENT,
	phone VARCHAR(30),
	email VARCHAR(255),
	address VARCHAR(500),
	latitude FLOAT,
	longitude FLOAT,
	about_title VARCHAR(255),
	about_body TEXT,
	updated_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id)
)ENGINE=InnoDB CHARSET=utf8mb4;

CREATE TABLE site_settings_translations (
	id BIGINT NOT NULL AUTO_INCREMENT,
	site_settings_id BIGINT NOT NULL,
	locale VARCHAR(10) NOT NULL,
	address VARCHAR(500),
	about_title VARCHAR(255),
	about_body TEXT,
	PRIMARY KEY (id),
	CONSTRAINT uq_site_settings_translations_settings_locale UNIQUE (site_settings_id, locale),
	FOREIGN KEY(site_settings_id) REFERENCES site_settings (id) ON DELETE CASCADE
)ENGINE=InnoDB CHARSET=utf8mb4;
