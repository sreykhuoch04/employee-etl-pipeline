-- sql/init.sql
-- Run once when MySQL container starts

CREATE DATABASE IF NOT EXISTS employee_db;
USE employee_db;

CREATE TABLE IF NOT EXISTS employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    education VARCHAR(50),
    joining_year INT,
    city VARCHAR(100),
    payment_tier INT,
    age INT,
    gender VARCHAR(10),
    ever_benched VARCHAR(5),
    experience_in_current_domain INT,
    leave_or_not INT,
    salary DECIMAL(12, 2),
    bonus_percentage DECIMAL(5, 2),
    final_salary DECIMAL(12, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
