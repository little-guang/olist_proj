CREATE TABLE products (
    product_id VARCHAR(50) NOT NULL,

    product_category_name VARCHAR(100),

    product_name_length INT,
    product_description_length INT,
    product_photos_qty INT,

    product_weight_g DECIMAL(12,2),
    product_length_cm DECIMAL(12,2),
    product_height_cm DECIMAL(12,2),
    product_width_cm DECIMAL(12,2),

    PRIMARY KEY (product_id),
    INDEX idx_products_category (product_category_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;