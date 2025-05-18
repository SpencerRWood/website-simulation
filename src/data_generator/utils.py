import os
import sqlite3
import pandas as pd
from .visitor import *
from .models import *
from sqlalchemy import create_engine, text

def get_db_session(db_path="visitors.db"):
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

def initialize_campaign_table(db_path, csv_path):
    """Check if campaigns table exists; if not, create and populate it using pandas.to_sql()."""
    
    conn = sqlite3.connect(db_path)

    # Read CSV into a DataFrame
    campaign_df = pd.read_csv(csv_path)

    # Ensure date columns are formatted correctly
    campaign_df['start_date'] = pd.to_datetime(campaign_df['start_date'], format='%m/%d/%y').dt.strftime('%Y-%m-%d')
    campaign_df['end_date'] = pd.to_datetime(campaign_df['end_date'], format='%m/%d/%y').dt.strftime('%Y-%m-%d')
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

def reset_database_tables(config):
    db_path = config["DB_PATH"]
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys = OFF;"))  # Disable foreign key constraints
        conn.execute(text("DROP TABLE IF EXISTS visitors;"))
        conn.execute(text("DROP TABLE IF EXISTS interactions;"))
        conn.execute(text("DROP TABLE IF EXISTS campaigns;"))
        conn.execute(text("PRAGMA foreign_keys = ON;"))  # Re-enable constraints
    
    # Recreate tables
    Base.metadata.create_all(engine)
    print('All tables reset successfully.')

def flatten_dict(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, key, sep=sep).items())
        elif isinstance(v, (str, int, float, bool)):
            items.append((key, v))
    return dict(items)
