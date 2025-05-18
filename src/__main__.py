
import json
import random
import numpy as np
import pandas as pd
from faker import Faker
from datetime import datetime
import sqlite3
import mlflow
import tempfile

from data_generator.season import seasonal_multiplier
from data_generator.channel import build_campaign_activity_lookup
from data_generator.simulation import run_daily_simulation
from data_generator.utils import check_table_exists, initialize_campaign_table, reset_database_tables, get_db_session, flatten_dict
import json

# Set the seed globally at the highest level
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
Faker.seed(SEED)
mlflow.set_tracking_uri("http://localhost:5000")

def main(config):
    print('Logging simulation parameters...')

    with mlflow.start_run(run_name="simulation_run"):
        flat_config = flatten_dict(config)

        for key, value in flat_config.items():
            mlflow.log_param(key, value)

        # Optional: also save full config as artifact
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
            json.dump(config, tmp, indent=2)
            tmp.flush()
            mlflow.log_artifact(tmp.name, artifact_path="config")

    ##Create config dictionaries
    DB_PATH = config["DB_PATH"]
    CSV_CAMPAIGN_PATH = config["CSV_CAMPAIGN_PATH"]
    start_date = datetime.strptime(config["start_date"], "%Y-%m-%d")
    end_date = datetime.strptime(config["end_date"], "%Y-%m-%d")
    website_structure = config["website_structure"]
    n_num_base_visitor_distribution = config["n_num_base_visitors"]
    seasonal_distribution = config["seasonal_distribution"]

    ##Check is campaign_data table exists
    if not check_table_exists(DB_PATH, "campaigns"):
        initialize_campaign_table(DB_PATH, CSV_CAMPAIGN_PATH)
    
    ##Set data range for simulation
    date_range = pd.date_range(start=start_date, end=end_date)
    
    conn = sqlite3.connect(DB_PATH)

    campaign_df = pd.read_sql('SELECT * FROM campaigns', conn)
    campaign_activity_by_day = build_campaign_activity_lookup(campaign_df)

    ##Create seasonlity factor
    seasonality = seasonal_multiplier(date_range, seasonal_distribution)
    db_session = get_db_session(DB_PATH)

    for i, current_date in enumerate(date_range):
        run_daily_simulation(current_date
                             , db_session
                             , website_structure
                             , n_num_base_visitor_distribution
                             , campaign_activity_by_day
                             , seasonality[i])
    db_session.close()

if __name__ == '__main__':
    print('Starting program...')
    ##Import config file
    config_file_path = "config.json"
    with open(config_file_path, "r") as file:
        config = json.load(file)
    ##Reset database if already existing
    reset_database_tables(config)
    ##Run main file
    main(config)