CREATE TABLE order_items (
    order_id VARCHAR(50) NOT NULL,
    order_item_id INT,
    product_id VARCHAR(50),
    seller_id VARCHAR(50),

    shipping_limit_date DATETIME,

    price DECIMAL(12,2),
    freight_value DECIMAL(12,2),

    INDEX idx_order_items_order_id (order_id),
    INDEX idx_order_items_product_id (product_id),
    INDEX idx_order_items_seller_id (seller_id),
    INDEX idx_order_items_order_item (order_id, order_item_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;