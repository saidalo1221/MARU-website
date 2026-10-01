CREATE TABLE audit_logs (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	user_id BIGINT, 
	action VARCHAR(50) NOT NULL, 
	entity VARCHAR(50) NOT NULL, 
	entity_id VARCHAR(50), 
	old_value TEXT, 
	new_value TEXT, 
	ip_address VARCHAR(45), 
	request_id VARCHAR(64), 
	created_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE categories (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	parent_id BIGINT, 
	name VARCHAR(255) NOT NULL, 
	slug VARCHAR(255) NOT NULL, 
	description TEXT, 
	seo_content TEXT, 
	image_url VARCHAR(500), 
	created_at DATETIME NOT NULL DEFAULT now(), 
	updated_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(parent_id) REFERENCES categories (id), 
	UNIQUE (slug)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE exchange_rates (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	currency VARCHAR(3) NOT NULL, 
	units_per_usd DECIMAL(18, 6) NOT NULL, 
	updated_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	UNIQUE (currency)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE integration_logs (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	integration VARCHAR(50) NOT NULL, 
	operation VARCHAR(50) NOT NULL, 
	direction VARCHAR(10) NOT NULL, 
	internal_entity VARCHAR(50) NOT NULL, 
	internal_id BIGINT NOT NULL, 
	external_id VARCHAR(255), 
	request_id VARCHAR(64), 
	status VARCHAR(20) NOT NULL, 
	error_code VARCHAR(100), 
	error_message TEXT, 
	attempt INTEGER NOT NULL, 
	duration_ms INTEGER, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	completed_at DATETIME, 
	PRIMARY KEY (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE notification_templates (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	event VARCHAR(50) NOT NULL, 
	locale VARCHAR(5) NOT NULL, 
	channel VARCHAR(20) NOT NULL, 
	subject VARCHAR(255), 
	body TEXT NOT NULL, 
	is_active BOOL NOT NULL, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	updated_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	CONSTRAINT uq_notification_template_event_locale_channel UNIQUE (event, locale, channel)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE promo_codes (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	code VARCHAR(50) NOT NULL, 
	discount_type VARCHAR(20) NOT NULL, 
	discount_value DECIMAL(12, 2) NOT NULL, 
	currency VARCHAR(3), 
	min_order_amount DECIMAL(12, 2) NOT NULL, 
	max_uses INTEGER, 
	used_count INTEGER NOT NULL, 
	valid_from DATETIME, 
	valid_until DATETIME, 
	is_active BOOL NOT NULL, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	updated_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	UNIQUE (code)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE shipping_rates (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	country VARCHAR(100) NOT NULL, 
	delivery_method VARCHAR(50) NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	base_fee DECIMAL(12, 2) NOT NULL, 
	per_kg_fee DECIMAL(12, 2) NOT NULL, 
	free_shipping_threshold DECIMAL(12, 2), 
	min_delivery_days INTEGER, 
	max_delivery_days INTEGER, 
	is_active BOOL NOT NULL, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	updated_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	CONSTRAINT uq_shipping_rates_country_method UNIQUE (country, delivery_method)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE tax_rules (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	country VARCHAR(100) NOT NULL, 
	region VARCHAR(100) NOT NULL DEFAULT '*', 
	customer_type VARCHAR(20) NOT NULL, 
	tax_type VARCHAR(30) NOT NULL, 
	min_order_amount DECIMAL(12, 2) NOT NULL DEFAULT 0, 
	rate DECIMAL(5, 2) NOT NULL, 
	is_active BOOL NOT NULL, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	updated_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	CONSTRAINT uq_tax_rules_lookup UNIQUE (country, region, customer_type, tax_type, min_order_amount)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE users (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	email VARCHAR(255) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	first_name VARCHAR(100), 
	last_name VARCHAR(100), 
	phone VARCHAR(30), 
	`role` VARCHAR(30) NOT NULL, 
	customer_type VARCHAR(20) NOT NULL, 
	is_active BOOL NOT NULL, 
	email_verified BOOL NOT NULL, 
	mfa_secret VARCHAR(32),
	mfa_enabled BOOL NOT NULL,
	admin_mfa_verified_until DATETIME,
	failed_login_attempts INTEGER NOT NULL DEFAULT 0,
	locked_until DATETIME,
	created_at DATETIME NOT NULL DEFAULT now(),
	updated_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id),
	UNIQUE (email)
)CHARSET=utf8mb4 ENGINE=InnoDB;

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

CREATE TABLE warehouses (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	name VARCHAR(255) NOT NULL, 
	country VARCHAR(100) NOT NULL,
	address TEXT,
	latitude FLOAT,
	longitude FLOAT,
	priority INTEGER NOT NULL,
	is_active BOOL NOT NULL,
	created_at DATETIME NOT NULL DEFAULT now(),
	updated_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE addresses (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	user_id BIGINT NOT NULL, 
	label VARCHAR(50), 
	first_name VARCHAR(100) NOT NULL, 
	last_name VARCHAR(100) NOT NULL, 
	phone VARCHAR(30) NOT NULL, 
	country VARCHAR(100) NOT NULL, 
	region VARCHAR(100), 
	city VARCHAR(100) NOT NULL, 
	address_line VARCHAR(255) NOT NULL, 
	postal_code VARCHAR(20) NOT NULL,
	is_default BOOL NOT NULL,
	latitude FLOAT,
	longitude FLOAT,
	created_at DATETIME NOT NULL DEFAULT now(),
	updated_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE analytics_events (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	event_name VARCHAR(50) NOT NULL, 
	user_id BIGINT, 
	session_id VARCHAR(64), 
	properties TEXT, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE carts (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	user_id BIGINT, 
	token VARCHAR(64), 
	currency VARCHAR(3) NOT NULL, 
	is_active BOOL NOT NULL, 
	converted_at DATETIME, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	updated_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	UNIQUE (token)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE category_translations (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	category_id BIGINT NOT NULL, 
	locale VARCHAR(10) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	description TEXT, 
	seo_content TEXT, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_category_translations_category_locale UNIQUE (category_id, locale), 
	FOREIGN KEY(category_id) REFERENCES categories (id) ON DELETE CASCADE
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE email_verification_tokens (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	user_id BIGINT NOT NULL, 
	token_hash VARCHAR(64) NOT NULL, 
	expires_at DATETIME NOT NULL, 
	used_at DATETIME, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	UNIQUE (token_hash)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE password_reset_tokens (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	user_id BIGINT NOT NULL, 
	token_hash VARCHAR(64) NOT NULL, 
	expires_at DATETIME NOT NULL, 
	used_at DATETIME, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	UNIQUE (token_hash)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE products (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	category_id BIGINT NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	slug VARCHAR(255) NOT NULL, 
	volume_ml INTEGER NOT NULL, 
	material VARCHAR(50) NOT NULL, 
	shape VARCHAR(100), 
	purpose VARCHAR(255), 
	length_mm INTEGER, 
	width_mm INTEGER, 
	height_mm INTEGER, 
	weight_g INTEGER, 
	description TEXT,
	country_of_origin VARCHAR(100),
	min_order_quantity INTEGER NOT NULL,
	badge_mode VARCHAR(10) NOT NULL DEFAULT 'auto',
	badge_new BOOLEAN,
	badge_sale BOOLEAN,
	badge_bestseller BOOLEAN,
	created_at DATETIME NOT NULL DEFAULT now(),
	updated_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id),
	CONSTRAINT ck_products_volume_ml CHECK (volume_ml IN (350, 470, 800, 1000, 1900)),
	CONSTRAINT ck_products_material CHECK (material = 'polypropylene'),
	CONSTRAINT ck_products_badge_mode CHECK (badge_mode IN ('auto', 'manual')),
	FOREIGN KEY(category_id) REFERENCES categories (id),
	UNIQUE (slug)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE orders (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	order_number VARCHAR(50) NOT NULL, 
	user_id BIGINT, 
	guest_order_token VARCHAR(64), 
	idempotency_key VARCHAR(64), 
	cart_id BIGINT, 
	promo_code_id BIGINT, 
	promo_code_snapshot VARCHAR(50), 
	status VARCHAR(20) NOT NULL, 
	reservation_expires_at DATETIME, 
	customer_type_snapshot VARCHAR(20) NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	subtotal_amount DECIMAL(12, 2) NOT NULL, 
	discount_amount DECIMAL(12, 2) NOT NULL, 
	tax_amount DECIMAL(12, 2) NOT NULL, 
	delivery_amount DECIMAL(12, 2) NOT NULL, 
	total_amount DECIMAL(12, 2) NOT NULL, 
	order_type VARCHAR(20) NOT NULL, 
	first_name VARCHAR(100) NOT NULL, 
	last_name VARCHAR(100) NOT NULL, 
	phone VARCHAR(30) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	country VARCHAR(100) NOT NULL, 
	region VARCHAR(100), 
	city VARCHAR(100) NOT NULL, 
	address_line VARCHAR(255) NOT NULL, 
	postal_code VARCHAR(20) NOT NULL, 
	delivery_method VARCHAR(50) NOT NULL, 
	payment_method VARCHAR(50) NOT NULL, 
	payment_status VARCHAR(24) NOT NULL DEFAULT 'created', 
	language VARCHAR(5), 
	whatsapp_opt_in TINYINT(1) NOT NULL DEFAULT 0, 
	source VARCHAR(20) NOT NULL, 
	company_name VARCHAR(255), 
	company_reg_number VARCHAR(100), 
	company_tax_number VARCHAR(100), 
	company_address VARCHAR(255), 
	contact_person VARCHAR(255), 
	payment_reference VARCHAR(255), 
	crm_deal_id VARCHAR(50), 
	notes TEXT, 
	attribution TEXT, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	updated_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	UNIQUE (order_number), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	UNIQUE (guest_order_token), 
	UNIQUE (idempotency_key), 
	FOREIGN KEY(cart_id) REFERENCES carts (id), 
	FOREIGN KEY(promo_code_id) REFERENCES promo_codes (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE product_translations (
	id BIGINT NOT NULL AUTO_INCREMENT,
	product_id BIGINT NOT NULL,
	locale VARCHAR(10) NOT NULL,
	name VARCHAR(255) NOT NULL,
	description TEXT,
	shape VARCHAR(100),
	purpose VARCHAR(255),
	country_of_origin VARCHAR(100),
	PRIMARY KEY (id),
	CONSTRAINT uq_product_translations_product_locale UNIQUE (product_id, locale),
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE CASCADE
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE product_variants (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	product_id BIGINT NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	color VARCHAR(100) NOT NULL, 
	color_hex VARCHAR(7), 
	photo_url VARCHAR(500), 
	is_active BOOL NOT NULL, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	updated_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id),
	FOREIGN KEY(product_id) REFERENCES products (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE variant_images (
	id BIGINT NOT NULL AUTO_INCREMENT,
	variant_id BIGINT NOT NULL,
	image_url VARCHAR(500) NOT NULL,
	sort_order INTEGER NOT NULL DEFAULT 0,
	created_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id),
	FOREIGN KEY(variant_id) REFERENCES product_variants (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE reviews (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	user_id BIGINT NOT NULL, 
	product_id BIGINT NOT NULL, 
	rating SMALLINT NOT NULL, 
	content TEXT, 
	status VARCHAR(20) NOT NULL, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	CONSTRAINT uq_review_user_product UNIQUE (user_id, product_id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE CASCADE
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE click_transactions (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	click_trans_id VARCHAR(50) NOT NULL, 
	order_id BIGINT NOT NULL, 
	amount DECIMAL(12, 2) NOT NULL, 
	action INTEGER NOT NULL, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	UNIQUE (click_trans_id), 
	FOREIGN KEY(order_id) REFERENCES orders (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE order_status_history (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	order_id BIGINT NOT NULL, 
	from_status VARCHAR(20), 
	to_status VARCHAR(20) NOT NULL, 
	changed_by_user_id BIGINT, 
	note TEXT, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id), 
	FOREIGN KEY(changed_by_user_id) REFERENCES users (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE payme_transactions (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	payme_id VARCHAR(50) NOT NULL, 
	order_id BIGINT NOT NULL, 
	amount_tiyin BIGINT NOT NULL, 
	payme_time_ms BIGINT NOT NULL, 
	state INTEGER NOT NULL, 
	reason INTEGER, 
	create_time_ms BIGINT NOT NULL, 
	perform_time_ms BIGINT NOT NULL, 
	cancel_time_ms BIGINT NOT NULL, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	UNIQUE (payme_id), 
	FOREIGN KEY(order_id) REFERENCES orders (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE quote_requests (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	rfq_number VARCHAR(30), 
	request_type VARCHAR(20) NOT NULL, 
	user_id BIGINT, 
	order_id BIGINT, 
	name VARCHAR(200) NOT NULL, 
	company VARCHAR(255), 
	country VARCHAR(100) NOT NULL, 
	city VARCHAR(100), 
	email VARCHAR(255) NOT NULL, 
	phone VARCHAR(30), 
	products TEXT, 
	quantity VARCHAR(100), 
	comment TEXT, 
	source VARCHAR(20) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	proposed_price DECIMAL(12, 2), 
	currency VARCHAR(3), 
	valid_until DATETIME, 
	manager_notes TEXT, 
	crm_lead_id VARCHAR(50), 
	created_at DATETIME NOT NULL DEFAULT now(), 
	updated_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	UNIQUE (rfq_number), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE refunds (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	order_id BIGINT NOT NULL, 
	amount DECIMAL(12, 2) NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	reason TEXT, 
	status VARCHAR(20) NOT NULL, 
	provider VARCHAR(20) NOT NULL, 
	provider_refund_id VARCHAR(255), 
	failure_reason TEXT, 
	created_by_user_id BIGINT, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	completed_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id), 
	FOREIGN KEY(created_by_user_id) REFERENCES users (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE shipments (
	id BIGINT NOT NULL AUTO_INCREMENT,
	order_id BIGINT NOT NULL,
	carrier VARCHAR(100) NOT NULL,
	tracking_number VARCHAR(100),
	tracking_url VARCHAR(500),
	status VARCHAR(20) NOT NULL,
	shipped_at DATETIME,
	delivered_at DATETIME,
	created_by_user_id BIGINT,
	created_at DATETIME NOT NULL DEFAULT now(),
	updated_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id),
	FOREIGN KEY(order_id) REFERENCES orders (id),
	FOREIGN KEY(created_by_user_id) REFERENCES users (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE INDEX ix_shipments_order_id ON shipments (order_id);

CREATE TABLE shipment_events (
	id BIGINT NOT NULL AUTO_INCREMENT,
	shipment_id BIGINT NOT NULL,
	status VARCHAR(20) NOT NULL,
	location VARCHAR(255),
	note TEXT,
	occurred_at DATETIME NOT NULL DEFAULT now(),
	created_by_user_id BIGINT,
	created_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id),
	FOREIGN KEY(shipment_id) REFERENCES shipments (id),
	FOREIGN KEY(created_by_user_id) REFERENCES users (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE INDEX ix_shipment_events_shipment_id ON shipment_events (shipment_id);

CREATE TABLE newsletter_subscribers (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	email VARCHAR(255) NOT NULL, 
	locale VARCHAR(5) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	token VARCHAR(64) NOT NULL, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	confirmed_at DATETIME, 
	unsubscribed_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (email), 
	UNIQUE (token)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE skus (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	variant_id BIGINT NOT NULL, 
	sku_code VARCHAR(100) NOT NULL, 
	barcode VARCHAR(50), 
	retail_price DECIMAL(12, 2) NOT NULL, 
	wholesale_price DECIMAL(12, 2), 
	distributor_price DECIMAL(12, 2), 
	export_price DECIMAL(12, 2), 
	special_price DECIMAL(12, 2), 
	currency VARCHAR(3) NOT NULL, 
	unit_weight_g INTEGER, 
	box_quantity INTEGER, 
	box_weight_g INTEGER, 
	box_length_mm INTEGER, 
	box_width_mm INTEGER, 
	box_height_mm INTEGER, 
	is_active BOOL NOT NULL, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	updated_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(variant_id) REFERENCES product_variants (id), 
	UNIQUE (sku_code), 
	UNIQUE (barcode)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE cart_items (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	cart_id BIGINT NOT NULL, 
	sku_id BIGINT NOT NULL, 
	quantity INTEGER NOT NULL, 
	saved_for_later BOOL NOT NULL DEFAULT false, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	updated_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	CONSTRAINT uq_cart_items_cart_sku UNIQUE (cart_id, sku_id), 
	CONSTRAINT ck_cart_items_quantity_positive CHECK (quantity > 0), 
	FOREIGN KEY(cart_id) REFERENCES carts (id), 
	FOREIGN KEY(sku_id) REFERENCES skus (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE inventory (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	sku_id BIGINT NOT NULL, 
	warehouse_id BIGINT NOT NULL, 
	stock INTEGER NOT NULL, 
	reserved INTEGER NOT NULL, 
	incoming INTEGER NOT NULL, 
	min_stock INTEGER NOT NULL, 
	updated_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	CONSTRAINT uq_inventory_sku_warehouse UNIQUE (sku_id, warehouse_id), 
	FOREIGN KEY(sku_id) REFERENCES skus (id), 
	FOREIGN KEY(warehouse_id) REFERENCES warehouses (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE order_items (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	order_id BIGINT NOT NULL, 
	sku_id BIGINT, 
	warehouse_id BIGINT, 
	sku_code_snapshot VARCHAR(100) NOT NULL, 
	product_name_snapshot VARCHAR(255) NOT NULL, 
	variant_name_snapshot VARCHAR(255), 
	unit_price DECIMAL(12, 2) NOT NULL, 
	quantity INTEGER NOT NULL, 
	line_total DECIMAL(12, 2) NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id), 
	FOREIGN KEY(sku_id) REFERENCES skus (id) ON DELETE SET NULL, 
	FOREIGN KEY(warehouse_id) REFERENCES warehouses (id) ON DELETE SET NULL
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE quantity_price_tiers (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	sku_id BIGINT NOT NULL, 
	min_quantity INTEGER NOT NULL, 
	price DECIMAL(12, 2) NOT NULL, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	CONSTRAINT uq_quantity_price_tiers_sku_min_qty UNIQUE (sku_id, min_quantity), 
	FOREIGN KEY(sku_id) REFERENCES skus (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE wishlist_items (
	id BIGINT NOT NULL AUTO_INCREMENT,
	user_id BIGINT NOT NULL,
	sku_id BIGINT NOT NULL,
	created_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id),
	CONSTRAINT uq_wishlist_user_sku UNIQUE (user_id, sku_id),
	FOREIGN KEY(user_id) REFERENCES users (id),
	FOREIGN KEY(sku_id) REFERENCES skus (id) ON DELETE CASCADE
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE blog_categories (
	id BIGINT NOT NULL AUTO_INCREMENT,
	name VARCHAR(255) NOT NULL,
	slug VARCHAR(255) NOT NULL,
	created_at DATETIME NOT NULL DEFAULT now(),
	updated_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id),
	UNIQUE (slug)
)CHARSET=utf8mb4 ENGINE=InnoDB;

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
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE blog_post_translations (
	id BIGINT NOT NULL AUTO_INCREMENT,
	post_id BIGINT NOT NULL,
	locale VARCHAR(10) NOT NULL,
	slug VARCHAR(255),
	title VARCHAR(255) NOT NULL,
	excerpt TEXT,
	content TEXT NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_blog_post_translations_post_locale UNIQUE (post_id, locale),
	FOREIGN KEY(post_id) REFERENCES blog_posts (id) ON DELETE CASCADE
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE page_sections (
	id BIGINT NOT NULL AUTO_INCREMENT,
	page VARCHAR(30) NOT NULL,
	title VARCHAR(255) NOT NULL,
	body TEXT NOT NULL,
	sort_order INTEGER NOT NULL,
	category VARCHAR(30),
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

CREATE TABLE admin_login_codes (
	id BIGINT NOT NULL AUTO_INCREMENT,
	user_id BIGINT NOT NULL,
	code_hash VARCHAR(64) NOT NULL,
	expires_at DATETIME NOT NULL,
	used_at DATETIME,
	created_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE site_settings (
	id BIGINT NOT NULL AUTO_INCREMENT,
	phone VARCHAR(30),
	email VARCHAR(255),
	address VARCHAR(500),
	latitude FLOAT,
	longitude FLOAT,
	about_title VARCHAR(255),
	about_body TEXT,
	facebook_url VARCHAR(255),
	instagram_url VARCHAR(255),
	telegram_url VARCHAR(255),
	youtube_url VARCHAR(255),
	updated_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;

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
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE about_sections (
	id BIGINT NOT NULL AUTO_INCREMENT,
	title VARCHAR(255) NOT NULL,
	body TEXT NOT NULL,
	sort_order INTEGER NOT NULL,
	created_at DATETIME NOT NULL DEFAULT now(),
	updated_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE about_section_translations (
	id BIGINT NOT NULL AUTO_INCREMENT,
	section_id BIGINT NOT NULL,
	locale VARCHAR(10) NOT NULL,
	title VARCHAR(255) NOT NULL,
	body TEXT NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_about_section_translations_section_locale UNIQUE (section_id, locale),
	FOREIGN KEY(section_id) REFERENCES about_sections (id) ON DELETE CASCADE
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE stock_alerts (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	sku_id BIGINT NOT NULL, 
	user_id BIGINT, 
	email VARCHAR(255) NOT NULL, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	notified_at DATETIME, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_stock_alerts_sku_email UNIQUE (sku_id, email), 
	FOREIGN KEY(sku_id) REFERENCES skus (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;
CREATE INDEX ix_stock_alerts_sku_id ON stock_alerts (sku_id);

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

CREATE TABLE payments (
	id BIGINT NOT NULL AUTO_INCREMENT,
	order_id BIGINT NOT NULL,
	provider VARCHAR(50) NOT NULL,
	provider_transaction_id VARCHAR(255),
	amount DECIMAL(12, 2) NOT NULL,
	currency VARCHAR(3) NOT NULL,
	status VARCHAR(24) NOT NULL,
	idempotency_key VARCHAR(80) NOT NULL,
	paid_at DATETIME,
	created_at DATETIME NOT NULL DEFAULT now(),
	updated_at DATETIME NOT NULL DEFAULT now(),
	PRIMARY KEY (id),
	UNIQUE (idempotency_key),
	FOREIGN KEY(order_id) REFERENCES orders (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;
CREATE INDEX ix_payments_order_id ON payments (order_id);
