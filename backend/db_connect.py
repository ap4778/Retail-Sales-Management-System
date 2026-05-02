# ============================================================
# File: db_connect.py
# Project: Retail Sales Management System
# Description: Database Connectivity Layer (MySQL)
# Technology: Python 3.x + MySQL Connector
# ============================================================

import os

import mysql.connector
from mysql.connector import Error


def _safe_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": _safe_int(os.getenv("MYSQL_PORT", "3306"), 3306),
    "user": os.getenv("MYSQL_USER", os.getenv("DB_USER", "root")),
    "password": os.getenv("MYSQL_PASSWORD", os.getenv("DB_PASSWORD", "bihari")),
    "database": os.getenv("MYSQL_DATABASE", os.getenv("DB_NAME", "retailshop_manage")),
    "autocommit": False,
}


def _get_server_connection():
    """Connect to MySQL server without selecting a database."""
    try:
        conn = mysql.connector.connect(
            host=MYSQL_CONFIG["host"],
            port=MYSQL_CONFIG["port"],
            user=MYSQL_CONFIG["user"],
            password=MYSQL_CONFIG["password"],
            autocommit=False,
        )
        if conn.is_connected():
            return conn
    except Error as err:
        print(f"[ERROR] Server connection failed: {err}")
    return None


def get_connection():
    """Establish and return a MySQL database connection."""
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        if conn.is_connected():
            return conn
    except Error as err:
        print(f"[ERROR] Database connection failed: {err}")
    return None


def _create_database_if_not_exists():
    """Create target database if it does not exist yet."""
    conn = _get_server_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{MYSQL_CONFIG['database']}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        conn.commit()
        return True
    except Error as err:
        print(f"[ERROR] Database creation failed: {err}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def initialise_database():
    """Create required tables in MySQL if they do not exist."""
    if not _create_database_if_not_exists():
        return

    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Customer (
                customer_id INT PRIMARY KEY NOT NULL,
                gender      VARCHAR(20),
                age         INT
            ) ENGINE=InnoDB
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Product (
                product_id     INT PRIMARY KEY NOT NULL,
                category       VARCHAR(50),
                price_per_unit DECIMAL(12, 2),
                cogs           DECIMAL(12, 2)
            ) ENGINE=InnoDB
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Sales (
                transaction_id INT NOT NULL AUTO_INCREMENT,
                sale_date      DATE,
                sale_time      TIME,
                customer_id    INT,
                product_id     INT,
                quantity       INT,
                total_sale     DECIMAL(12, 2),
                PRIMARY KEY (transaction_id, product_id),
                FOREIGN KEY (customer_id) REFERENCES Customer(customer_id),
                FOREIGN KEY (product_id)  REFERENCES Product(product_id)
            ) ENGINE=InnoDB
            """
        )

        conn.commit()
        print("[OK] All tables created / verified successfully (MySQL).")
    except Error as err:
        print(f"[ERROR] Table creation failed: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    initialise_database()
