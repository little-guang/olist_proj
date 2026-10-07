CREATE TABLE IF NOT EXISTS `order_reviews` (
    `review_id` VARCHAR(50) NOT NULL,
    `order_id` VARCHAR(50) NOT NULL,
    `review_score` INT,
    `review_comment_title` TEXT,
    `review_comment_message` TEXT,
    `review_creation_date` DATETIME,
    `review_answer_timestamp` DATETIME,
    PRIMARY KEY (`review_id`, `order_id`),
    CONSTRAINT `fk_reviews_order` FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;