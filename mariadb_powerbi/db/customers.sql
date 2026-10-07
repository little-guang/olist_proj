CREATE TABLE IF NOT EXISTS `customers` (
    `customer_id` VARCHAR(50) NOT NULL,
    `customer_unique_id` VARCHAR(50) NOT NULL,
    `customer_zip_code_prefix` VARCHAR(10),
    `customer_city` VARCHAR(100),
    `customer_state` VARCHAR(10),
    PRIMARY KEY (`customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;