CREATE USER IF NOT EXISTS hackaton@localhost IDENTIFIED BY 'hackaton';

DROP DATABASE IF EXISTS hackaton;
CREATE DATABASE hackaton;

GRANT ALL PRIVILEGES ON hackaton.* TO hackaton@localhost;

use hackaton;

CREATE TABLE queries (
    `id` INTEGER AUTO_INCREMENT PRIMARY KEY,
    `uuid` VARCHAR(255) UNIQUE NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `profession` VARCHAR(255) NOT NULL,
    `_vacancy_table` VARCHAR(255) NULL,

    `created_at` DATETIME NOT NULL
    
);