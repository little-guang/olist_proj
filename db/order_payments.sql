CREATE TABLE IF NOT EXISTS `order_payments` (
    `order_id` VARCHAR(50) NOT NULL,
    `payment_sequential` INT NOT NULL,
    `payment_type` VARCHAR(50),
    `payment_installments` INT,
    `payment_value` DECIMAL(10, 2),
    PRIMARY KEY (`order_id`, `payment_sequential`),
    CONSTRAINT `fk_payments_order` FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;