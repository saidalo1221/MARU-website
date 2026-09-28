-- Incremental migration for this session's backend work: translatable
-- Shape/Purpose/Country of origin on products (previously only name and
-- description could be translated). Run against an existing MariaDB
-- database that already has app/migration_new_tables.sql through
-- app/migration_2026_session5.sql applied. For a brand-new database, use
-- app/schema_mariadb.sql instead (it already includes everything below).
--
-- Not run against a real MariaDB instance (unreachable from this dev
-- machine — see TODO.md); verified by running the equivalent ALTER TABLE
-- against SQLite. Re-verify on staging before production.

ALTER TABLE product_translations ADD COLUMN shape VARCHAR(100);
ALTER TABLE product_translations ADD COLUMN purpose VARCHAR(255);
ALTER TABLE product_translations ADD COLUMN country_of_origin VARCHAR(100);
