import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from db_connect import get_connection, initialise_database


app = Flask(__name__)
CORS(app)

# Ensure tables exist before serving requests.
initialise_database()


def _open_connection():
    return get_connection()


def _error(message, status=400):
    return jsonify({"error": message}), status


def _parse_int(value, field_name):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be an integer")


def _parse_float(value, field_name):
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a number")


def _is_integrity_error(err):
    message = str(err).lower()
    return (
        "duplicate entry" in message
        or "foreign key constraint fails" in message
        or "cannot add or update a child row" in message
        or "unique constraint failed" in message
        or "foreign key constraint failed" in message
    )


def _integrity_message(err):
    message = str(err).lower()

    if "duplicate entry" in message:
        if "for key 'customer.primary'" in message or "customer.customer_id" in message:
            return "Customer ID already exists"
        if "for key 'product.primary'" in message or "product.product_id" in message:
            return "Product ID already exists"
        if "for key 'sales.primary'" in message or "sales.transaction_id" in message:
            return "Transaction ID already exists"
        return "Record already exists"

    if "unique constraint failed" in message:
        if "customer.customer_id" in message:
            return "Customer ID already exists"
        if "product.product_id" in message:
            return "Product ID already exists"
        if "sales.transaction_id" in message:
            return "Transaction ID already exists"
        return "Record already exists"

    if "foreign key constraint fails" in message or "foreign key constraint failed" in message:
        return "Customer ID or Product ID does not exist"

    return "Database constraint failed"


def _profit_margin(price_per_unit, cogs):
    if not price_per_unit:
        return 0
    return round(((price_per_unit - cogs) / price_per_unit) * 100, 1)


def _serialize_sale_record(record):
    item = dict(record)
    sale_date = item.get("sale_date")
    sale_time = item.get("sale_time")

    if sale_date is not None and hasattr(sale_date, "isoformat"):
        item["sale_date"] = sale_date.isoformat()
    elif sale_date is not None:
        item["sale_date"] = str(sale_date)

    if sale_time is not None:
        item["sale_time"] = str(sale_time)

    return item


@app.route("/")
def serve_frontend():
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend')
    return send_from_directory(frontend_dir, 'index.html')


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "Retail Sales API is running"})


@app.route("/api/customers", methods=["GET"])
def get_customers():
    conn = _open_connection()
    if not conn:
        return _error("Database connection failed", 500)

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT
                c.customer_id,
                c.gender,
                c.age,
                COUNT(s.transaction_id) AS transaction_count
            FROM Customer c
            LEFT JOIN Sales s ON s.customer_id = c.customer_id
            GROUP BY c.customer_id, c.gender, c.age
            ORDER BY c.customer_id
            """
        )
        return jsonify(cursor.fetchall())
    except Exception as err:
        return _error(str(err), 500)
    finally:
        cursor.close()
        conn.close()


@app.route("/api/customers", methods=["POST"])
def add_customer():
    data = request.get_json(silent=True) or {}
    if "customer_id" not in data or "gender" not in data or "age" not in data:
        return _error("Missing required fields: customer_id, gender, age")

    try:
        customer_id = _parse_int(data.get("customer_id"), "customer_id")
        age = _parse_int(data.get("age"), "age")
        gender = str(data.get("gender", "")).strip()
    except ValueError as err:
        return _error(str(err))

    if not gender:
        return _error("gender cannot be empty")
    if age <= 0 or age > 120:
        return _error("age must be between 1 and 120")

    conn = _open_connection()
    if not conn:
        return _error("Database connection failed", 500)

    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Customer (customer_id, gender, age) VALUES (%s, %s, %s)",
            (customer_id, gender, age),
        )
        conn.commit()
        return (
            jsonify(
                {
                    "message": f"Customer {customer_id} added successfully",
                    "customer_id": customer_id,
                }
            ),
            201,
        )
    except Exception as err:
        conn.rollback()
        if _is_integrity_error(err):
            return _error(_integrity_message(err), 409)
        return _error(str(err), 500)
    finally:
        cursor.close()
        conn.close()


@app.route("/api/customers/<int:customer_id>", methods=["GET"])
def get_customer(customer_id):
    conn = _open_connection()
    if not conn:
        return _error("Database connection failed", 500)

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT
                c.customer_id,
                c.gender,
                c.age,
                COUNT(s.transaction_id) AS transaction_count
            FROM Customer c
            LEFT JOIN Sales s ON s.customer_id = c.customer_id
            WHERE c.customer_id = %s
            GROUP BY c.customer_id, c.gender, c.age
            """,
            (customer_id,),
        )
        row = cursor.fetchone()
        if not row:
            return _error("Customer not found", 404)
        return jsonify(row)
    except Exception as err:
        return _error(str(err), 500)
    finally:
        cursor.close()
        conn.close()


