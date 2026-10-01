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
