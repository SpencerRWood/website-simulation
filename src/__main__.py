##TODO: If someone has signed up, make sure it doesn't over write the status if they move through again
##TODO: Implement MLFlow for experiment tracking
import json
import random
import numpy as np
import pandas as pd
from faker import Faker
from datetime import datetime

from data_generator.season import seasonal_multiplier
from data_generator.simulation import run_daily_simulation
from data_generator.database_utils import check_table_exists, initialize_campaign_table, reset_database_tables, get_db_session

# Set the seed globally at the highest level
##FIXME: Number of page interactions are not setting Seeds correctly
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
Faker.seed(SEED)

def main(config):
    ##Import config file

    ##Create config dictionaries
    DB_PATH = config["DB_PATH"]
    CSV_CAMPAIGN_PATH = config["CSV_CAMPAIGN_PATH"]
    start_date = datetime.strptime(config["start_date"], "%Y-%m-%d")
    end_date = datetime.strptime(config["end_date"], "%Y-%m-%d")
    website_structure = config["website_structure"]
    n_num_base_visitor_distribution = config["n_num_base_visitors"]
    pct_return_visitors = config["pct_return_visitors"]
    seasonal_distribution = config["seasonal_distribution"]

    ##TODO: Check if database exists and if not create it
    ##Check is campaign_data table exists
    # if not check_table_exists(DB_PATH, "campaigns"):
    #     initialize_campaign_table(DB_PATH, CSV_CAMPAIGN_PATH)
    
    ##TODO: Abstract this to a module - have the config params passed through
    ##Create seasonlity factor
    
    date_range = pd.date_range(start=start_date, end=end_date)
    seasonality = seasonal_multiplier(date_range, seasonal_distribution)

    for i, current_date in enumerate(date_range):
        run_daily_simulation(current_date
                             , DB_PATH
                             , website_structure
                             , n_num_base_visitor_distribution
                             , pct_return_visitors
                             , seasonality[i])

if __name__ == '__main__':
    print('Starting program...')
    config_file_path = "config.json"
    with open(config_file_path, "r") as file:
        config = json.load(file)
    reset_database_tables(config)
    main(config)
    print('Program complete!')