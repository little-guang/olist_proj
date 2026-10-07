CREATE TABLE IF NOT EXISTS `orders` (
    `order_id` VARCHAR(50) NOT NULL,
    `customer_id` VARCHAR(50) NOT NULL,
    `order_status` VARCHAR(50),
    `order_purchase_timestamp` DATETIME,
    `order_approved_at` DATETIME,
    `order_delivered_carrier_date` DATETIME,
    `order_delivered_customer_date` DATETIME,
    `order_estimated_delivery_date` DATETIME,
    PRIMARY KEY (`order_id`),
    CONSTRAINT `fk_orders_customer` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;