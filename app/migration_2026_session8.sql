-- Incremental migration for this session's backend work. Run against an
-- existing MariaDB database that already has app/migration_new_tables.sql
-- through app/migration_2026_session7.sql applied. For a brand-new
-- database, use app/schema_mariadb.sql instead (already includes
-- everything below).
--
-- Not run against a real MariaDB instance (unreachable from this dev
-- machine — see TODO.md); verified by running the equivalent ALTER TABLE
-- against SQLite. Re-verify on staging before production.

-- Multi-image gallery per product variant (admin can add several photos per
-- color, shown as a big image + scrollable/clickable thumbnails on the
-- product page). ProductVariant.photo_url stays as the single legacy cover.
CREATE TABLE variant_images (
	id BIGINT NOT NULL AUTO_INCREMENT,
	variant_id BIGINT NOT NULL,
	image_url VARCHAR(500) NOT NULL,
	sort_order INTEGER NOT NULL DEFAULT 0,
	created_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id),
	FOREIGN KEY(variant_id) REFERENCES product_variants (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;

-- Product badges (New / Sale / Best Seller). "auto" computes them from
-- created_at / SKU special_price / sales volume; "manual" uses the three
-- override flags below instead — toggled per product by the admin.
ALTER TABLE products ADD COLUMN badge_mode VARCHAR(10) NOT NULL DEFAULT 'auto';
ALTER TABLE products ADD COLUMN badge_new BOOLEAN;
ALTER TABLE products ADD COLUMN badge_sale BOOLEAN;
ALTER TABLE products ADD COLUMN badge_bestseller BOOLEAN;
ALTER TABLE products ADD CONSTRAINT ck_products_badge_mode CHECK (badge_mode IN ('auto', 'manual'));
