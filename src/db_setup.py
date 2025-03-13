from data_generator import database_utils
import sqlite3

conn = sqlite3.connect('website_data.db')
database_utils.create_tables(conn)
conn.close()