CREATE TABLE IF NOT EXISTS `dim_geolocation` (
    `zip_code_prefix` VARCHAR(10) NOT NULL,
    `latitude` DECIMAL(10, 8),
    `longitude` DECIMAL(11, 8),
    `city` VARCHAR(100),
    `state` VARCHAR(10),
    `sample_count` INT NOT NULL,
    PRIMARY KEY (`zip_code_prefix`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `dim_customers` (
    `customer_id` VARCHAR(50) NOT NULL,
    `customer_unique_id` VARCHAR(50) NOT NULL,
    `customer_zip_code_prefix` VARCHAR(10),
    `customer_city` VARCHAR(100),
    `customer_state` VARCHAR(10),
    PRIMARY KEY (`customer_id`),
    KEY `idx_dim_customers_city_state` (`customer_state`, `customer_city`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `dim_sellers` (
    `seller_id` VARCHAR(50) NOT NULL,
    `seller_zip_code_prefix` VARCHAR(10),
    `seller_city` VARCHAR(100),
    `seller_state` VARCHAR(10),
    PRIMARY KEY (`seller_id`),
    KEY `idx_dim_sellers_city_state` (`seller_state`, `seller_city`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `dim_products` (
    `product_id` VARCHAR(50) NOT NULL,
    `product_category_name` VARCHAR(255),
    `product_category_name_english` VARCHAR(255),
    `product_name_length` INT,
    `product_description_length` INT,
    `product_photos_qty` INT,
    `product_weight_g` INT,
    `product_length_cm` INT,
    `product_height_cm` INT,
    `product_width_cm` INT,
    PRIMARY KEY (`product_id`),
    KEY `idx_dim_products_category_en` (`product_category_name_english`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `fact_orders` (
    `order_id` VARCHAR(50) NOT NULL,
    `customer_id` VARCHAR(50) NOT NULL,
    `order_status` VARCHAR(50),
    `order_purchase_timestamp` DATETIME,
    `order_approved_at` DATETIME,
    `order_delivered_carrier_date` DATETIME,
    `order_delivered_customer_date` DATETIME,
    `order_estimated_delivery_date` DATETIME,
    PRIMARY KEY (`order_id`),
    KEY `idx_fact_orders_customer` (`customer_id`),
    KEY `idx_fact_orders_purchase` (`order_purchase_timestamp`),
    CONSTRAINT `fk_fact_orders_customer`
        FOREIGN KEY (`customer_id`) REFERENCES `dim_customers` (`customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `fact_order_items` (
    `order_id` VARCHAR(50) NOT NULL,
    `order_item_id` INT NOT NULL,
    `product_id` VARCHAR(50) NOT NULL,
    `seller_id` VARCHAR(50) NOT NULL,
    `shipping_limit_date` DATETIME,
    `price` DECIMAL(10, 2),
    `freight_value` DECIMAL(10, 2),
    PRIMARY KEY (`order_id`, `order_item_id`),
    KEY `idx_fact_order_items_product` (`product_id`),
    KEY `idx_fact_order_items_seller` (`seller_id`),
    CONSTRAINT `fk_fact_order_items_order`
        FOREIGN KEY (`order_id`) REFERENCES `fact_orders` (`order_id`),
    CONSTRAINT `fk_fact_order_items_product`
        FOREIGN KEY (`product_id`) REFERENCES `dim_products` (`product_id`),
    CONSTRAINT `fk_fact_order_items_seller`
        FOREIGN KEY (`seller_id`) REFERENCES `dim_sellers` (`seller_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `fact_order_payments` (
    `order_id` VARCHAR(50) NOT NULL,
    `payment_sequential` INT NOT NULL,
    `payment_type` VARCHAR(50),
    `payment_installments` INT,
    `payment_value` DECIMAL(10, 2),
    PRIMARY KEY (`order_id`, `payment_sequential`),
    CONSTRAINT `fk_fact_order_payments_order`
        FOREIGN KEY (`order_id`) REFERENCES `fact_orders` (`order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `fact_order_reviews` (
    `review_id` VARCHAR(50) NOT NULL,
    `order_id` VARCHAR(50) NOT NULL,
    `review_score` INT,
    `review_comment_title` TEXT,
    `review_comment_message` TEXT,
    `review_creation_date` DATETIME,
    `review_answer_timestamp` DATETIME,
    PRIMARY KEY (`review_id`, `order_id`),
    KEY `idx_fact_order_reviews_order` (`order_id`),
    CONSTRAINT `fk_fact_order_reviews_order`
        FOREIGN KEY (`order_id`) REFERENCES `fact_orders` (`order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `dim_geolocation` (
    `zip_code_prefix`, `latitude`, `longitude`, `city`, `state`, `sample_count`
)
SELECT
    `geolocation_zip_code_prefix`,
    AVG(`geolocation_lat`),
    AVG(`geolocation_lng`),
    MAX(`geolocation_city`),
    MAX(`geolocation_state`),
    SUM(`geolocation_sample_count`)
FROM `geolocation`
GROUP BY `geolocation_zip_code_prefix`
ON DUPLICATE KEY UPDATE
    `latitude` = VALUES(`latitude`),
    `longitude` = VALUES(`longitude`),
    `city` = VALUES(`city`),
    `state` = VALUES(`state`),
    `sample_count` = VALUES(`sample_count`);

INSERT INTO `dim_customers` (
    `customer_id`, `customer_unique_id`, `customer_zip_code_prefix`,
    `customer_city`, `customer_state`
)
SELECT
    `customer_id`, `customer_unique_id`, `customer_zip_code_prefix`,
    `customer_city`, `customer_state`
FROM `customers`
ON DUPLICATE KEY UPDATE
    `customer_unique_id` = VALUES(`customer_unique_id`),
    `customer_zip_code_prefix` = VALUES(`customer_zip_code_prefix`),
    `customer_city` = VALUES(`customer_city`),
    `customer_state` = VALUES(`customer_state`);

INSERT INTO `dim_sellers` (
    `seller_id`, `seller_zip_code_prefix`, `seller_city`, `seller_state`
)
SELECT `seller_id`, `seller_zip_code_prefix`, `seller_city`, `seller_state`
FROM `sellers`
ON DUPLICATE KEY UPDATE
    `seller_zip_code_prefix` = VALUES(`seller_zip_code_prefix`),
    `seller_city` = VALUES(`seller_city`),
    `seller_state` = VALUES(`seller_state`);

INSERT INTO `dim_products` (
    `product_id`, `product_category_name`, `product_category_name_english`,
    `product_name_length`, `product_description_length`, `product_photos_qty`,
    `product_weight_g`, `product_length_cm`, `product_height_cm`, `product_width_cm`
)
SELECT
    p.`product_id`,
    COALESCE(p.`product_category_name`, 'unknown'),
    COALESCE(t.`product_category_name_english`, 'unknown'),
    p.`product_name_length`,
    p.`product_description_length`,
    p.`product_photos_qty`,
    p.`product_weight_g`,
    p.`product_length_cm`,
    p.`product_height_cm`,
    p.`product_width_cm`
FROM `products` AS p
LEFT JOIN `category_translation` AS t
    ON p.`product_category_name` = t.`product_category_name`
ON DUPLICATE KEY UPDATE
    `product_category_name` = VALUES(`product_category_name`),
    `product_category_name_english` = VALUES(`product_category_name_english`),
    `product_name_length` = VALUES(`product_name_length`),
    `product_description_length` = VALUES(`product_description_length`),
    `product_photos_qty` = VALUES(`product_photos_qty`),
    `product_weight_g` = VALUES(`product_weight_g`),
    `product_length_cm` = VALUES(`product_length_cm`),
    `product_height_cm` = VALUES(`product_height_cm`),
    `product_width_cm` = VALUES(`product_width_cm`);

INSERT INTO `fact_orders` (
    `order_id`, `customer_id`, `order_status`, `order_purchase_timestamp`,
    `order_approved_at`, `order_delivered_carrier_date`,
    `order_delivered_customer_date`, `order_estimated_delivery_date`
)
SELECT
    `order_id`, `customer_id`, `order_status`, `order_purchase_timestamp`,
    `order_approved_at`, `order_delivered_carrier_date`,
    `order_delivered_customer_date`, `order_estimated_delivery_date`
FROM `orders`
ON DUPLICATE KEY UPDATE
    `customer_id` = VALUES(`customer_id`),
    `order_status` = VALUES(`order_status`),
    `order_purchase_timestamp` = VALUES(`order_purchase_timestamp`),
    `order_approved_at` = VALUES(`order_approved_at`),
    `order_delivered_carrier_date` = VALUES(`order_delivered_carrier_date`),
    `order_delivered_customer_date` = VALUES(`order_delivered_customer_date`),
    `order_estimated_delivery_date` = VALUES(`order_estimated_delivery_date`);

INSERT INTO `fact_order_items` (
    `order_id`, `order_item_id`, `product_id`, `seller_id`,
    `shipping_limit_date`, `price`, `freight_value`
)
SELECT
    `order_id`, `order_item_id`, `product_id`, `seller_id`,
    `shipping_limit_date`, `price`, `freight_value`
FROM `order_items`
ON DUPLICATE KEY UPDATE
    `product_id` = VALUES(`product_id`),
    `seller_id` = VALUES(`seller_id`),
    `shipping_limit_date` = VALUES(`shipping_limit_date`),
    `price` = VALUES(`price`),
    `freight_value` = VALUES(`freight_value`);

INSERT INTO `fact_order_payments` (
    `order_id`, `payment_sequential`, `payment_type`,
    `payment_installments`, `payment_value`
)
SELECT
    `order_id`, `payment_sequential`, `payment_type`,
    `payment_installments`, `payment_value`
FROM `order_payments`
ON DUPLICATE KEY UPDATE
    `payment_type` = VALUES(`payment_type`),
    `payment_installments` = VALUES(`payment_installments`),
    `payment_value` = VALUES(`payment_value`);

INSERT INTO `fact_order_reviews` (
    `review_id`, `order_id`, `review_score`, `review_comment_title`,
    `review_comment_message`, `review_creation_date`, `review_answer_timestamp`
)
SELECT
    `review_id`, `order_id`, `review_score`, `review_comment_title`,
    `review_comment_message`, `review_creation_date`, `review_answer_timestamp`
FROM `order_reviews`
ON DUPLICATE KEY UPDATE
    `review_score` = VALUES(`review_score`),
    `review_comment_title` = VALUES(`review_comment_title`),
    `review_comment_message` = VALUES(`review_comment_message`),
    `review_creation_date` = VALUES(`review_creation_date`),
    `review_answer_timestamp` = VALUES(`review_answer_timestamp`);

CREATE OR REPLACE VIEW `view_order_summary` AS
SELECT
    o.`order_id`,
    o.`order_purchase_timestamp`,
    o.`order_status`,
    c.`customer_id`,
    c.`customer_unique_id`,
    c.`customer_zip_code_prefix`,
    c.`customer_city`,
    c.`customer_state`,
    g.`latitude` AS `customer_latitude`,
    g.`longitude` AS `customer_longitude`,
    COALESCE(i.`item_count`, 0) AS `item_count`,
    COALESCE(i.`product_sales`, 0.00) AS `product_sales`,
    COALESCE(i.`freight_total`, 0.00) AS `freight_total`,
    COALESCE(p.`payment_total`, 0.00) AS `payment_total`,
    r.`average_review_score`,
    COALESCE(r.`review_count`, 0) AS `review_count`,
    o.`order_delivered_customer_date`,
    o.`order_estimated_delivery_date`
FROM `fact_orders` AS o
LEFT JOIN `dim_customers` AS c
    ON o.`customer_id` = c.`customer_id`
LEFT JOIN `dim_geolocation` AS g
    ON c.`customer_zip_code_prefix` = g.`zip_code_prefix`
LEFT JOIN (
    SELECT
        `order_id`,
        COUNT(*) AS `item_count`,
        SUM(`price`) AS `product_sales`,
        SUM(`freight_value`) AS `freight_total`
    FROM `fact_order_items`
    GROUP BY `order_id`
) AS i ON o.`order_id` = i.`order_id`
LEFT JOIN (
    SELECT `order_id`, SUM(`payment_value`) AS `payment_total`
    FROM `fact_order_payments`
    GROUP BY `order_id`
) AS p ON o.`order_id` = p.`order_id`
LEFT JOIN (
    SELECT
        `order_id`,
        AVG(`review_score`) AS `average_review_score`,
        COUNT(*) AS `review_count`
    FROM `fact_order_reviews`
    GROUP BY `order_id`
) AS r ON o.`order_id` = r.`order_id`;

CREATE OR REPLACE VIEW `view_order_item_summary` AS
SELECT
    o.`order_id`,
    o.`order_purchase_timestamp`,
    o.`order_status`,
    c.`customer_zip_code_prefix`,
    c.`customer_city`,
    c.`customer_state`,
    g.`latitude` AS `customer_latitude`,
    g.`longitude` AS `customer_longitude`,
    i.`order_item_id`,
    i.`product_id`,
    p.`product_category_name_english`,
    i.`seller_id`,
    s.`seller_city`,
    s.`seller_state`,
    i.`price`,
    i.`freight_value`,
    (i.`price` + i.`freight_value`) AS `item_total`
FROM `fact_order_items` AS i
INNER JOIN `fact_orders` AS o
    ON i.`order_id` = o.`order_id`
LEFT JOIN `dim_customers` AS c
    ON o.`customer_id` = c.`customer_id`
LEFT JOIN `dim_geolocation` AS g
    ON c.`customer_zip_code_prefix` = g.`zip_code_prefix`
LEFT JOIN `dim_products` AS p
    ON i.`product_id` = p.`product_id`
LEFT JOIN `dim_sellers` AS s
    ON i.`seller_id` = s.`seller_id`;
