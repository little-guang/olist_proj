CREATE TABLE IF NOT EXISTS `sellers` (
    `seller_id` VARCHAR(50) NOT NULL,
    `seller_zip_code_prefix` VARCHAR(10),
    `seller_city` VARCHAR(100),
    `seller_state` VARCHAR(10),
    PRIMARY KEY (`seller_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=UTF8MB4_UNICODE_CI;