CREATE TABLE audit_logs (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	user_id BIGINT, 
	action VARCHAR(50) NOT NULL, 
	entity VARCHAR(50) NOT NULL, 
	entity_id VARCHAR(50), 
	old_value TEXT, 
	new_value TEXT, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE categories (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	parent_id BIGINT, 
	name VARCHAR(255) NOT NULL, 
	slug VARCHAR(255) NOT NULL, 
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
	is_active BOOL NOT NULL, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	updated_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	CONSTRAINT uq_shipping_rates_country_method UNIQUE (country, delivery_method)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE tax_rules (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	country VARCHAR(100) NOT NULL, 
	customer_type VARCHAR(20) NOT NULL, 
	tax_type VARCHAR(30) NOT NULL, 
	rate DECIMAL(5, 2) NOT NULL, 
	is_active BOOL NOT NULL, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	updated_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	CONSTRAINT uq_tax_rules_country_customer_type_tax_type UNIQUE (country, customer_type, tax_type)
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
	created_at DATETIME NOT NULL DEFAULT now(), 
	updated_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	UNIQUE (email)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE warehouses (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	name VARCHAR(255) NOT NULL, 
	country VARCHAR(100) NOT NULL, 
	address TEXT, 
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
	city VARCHAR(100) NOT NULL, 
	address_line VARCHAR(255) NOT NULL, 
	postal_code VARCHAR(20) NOT NULL, 
	is_default BOOL NOT NULL, 
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
	created_at DATETIME NOT NULL DEFAULT now(), 
	updated_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	CONSTRAINT ck_products_volume_ml CHECK (volume_ml IN (350, 470, 800, 1000, 1900)), 
	CONSTRAINT ck_products_material CHECK (material = 'polypropylene'), 
	FOREIGN KEY(category_id) REFERENCES categories (id), 
	UNIQUE (slug)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE orders (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	order_number VARCHAR(50) NOT NULL, 
	user_id BIGINT, 
	guest_order_token VARCHAR(64), 
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
	city VARCHAR(100) NOT NULL, 
	address_line VARCHAR(255) NOT NULL, 
	postal_code VARCHAR(20) NOT NULL, 
	delivery_method VARCHAR(50) NOT NULL, 
	payment_method VARCHAR(50) NOT NULL, 
	source VARCHAR(20) NOT NULL, 
	company_name VARCHAR(255), 
	company_reg_number VARCHAR(100), 
	company_tax_number VARCHAR(100), 
	company_address VARCHAR(255), 
	contact_person VARCHAR(255), 
	payment_reference VARCHAR(255), 
	crm_deal_id VARCHAR(50), 
	notes TEXT, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	updated_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	UNIQUE (order_number), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	UNIQUE (guest_order_token), 
	FOREIGN KEY(cart_id) REFERENCES carts (id), 
	FOREIGN KEY(promo_code_id) REFERENCES promo_codes (id)
)CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE product_translations (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	product_id BIGINT NOT NULL, 
	locale VARCHAR(10) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	description TEXT, 
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
