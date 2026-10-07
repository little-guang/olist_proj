CREATE TABLE IF NOT EXISTS `geolocation` (
    `geolocation_zip_code_prefix` VARCHAR(10) NOT NULL,
    `geolocation_lat` DECIMAL(10, 8),
    `geolocation_lng` DECIMAL(11, 8),
    `geolocation_city` VARCHAR(100),
    `geolocation_state` VARCHAR(10),
    `geolocation_sample_count` INT NOT NULL,
    PRIMARY KEY (`geolocation_zip_code_prefix`),
    KEY `idx_geo_state` (`geolocation_state`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;