@app.route("/api/products", methods=["GET"])
def get_products():
    conn = _open_connection()
    if not conn:
        return _error("Database connection failed", 500)

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM Product ORDER BY product_id")
        products = cursor.fetchall()
        for product in products:
            product["profit_margin"] = _profit_margin(
                float(product["price_per_unit"] or 0),
                float(product["cogs"] or 0),
            )
        return jsonify(products)
    except Exception as err:
        return _error(str(err), 500)
    finally:
        cursor.close()
        conn.close()


@app.route("/api/products", methods=["POST"])
def add_product():
    data = request.get_json(silent=True) or {}
    if "product_id" not in data or "category" not in data or "price_per_unit" not in data or "cogs" not in data:
        return _error("Missing required fields: product_id, category, price_per_unit, cogs")

    try:
        product_id = _parse_int(data.get("product_id"), "product_id")
        category = str(data.get("category", "")).strip()
        price_per_unit = _parse_float(data.get("price_per_unit"), "price_per_unit")
        cogs = _parse_float(data.get("cogs"), "cogs")
    except ValueError as err:
        return _error(str(err))

    if not category:
        return _error("category cannot be empty")
    if price_per_unit <= 0:
        return _error("price_per_unit must be greater than 0")
    if cogs < 0:
        return _error("cogs cannot be negative")

    conn = _open_connection()
    if not conn:
        return _error("Database connection failed", 500)

    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Product (product_id, category, price_per_unit, cogs) VALUES (%s, %s, %s, %s)",
            (product_id, category, price_per_unit, cogs),
        )
        conn.commit()
        return (
            jsonify(
                {
                    "message": f"Product {product_id} ({category}) added successfully",
                    "product_id": product_id,
                }
            ),
            201,
        )
    except Exception as err:
        conn.rollback()
        if _is_integrity_error(err):
            return _error(_integrity_message(err), 409)
        return _error(str(err), 500)
    finally:
        cursor.close()
        conn.close()


