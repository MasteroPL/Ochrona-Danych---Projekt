DROP DATABASE IF EXISTS fileshare;
CREATE DATABASE fileshare DEFAULT CHARACTER SET utf8 COLLATE utf8_polish_ci;

USE fileshare;

CREATE TABLE user (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,

    login VARCHAR(20) NOT NULL UNIQUE,
    password_hash VARCHAR(256) NOT NULL
);

CREATE TABLE user_file (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,

    file_code VARCHAR(36) NOT NULL UNIQUE,
    file_path VARCHAR(256) NOT NULL,
    file_name VARCHAR(50) NOT NULL,
    is_public BOOLEAN NOT NULL DEFAULT 0,
    file_type ENUM('TEXT', 'BLOB') NOT NULL,
    file_mime_type VARCHAR(50) NOT NULL,

    -- Jeśli tak, użytkownik podał hasło do odwracalnego zakodowania pliku
    -- Identyczne hasło musi zostać podane w celu odkodowania go
    -- W przeciwnym wypadku plik zostanie zakodowany domyślnym hasłem
    file_manually_encoded BOOLEAN NOT NULL DEFAULT 0,

    -- Sygnatura potrzebna tylko jeśli plik jest zakodowany
    file_signature VARBINARY(40) NOT NULL,

    updated_at DATETIME NOT NULL DEFAULT NOW(),
    created_at DATETIME NOT NULL DEFAULT NOW()
);

CREATE TABLE user__user_file__assignment (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,

    user_id INT NOT NULL,
    user_file_id INT NOT NULL,

    access_type ENUM('OWNER', 'EDITOR', 'READER') NOT NULL DEFAULT 'READER',

    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (user_file_id) REFERENCES user_file(id),

    UNIQUE KEY (user_id, user_file_id)
);


DELIMITER $$
CREATE TRIGGER trggr__user_file__auto_values_update
BEFORE UPDATE ON user_file FOR EACH ROW
BEGIN
    SET NEW.updated_at = NOW();
END$$
DELIMITER ;


CREATE TABLE failed_logins (
    ip_address VARCHAR(30) NOT NULL,
    user_id INT NULL,
    created_at DATETIME NOT NULL DEFAULT NOW(),

    FOREIGN KEY (user_id) REFERENCES user(id)
);

CREATE INDEX failed_logins__ip_address
ON failed_logins (ip_address);