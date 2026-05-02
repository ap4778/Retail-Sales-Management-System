-- ============================================================
-- File: schema.sql
-- Project: Retail Sales Management System
-- Course: 21CSC205P - Database Management Systems
-- Description: Complete SQL schema and sample data
-- ============================================================

-- Create and use the database
CREATE DATABASE IF NOT EXISTS retailshop_manage;
USE retailshop_manage;

-- ============================================================
-- TABLE: Customer
-- ============================================================
DROP TABLE IF EXISTS Sales;
DROP TABLE IF EXISTS Product;
DROP TABLE IF EXISTS Customer;

CREATE TABLE Customer (
    customer_id INT          PRIMARY KEY NOT NULL,
    gender      VARCHAR(20),
    age         INT
);

-- ============================================================
-- TABLE: Product
-- ============================================================
CREATE TABLE Product (
    product_id     INT          PRIMARY KEY NOT NULL,
    category       VARCHAR(20),
    price_per_unit FLOAT,
    cogs           FLOAT
);

-- ============================================================
-- TABLE: Sales
-- ============================================================
CREATE TABLE Sales (
    transaction_id INT   NOT NULL,
    sale_date      DATE,
    sale_time      TIME,
    customer_id    INT,
    product_id     INT,
    quantity       INT,
    total_sale     FLOAT,
    PRIMARY KEY (transaction_id, product_id),
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id),
    FOREIGN KEY (product_id)  REFERENCES Product(product_id)
);

-- ============================================================
-- SAMPLE DATA: Customer
-- ============================================================
INSERT INTO Customer (customer_id, gender, age) VALUES
  (1001, 'Male',   28),
  (1002, 'Female', 34),
  (1003, 'Male',   22),
  (1004, 'Female', 45),
  (1005, 'Male',   31);

-- ============================================================
-- SAMPLE DATA: Product
-- ============================================================
INSERT INTO Product (product_id, category, price_per_unit, cogs) VALUES
  (1, 'Electronics', 500.00,  300.00),
  (2, 'Clothing',    150.00,   80.00),
  (3, 'Furniture',  1200.00,  700.00);

-- ============================================================
-- SAMPLE DATA: Sales
-- ============================================================
INSERT INTO Sales (transaction_id, sale_date, sale_time, customer_id, product_id, quantity, total_sale) VALUES
  (5001, '2024-01-15', '10:30:00', 1001, 1, 2, 1000.00),
  (5002, '2024-01-16', '11:00:00', 1002, 2, 1,  150.00),
  (5003, '2024-01-17', '14:00:00', 1003, 1, 3, 1500.00),
  (5004, '2024-01-18', '09:30:00', 1001, 3, 1, 1200.00),
  (5005, '2024-01-19', '16:00:00', 1004, 2, 4,  600.00);

-- ============================================================
-- VERIFICATION QUERIES
-- ============================================================
SELECT 'Customer Records:' AS info;
SELECT * FROM Customer;

SELECT 'Product Records:' AS info;
SELECT * FROM Product;

SELECT 'Sales Records:' AS info;
SELECT * FROM Sales;

SELECT 'Revenue Summary:' AS info;
SELECT
    c.customer_id,
    c.gender,
    p.category,
    SUM(s.quantity)   AS total_quantity,
    SUM(s.total_sale) AS total_revenue
FROM Sales s
JOIN Customer c ON s.customer_id = c.customer_id
JOIN Product  p ON s.product_id  = p.product_id
GROUP BY c.customer_id, c.gender, p.category
ORDER BY total_revenue DESC;
