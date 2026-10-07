CREATE TABLE IF NOT EXISTS `category_translation` (
    `product_category_name` VARCHAR(255) NOT NULL,
    `product_category_name_english` VARCHAR(255),
    PRIMARY KEY (`product_category_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;