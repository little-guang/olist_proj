CREATE TABLE geolocation (
    geolocation_zip_code_prefix CHAR(5),
    geolocation_lat DECIMAL(10,7),
    geolocation_lng DECIMAL(10,7),
    geolocation_city VARCHAR(100),
    geolocation_state CHAR(2),

    INDEX idx_geo_zip (geolocation_zip_code_prefix),
    INDEX idx_geo_state (geolocation_state)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;