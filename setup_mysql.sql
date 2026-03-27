-- MySQL Setup Script for Restaurant Reservation API
-- Run this script with: mysql -u root -p < setup_mysql.sql

-- Create the database
CREATE DATABASE IF NOT EXISTS restaurant_db;

-- Create the user and grant permissions
CREATE USER IF NOT EXISTS 'restaurant_user'@'localhost' IDENTIFIED BY 'password';

-- Grant all privileges on the restaurant database to the user
GRANT ALL PRIVILEGES ON restaurant_db.* TO 'restaurant_user'@'localhost';

-- Apply privilege changes
FLUSH PRIVILEGES;

-- Verify
SELECT 'Database and user created successfully!' as status;
