from db_connect import get_connection

def alter_sales_table():
    conn = get_connection()
    if not conn:
        print("Could not connect to database")
        return
    
    cursor = conn.cursor()
    try:
        # Drop the existing primary key and add the new composite primary key
        cursor.execute("ALTER TABLE Sales DROP PRIMARY KEY, ADD PRIMARY KEY (transaction_id, product_id)")
        conn.commit()
        print("Successfully updated Sales table primary key.")
    except Exception as e:
        print("Error altering table (might already be updated):", e)
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    alter_sales_table()
