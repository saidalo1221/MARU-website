-- Incremental migration for this session's backend work (Blog, PRD ТЗ№3
-- §40), to run against an existing MariaDB database that already has
-- app/migration_new_tables.sql and app/migration_2026_session2.sql applied.
-- For a brand-new database, use app/schema_mariadb.sql instead (it already
-- includes everything below).
--
-- Not run against a real MariaDB instance (unreachable from this dev
-- machine — see TODO.md); DDL generated directly from the SQLAlchemy models
-- via CreateTable(...).compile(dialect=mysql.dialect()), and verified by
-- running Base.metadata.create_all() against SQLite. Re-verify on staging
-- before production.

CREATE TABLE blog_categories (
	id BIGINT NOT NULL AUTO_INCREMENT,
	name VARCHAR(255) NOT NULL,
	slug VARCHAR(255) NOT NULL,
	created_at DATETIME NOT NULL DEFAULT now(),
	updated_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id),
	UNIQUE (slug)
)ENGINE=InnoDB CHARSET=utf8mb4;

CREATE TABLE blog_posts (
	id BIGINT NOT NULL AUTO_INCREMENT,
	category_id BIGINT NOT NULL,
	slug VARCHAR(255) NOT NULL,
	title VARCHAR(255) NOT NULL,
	excerpt TEXT,
	content TEXT NOT NULL,
	cover_image_url VARCHAR(500),
	author_name VARCHAR(100),
	is_published BOOL NOT NULL,
	published_at DATETIME,
	created_at DATETIME NOT NULL DEFAULT now(),
	updated_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id),
	FOREIGN KEY(category_id) REFERENCES blog_categories (id),
	UNIQUE (slug)
)ENGINE=InnoDB CHARSET=utf8mb4;

CREATE TABLE blog_post_translations (
	id BIGINT NOT NULL AUTO_INCREMENT,
	post_id BIGINT NOT NULL,
	locale VARCHAR(10) NOT NULL,
	title VARCHAR(255) NOT NULL,
	excerpt TEXT,
	content TEXT NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_blog_post_translations_post_locale UNIQUE (post_id, locale),
	FOREIGN KEY(post_id) REFERENCES blog_posts (id) ON DELETE CASCADE
)ENGINE=InnoDB CHARSET=utf8mb4;
