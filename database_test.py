import sqlite3
from sqlite3 import Error
from binance.client import Client
def create_connection():
    conn = None;
    try:
        conn = sqlite3.connect('binance_db.sqlite')  # Creates a SQLite database in the local directory
        return conn
    except Error as e:
        print(e)

    return conn

def create_table(conn):
    try:
        query = '''CREATE TABLE IF NOT EXISTS trading_data (
                                id INTEGER PRIMARY KEY,
                                24h_high REAL NOT NULL,
                                24h_low REAL NOT NULL,
                                middle_price REAL NOT NULL,
                                log_time TEXT NOT NULL); '''
        conn.execute(query)
    except Error as e:
        print(e)

import datetime

def fetch_variables(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trading_data ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    return row

def update_variables(conn, values):
    query = '''INSERT INTO trading_data(24h_high, 24h_low, middle_price, log_time) VALUES(?,?,?,?)'''
    cur = conn.cursor()
    cur.execute(query, values)
    conn.commit()
    return cur.lastrowid


conn = create_connection()

# if connection is successful, create the table
if conn is not None:
    create_table(conn)
else:
    print("Error! Cannot create the database connection.")

api_key = 'uKMKnNmRBX9vWkccHW9TpFFtYn6WngsxekMKM62BhRXEKCJFa69ExXfrfRIKZ81A'
api_secret = 'pezQCPomhZzMtN8CquG6187DF4gLJ6DP6xTd71LPWHXg7nBfPMkmolEUczdtdrw1'
client = Client(api_key, api_secret)
# Fetch 24h ticker data
ticker_24h = client.get_ticker(symbol="XRPBUSD")

# Calculate variables
high_24h = float(ticker_24h['highPrice'])
low_24h = float(ticker_24h['lowPrice'])
middle_price = (high_24h + low_24h) / 2
log_time = str(datetime.datetime.now())

# Update variables in the database
update_variables(conn, (high_24h, low_24h, middle_price, log_time))

# Fetch variables from the database
print(fetch_variables(conn))