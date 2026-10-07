CREATE TABLE IF NOT EXISTS `products` (
    `product_id` VARCHAR(50) NOT NULL,
    `product_category_name` VARCHAR(255),
    `product_name_length` INT,
    `product_description_length` INT,
    `product_photos_qty` INT,
    `product_weight_g` INT,
    `product_length_cm` INT,
    `product_height_cm` INT,
    `product_width_cm` INT,
    PRIMARY KEY (`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;