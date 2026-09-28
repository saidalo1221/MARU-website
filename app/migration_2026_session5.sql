-- Incremental migration for this session's backend work: free-form About Us
-- sections (app/models/about_section.py), replacing the hardcoded
-- History/Company/Production/Equipment/Quality/Products/Markets copy in
-- frontend/src/i18n/translations.js. Run against an existing MariaDB
-- database that already has app/migration_new_tables.sql through
-- app/migration_2026_session4.sql applied. For a brand-new database, use
-- app/schema_mariadb.sql instead (it already includes everything below).
--
-- Not run against a real MariaDB instance (unreachable from this dev
-- machine — see TODO.md); DDL generated directly from the SQLAlchemy models
-- via CreateTable(...).compile(dialect=mysql.dialect()), and verified by
-- running Base.metadata.create_all() against SQLite. Re-verify on staging
-- before production.

CREATE TABLE about_sections (
	id BIGINT NOT NULL AUTO_INCREMENT,
	title VARCHAR(255) NOT NULL,
	body TEXT NOT NULL,
	sort_order INTEGER NOT NULL,
	created_at DATETIME NOT NULL DEFAULT now(),
	updated_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id)
)ENGINE=InnoDB CHARSET=utf8mb4;

CREATE TABLE about_section_translations (
	id BIGINT NOT NULL AUTO_INCREMENT,
	section_id BIGINT NOT NULL,
	locale VARCHAR(10) NOT NULL,
	title VARCHAR(255) NOT NULL,
	body TEXT NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_about_section_translations_section_locale UNIQUE (section_id, locale),
	FOREIGN KEY(section_id) REFERENCES about_sections (id) ON DELETE CASCADE
)ENGINE=InnoDB CHARSET=utf8mb4;
