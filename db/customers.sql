CREATE TABLE customers (
    customer_id VARCHAR(50) NOT NULL,
    customer_unique_id VARCHAR(50),
    customer_zip_code_prefix CHAR(5),
    customer_city VARCHAR(100),
    customer_state CHAR(2),

    PRIMARY KEY (customer_id),
    INDEX idx_customer_unique_id (customer_unique_id),
    INDEX idx_customer_zip (customer_zip_code_prefix)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;