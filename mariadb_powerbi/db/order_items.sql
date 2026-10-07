CREATE TABLE IF NOT EXISTS `order_items` (
    `order_id` VARCHAR(50) NOT NULL,
    `order_item_id` INT NOT NULL,
    `product_id` VARCHAR(50) NOT NULL,
    `seller_id` VARCHAR(50) NOT NULL,
    `shipping_limit_date` DATETIME,
    `price` DECIMAL(10, 2),
    `freight_value` DECIMAL(10, 2),
    PRIMARY KEY (`order_id`, `order_item_id`),
    CONSTRAINT `fk_items_order` FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`),
    CONSTRAINT `fk_items_product` FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`),
    CONSTRAINT `fk_items_seller` FOREIGN KEY (`seller_id`) REFERENCES `sellers` (`seller_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;