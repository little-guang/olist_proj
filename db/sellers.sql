CREATE TABLE sellers (
    seller_id VARCHAR(50) NOT NULL,
    seller_zip_code_prefix CHAR(5),
    seller_city VARCHAR(100),
    seller_state CHAR(2),

    PRIMARY KEY (seller_id),
    INDEX idx_seller_zip (seller_zip_code_prefix)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;