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
)ENGINE=InnoDB CHARSET=utf8mb4;

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
)ENGINE=InnoDB CHARSET=utf8mb4;

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
)ENGINE=InnoDB CHARSET=utf8mb4;

CREATE TABLE quote_requests (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	rfq_number VARCHAR(30), 
	request_type VARCHAR(20) NOT NULL, 
	user_id BIGINT, 
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
	FOREIGN KEY(user_id) REFERENCES users (id)
)ENGINE=InnoDB CHARSET=utf8mb4;

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
)ENGINE=InnoDB CHARSET=utf8mb4;

CREATE TABLE wishlist_items (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	user_id BIGINT NOT NULL, 
	sku_id BIGINT NOT NULL, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	CONSTRAINT uq_wishlist_user_sku UNIQUE (user_id, sku_id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(sku_id) REFERENCES skus (id) ON DELETE CASCADE
)ENGINE=InnoDB CHARSET=utf8mb4;
