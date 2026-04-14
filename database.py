import sqlite3
import pandas as pd

DB_NAME = "sales_database.db"

def init_db():
    """Initializes the SQLite database and creates necessary tables."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Main Sales Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales_data (
            date TEXT PRIMARY KEY,
            amount REAL
        )
    ''')
    
    # Error Logs Table for missing/bad data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS error_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            attempted_date TEXT,
            raw_value TEXT,
            error_reason TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def insert_sales_data(date, amount):
    """Inserts or updates sales data."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sales_data (date, amount) 
        VALUES (?, ?)
        ON CONFLICT(date) DO UPDATE SET amount = excluded.amount
    ''', (date, amount))
    conn.commit()
    conn.close()

def log_error(timestamp, attempted_date, raw_value, error_reason):
    """Logs bad data to the error table."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO error_logs (timestamp, attempted_date, raw_value, error_reason) 
        VALUES (?, ?, ?, ?)
    ''', (timestamp, attempted_date, raw_value, error_reason))
    conn.commit()
    conn.close()

def get_aggregated_sales(timeframe):
    """Uses SQL to aggregate data by Days, Weeks, or Years."""
    conn = sqlite3.connect(DB_NAME)
    
    if timeframe == 'Daily':
        query = "SELECT date, amount FROM sales_data ORDER BY date"
    elif timeframe == 'Weekly':
        # Groups by Year and Week Number
        query = "SELECT strftime('%Y-%W', date) AS date, SUM(amount) AS amount FROM sales_data GROUP BY strftime('%Y-%W', date) ORDER BY date"
    elif timeframe == 'Yearly':
        # Groups by Year
        query = "SELECT strftime('%Y', date) AS date, SUM(amount) AS amount FROM sales_data GROUP BY strftime('%Y', date) ORDER BY date"
        
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_error_logs():
    """Retrieves the error logs."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM error_logs ORDER BY id DESC", conn)
    conn.close()
    return df