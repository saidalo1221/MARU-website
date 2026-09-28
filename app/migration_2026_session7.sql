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
