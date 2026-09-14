CREATE TABLE order_reviews (
    review_id VARCHAR(50) NOT NULL,
    order_id VARCHAR(50) NOT NULL,

    review_score INT,
    review_comment_title TEXT,
    review_comment_message TEXT,

    review_creation_date DATETIME,
    review_answer_timestamp DATETIME,

    PRIMARY KEY (review_id,order_id)
) ENGINE=InnoDB DEFAULT CHARSET=UTF8MB4;