@app.route("/api/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    conn = _open_connection()
    if not conn:
        return _error("Database connection failed", 500)

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM Product WHERE product_id = %s", (product_id,))
        row = cursor.fetchone()
        if not row:
            return _error("Product not found", 404)

        row["profit_margin"] = _profit_margin(
            float(row["price_per_unit"] or 0),
            float(row["cogs"] or 0),
        )
        return jsonify(row)
    except Exception as err:
        return _error(str(err), 500)
    finally:
        cursor.close()
        conn.close()


@app.route("/api/sales", methods=["GET"])
def get_sales():
    conn = _open_connection()
    if not conn:
        return _error("Database connection failed", 500)

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT s.transaction_id, s.sale_date, s.sale_time, s.customer_id, 
                   GROUP_CONCAT(CONCAT(s.product_id, ' (', p.category, ') - Qty: ', s.quantity) SEPARATOR ', ') AS product_id, 
                   SUM(s.quantity) AS quantity, 
                   SUM(s.total_sale) AS total_sale
            FROM Sales s
            LEFT JOIN Product p ON s.product_id = p.product_id
            GROUP BY s.transaction_id, s.sale_date, s.sale_time, s.customer_id
            ORDER BY s.transaction_id DESC
        """)
        sales = [_serialize_sale_record(row) for row in cursor.fetchall()]
        return jsonify(sales)
    except Exception as err:
        return _error(str(err), 500)
    finally:
        cursor.close()
        conn.close()


@app.route("/api/sales", methods=["POST"])
def add_sale():
    data = request.get_json(silent=True) or {}
    
    # New format supporting multiple products in one transaction
    if "products" in data:
        try:
            customer_id = _parse_int(data.get("customer_id"), "customer_id")
        except ValueError as err:
            return _error(str(err))

        products = data.get("products")
        if not products or not isinstance(products, list):
            return _error("products must be a non-empty list")

        from datetime import datetime
        now = datetime.now()
        sale_date = now.strftime("%Y-%m-%d")
        sale_time = now.strftime("%H:%M:%S")

        conn = _open_connection()
        if not conn:
            return _error("Database connection failed", 500)

        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT customer_id FROM Customer WHERE customer_id = %s", (customer_id,))
            if not cursor.fetchone():
                return _error("Customer not found", 404)

            transaction_id = None
            for prod in products:
                product_id = _parse_int(prod.get("product_id"), "product_id")
                quantity = _parse_int(prod.get("quantity"), "quantity")

                if quantity <= 0:
                    return _error("quantity must be greater than 0")

                cursor.execute("SELECT price_per_unit FROM Product WHERE product_id = %s", (product_id,))
                product_row = cursor.fetchone()
                if not product_row:
                    return _error(f"Product {product_id} not found", 404)

                if "total_sale" in prod and prod.get("total_sale") is not None:
                    total_sale = _parse_float(prod.get("total_sale"), "total_sale")
                else:
                    total_sale = float(product_row["price_per_unit"]) * quantity

                if total_sale < 0:
                    return _error("total_sale cannot be negative")

                if transaction_id is None:
                    # First item: let DB auto-generate the transaction_id
                    cursor.execute(
                        """
                        INSERT INTO Sales
                            (sale_date, sale_time, customer_id, product_id, quantity, total_sale)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (sale_date, sale_time, customer_id, product_id, quantity, total_sale),
                    )
                    transaction_id = cursor.lastrowid
                else:
                    # Subsequent items: use the generated transaction_id
                    cursor.execute(
                        """
                        INSERT INTO Sales
                            (transaction_id, sale_date, sale_time, customer_id, product_id, quantity, total_sale)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (transaction_id, sale_date, sale_time, customer_id, product_id, quantity, total_sale),
                    )

            conn.commit()
            return (
                jsonify(
                    {
                        "message": f"Sale {transaction_id} recorded successfully",
                        "transaction_id": transaction_id,
                    }
                ),
                201,
            )
        except Exception as err:
            conn.rollback()
            if _is_integrity_error(err):
                return _error(_integrity_message(err), 409)
            return _error(str(err), 500)
        finally:
            cursor.close()
            conn.close()

    # Fallback to old format
    required = ["customer_id", "product_id", "quantity"]
    missing = [field for field in required if field not in data]
    if missing:
        return _error(f"Missing required fields: {', '.join(missing)}")

    try:
        customer_id = _parse_int(data.get("customer_id"), "customer_id")
        product_id = _parse_int(data.get("product_id"), "product_id")
        quantity = _parse_int(data.get("quantity"), "quantity")
    except ValueError as err:
        return _error(str(err))

    if quantity <= 0:
        return _error("quantity must be greater than 0")

    # Use system date and time (cannot be changed by users)
    from datetime import datetime
    now = datetime.now()
    sale_date = now.strftime("%Y-%m-%d")
    sale_time = now.strftime("%H:%M:%S")

    conn = _open_connection()
    if not conn:
        return _error("Database connection failed", 500)

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT price_per_unit FROM Product WHERE product_id = %s", (product_id,))
        product_row = cursor.fetchone()
        if not product_row:
            return _error("Product not found", 404)

        cursor.execute("SELECT customer_id FROM Customer WHERE customer_id = %s", (customer_id,))
        customer_row = cursor.fetchone()
        if not customer_row:
            return _error("Customer not found", 404)

        if "total_sale" in data and data.get("total_sale") is not None:
            total_sale = _parse_float(data.get("total_sale"), "total_sale")
        else:
            total_sale = float(product_row["price_per_unit"]) * quantity

        if total_sale < 0:
            return _error("total_sale cannot be negative")

        if "transaction_id" in data:
            transaction_id = _parse_int(data.get("transaction_id"), "transaction_id")
            cursor.execute(
                """
                INSERT INTO Sales
                    (transaction_id, sale_date, sale_time, customer_id, product_id, quantity, total_sale)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (transaction_id, sale_date, sale_time, customer_id, product_id, quantity, total_sale),
            )
        else:
            cursor.execute(
                """
                INSERT INTO Sales
                    (sale_date, sale_time, customer_id, product_id, quantity, total_sale)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (sale_date, sale_time, customer_id, product_id, quantity, total_sale),
            )
            transaction_id = cursor.lastrowid

        conn.commit()
        return (
            jsonify(
                {
                    "message": f"Sale {transaction_id} recorded successfully",
                    "transaction_id": transaction_id,
                }
            ),
            201,
        )
    except Exception as err:
        conn.rollback()
        if _is_integrity_error(err):
            return _error(_integrity_message(err), 409)
        return _error(str(err), 500)
    finally:
        cursor.close()
        conn.close()


@app.route("/api/sales/<int:transaction_id>", methods=["GET"])
def get_sale(transaction_id):
    conn = _open_connection()
    if not conn:
        return _error("Database connection failed", 500)

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT s.transaction_id, s.sale_date, s.sale_time, s.customer_id, 
                   GROUP_CONCAT(CONCAT(s.product_id, ' (', p.category, ') - Qty: ', s.quantity) SEPARATOR ', ') AS product_id, 
                   SUM(s.quantity) AS quantity, 
                   SUM(s.total_sale) AS total_sale
            FROM Sales s
            LEFT JOIN Product p ON s.product_id = p.product_id
            WHERE s.transaction_id = %s
            GROUP BY s.transaction_id, s.sale_date, s.sale_time, s.customer_id
        """, (transaction_id,))
        row = cursor.fetchone()
        if not row:
            return _error("Sale not found", 404)
        return jsonify(_serialize_sale_record(row))
    except Exception as err:
        return _error(str(err), 500)
    finally:
        cursor.close()
        conn.close()


