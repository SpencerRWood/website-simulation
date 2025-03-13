import os
import sqlite3
import pandas as pd
from .visitor import *
from sqlalchemy import text

def get_db_session(db_path="visitors.db"):
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

# def check_database_exists(db_path):
#     """Checks if the SQLite database exists and creates it if it doesn't."""
#     if not os.path.exists(db_path):
#         print(f"Database not found at {db_path}. Creating a new one...")
#         conn = sqlite3.connect(db_path)
#         conn.close()
#         print("Database created successfully.")
#     else:
#         print(f"Database found at {db_path}.")

def check_database_exists(db_path):
    """Ensure the database and tables exist by initializing ORM."""
    session = get_db_session(db_path)
    session.close()

def initialize_campaign_table(db_path, csv_path):
    """Check if campaigns table exists; if not, create and populate it using pandas.to_sql()."""
    
    conn = sqlite3.connect(db_path)

    # Read CSV into a DataFrame
    campaign_df = pd.read_csv(csv_path)

    # Ensure date columns are formatted correctly
    campaign_df['start_date'] = pd.to_datetime(campaign_df['start_date']).dt.strftime('%Y-%m-%d')
    campaign_df['end_date'] = pd.to_datetime(campaign_df['end_date']).dt.strftime('%Y-%m-%d')

    # Load data into SQLite; if table doesn't exist, it gets created automatically
    campaign_df.to_sql('campaigns', conn, if_exists='fail', index=False)

    print("Campaign data loaded successfully.")
    conn.close()

# Check if the table exists before running the function
def check_table_exists(db_path, table_name):
    """Returns True if the given table exists in the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
    table_exists = cursor.fetchone()
    conn.close()
    return table_exists is not None

# Reset database tables
# def reset_database_tables(config):
#     db_path = config["DB_PATH"]
#     conn = sqlite3.connect(db_path)

#     cursor = conn.cursor()
#     # Execute SQL command to drop the table
#     cursor.execute("DROP TABLE IF EXISTS visitors")
#     cursor.execute("DROP TABLE IF EXISTS interactions")
#     # Commit the change and close the connection
#     conn.commit()
#     conn.close()

def reset_database_tables(config):
    db_path = config["DB_PATH"]
    session = get_db_session(db_path)
    
    session.query(Visitor).delete()  # Clear visitor table using ORM
    session.execute(text("DROP TABLE IF EXISTS interactions"))

    session.commit()
    session.close()

