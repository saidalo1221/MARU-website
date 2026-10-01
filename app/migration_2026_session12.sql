-- Social media links shown in the storefront footer (PRD ТЗ№2 §7).
ALTER TABLE site_settings
    ADD COLUMN facebook_url VARCHAR(255) NULL,
    ADD COLUMN instagram_url VARCHAR(255) NULL,
    ADD COLUMN telegram_url VARCHAR(255) NULL,
    ADD COLUMN youtube_url VARCHAR(255) NULL;