@app.route("/api/dashboard/stats", methods=["GET"])
def get_dashboard_stats():
    conn = _open_connection()
    if not conn:
        return _error("Database connection failed", 500)

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT COUNT(*) AS total FROM Customer")
        total_customers = int(cursor.fetchone()["total"])

        cursor.execute("SELECT COUNT(*) AS total FROM Product")
        total_products = int(cursor.fetchone()["total"])

        cursor.execute("SELECT COUNT(*) AS total FROM Sales")
        total_transactions = int(cursor.fetchone()["total"])

        cursor.execute("SELECT COALESCE(SUM(total_sale), 0) AS total FROM Sales")
        total_revenue = float(cursor.fetchone()["total"])

        cursor.execute("SELECT COALESCE(SUM(quantity), 0) AS total FROM Sales")
        total_units = int(cursor.fetchone()["total"])

        return jsonify(
            {
                "total_customers": total_customers,
                "total_products": total_products,
                "total_transactions": total_transactions,
                "total_revenue": total_revenue,
                "total_units_sold": total_units,
            }
        )
    except Exception as err:
        return _error(str(err), 500)
    finally:
        cursor.close()
        conn.close()


@app.route("/api/dashboard/recent-sales", methods=["GET"])
def get_recent_sales():
    conn = _open_connection()
    if not conn:
        return _error("Database connection failed", 500)

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT s.transaction_id, s.sale_date, s.sale_time, s.customer_id, 
                   GROUP_CONCAT(CONCAT(s.product_id, ' (', p.category, ') - Qty: ', s.quantity) SEPARATOR ', ') AS product_id, 
                   SUM(s.quantity) AS quantity, 
                   SUM(s.total_sale) AS total_sale
            FROM Sales s
            LEFT JOIN Product p ON s.product_id = p.product_id
            GROUP BY s.transaction_id, s.sale_date, s.sale_time, s.customer_id
            ORDER BY s.transaction_id DESC
            LIMIT 5
            """
        )
        sales = [_serialize_sale_record(row) for row in cursor.fetchall()]
        return jsonify(sales)
    except Exception as err:
        return _error(str(err), 500)
    finally:
        cursor.close()
        conn.close()


@app.route("/api/reports/sales", methods=["GET"])
def get_sales_report():
    customer_id = request.args.get("customer_id", type=int)
    product_id = request.args.get("product_id", type=int)
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")

    conn = _open_connection()
    if not conn:
        return _error("Database connection failed", 500)

    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT s.transaction_id, s.sale_date, s.sale_time, s.customer_id, 
                   GROUP_CONCAT(CONCAT(s.product_id, ' (', p.category, ') - Qty: ', s.quantity) SEPARATOR ', ') AS product_id, 
                   SUM(s.quantity) AS quantity, 
                   SUM(s.total_sale) AS total_sale
            FROM Sales s
            LEFT JOIN Product p ON s.product_id = p.product_id
            WHERE 1=1
        """
        params = []

        if customer_id:
            query += " AND customer_id = %s"
            params.append(customer_id)
        if product_id:
            query += " AND product_id = %s"
            params.append(product_id)
        if from_date:
            query += " AND sale_date >= %s"
            params.append(from_date)
        if to_date:
            query += " AND sale_date <= %s"
            params.append(to_date)

        query += " GROUP BY s.transaction_id, s.sale_date, s.sale_time, s.customer_id ORDER BY s.transaction_id DESC"
        cursor.execute(query, params)
        sales = [_serialize_sale_record(row) for row in cursor.fetchall()]

        total_revenue = sum(float(item["total_sale"]) for item in sales)
        total_quantity = sum(int(item["quantity"]) for item in sales)

        return jsonify(
            {
                "sales": sales,
                "summary": {
                    "total_transactions": len(sales),
                    "total_quantity": total_quantity,
                    "total_revenue": total_revenue,
                },
            }
        )
    except Exception as err:
        return _error(str(err), 500)
    finally:
        cursor.close()
        conn.close()


