import sqlite3
import pandas as pd

DB_NAME = "sales_database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS sales_data (date TEXT PRIMARY KEY, amount REAL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS error_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, attempted_date TEXT, raw_value TEXT, error_reason TEXT)')
    conn.commit()
    conn.close()

def insert_bulk_data(df):
    """Inserts a pandas DataFrame directly into the SQL table."""
    conn = sqlite3.connect(DB_NAME)
    # Assumes CSV has columns 'date' and 'amount'
    df.to_sql('sales_data', conn, if_exists='append', index=False)
    conn.close()

# Keep existing functions: insert_sales_data, log_error, get_aggregated_sales, get_error_logs
# (You do not need to change the rest of the file)