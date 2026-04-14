import sqlite3
import pandas as pd

DB_NAME = "sales_database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Main sales table
    cursor.execute('CREATE TABLE IF NOT EXISTS sales_data (date TEXT PRIMARY KEY, amount REAL)')
    # Error tracking table
    cursor.execute('CREATE TABLE IF NOT EXISTS error_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, attempted_date TEXT, raw_value TEXT, error_reason TEXT)')
    conn.commit()
    conn.close()

def insert_bulk_data(df):
    """Inserts data and heals the schema if it doesn't match."""
    conn = sqlite3.connect(DB_NAME)
    try:
        # Standardize types
        df['date'] = df['date'].astype(str)
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        df = df.dropna(subset=['amount'])
        
        # 'replace' ensures that if you upload a new structure, the DB adapts
        # instead of throwing an 'Execution Failed' error.
        df.to_sql('sales_data', conn, if_exists='replace', index=False, chunksize=10000)
    except Exception as e:
        # This will print the exact SQL error to your terminal
        print(f"Detailed SQL Error: {e}")
        raise e
    finally:
        conn.close()

def insert_sales_data(date, amount):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO sales_data (date, amount) VALUES (?, ?)', (date, amount))
    conn.commit()
    conn.close()

def log_error(timestamp, attempted_date, raw_value, error_reason):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO error_logs (timestamp, attempted_date, raw_value, error_reason) VALUES (?, ?, ?, ?)', 
                   (timestamp, attempted_date, raw_value, error_reason))
    conn.commit()
    conn.close()

def get_aggregated_sales(timeframe):
    conn = sqlite3.connect(DB_NAME)
    if timeframe == 'Daily':
        query = "SELECT date, amount FROM sales_data ORDER BY date"
    elif timeframe == 'Weekly':
        query = "SELECT strftime('%Y-%W', date) AS date, SUM(amount) AS amount FROM sales_data GROUP BY strftime('%Y-%W', date) ORDER BY date"
    elif timeframe == 'Yearly':
        query = "SELECT strftime('%Y', date) AS date, SUM(amount) AS amount FROM sales_data GROUP BY strftime('%Y', date) ORDER BY date"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_error_logs():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM error_logs ORDER BY id DESC", conn)
    conn.close()
    return df