@app.route("/api/reports/category-summary", methods=["GET"])
def get_category_summary():
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")

    conn = _open_connection()
    if not conn:
        return _error("Database connection failed", 500)

    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT
                COALESCE(p.category, 'Unknown') AS category,
                COUNT(s.transaction_id) AS total_transactions,
                COALESCE(SUM(s.quantity), 0) AS total_quantity,
                COALESCE(SUM(s.total_sale), 0) AS total_revenue
            FROM Sales s
            LEFT JOIN Product p ON s.product_id = p.product_id
            WHERE 1=1
        """
        params = []
        if from_date:
            query += " AND s.sale_date >= %s"
            params.append(from_date)
        if to_date:
            query += " AND s.sale_date <= %s"
            params.append(to_date)
            
        query += " GROUP BY p.category ORDER BY total_revenue DESC"
        
        cursor.execute(query, params)

        results = cursor.fetchall()
        for item in results:
            item["total_revenue"] = float(item["total_revenue"])

        return jsonify(results)
    except Exception as err:
        return _error(str(err), 500)
    finally:
        cursor.close()
        conn.close()


@app.route("/api/calculate-total", methods=["GET"])
def calculate_total():
    product_id = request.args.get("product_id", type=int)
    quantity = request.args.get("quantity", type=int)

    if not product_id or not quantity:
        return _error("Product ID and Quantity are required")
    if quantity <= 0:
        return _error("Quantity must be greater than 0")

    conn = _open_connection()
    if not conn:
        return _error("Database connection failed", 500)

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT price_per_unit FROM Product WHERE product_id = %s", (product_id,))
        row = cursor.fetchone()
        if not row:
            return _error("Product not found", 404)

        total = float(row["price_per_unit"]) * quantity
        return jsonify({"product_id": product_id, "quantity": quantity, "total_sale": total})
    except Exception as err:
        return _error(str(err), 500)
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    print("=" * 50)
    print("Starting Retail Sales Management API...")
    print("API available at: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, port=5000)
