import pandas as pd
import simpy
import numpy as np
import sqlite3
from datetime import timedelta
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func 

from .website import Session, Website
from .visitor import Visitor,generate_visitors,get_return_visitors, visitor_arrival_times,gaussian_arrivals
from .database_utils import get_db_session

def simulate_visitor_sessions(env, website, visitors, arrival_times):
    ##TODO: Optimize
    """Simulates visitors arriving at specific times."""
    visitor_sessions = []

    for visitor, arrival_time in zip(visitors, arrival_times):
        delay = arrival_time - env.now
        if delay > 0:
            yield env.timeout(delay)

        session = Session(env, website, visitor)
        env.process(session.simulate_site_interactions())
        visitor_sessions.append(session)
    yield env.timeout(1) 

    # def process_visitor(visitor, arrival_time):
    #     delay = arrival_time - env.now
    #     if delay > 0:
    #         yield env.timeout(delay)
    #     session = Session(env, website, visitor)
    #     env.process(session.simulate_site_interactions())

    return visitor_sessions

def sample_percentage(total, params_dict):
    ##TODO: Make it return 10% of total - this means total + adjusted value
    ##TODO: Add all parameters to config
    """Returns a fluctuating percentage of a total value, normally distributed around a mean."""
    min_percentage = 0.0
    max_percentage = None

    mean_percentage = params_dict["mean"]
    std_dev_percentage = params_dict["std_dev"]

    sampled_percentage = np.random.normal(loc=mean_percentage, scale=std_dev_percentage)
    sampled_percentage = np.clip(sampled_percentage, min_percentage, max_percentage)
    
    return int(total * sampled_percentage)

def run_daily_simulation(current_date
                         , DB_PATH
                         , website_structure
                         , n_num_base_visitor_distribution
                         , pct_return_visitors
                         , seasonality_factor=1):
    print(f"Running simulation for {current_date}")
    db_session = get_db_session(DB_PATH)

    ##Iniatilize number of base visitors to the site for that day
    n_num_base_visitors = int((np.random.normal(n_num_base_visitor_distribution["mean"]
                                            , n_num_base_visitor_distribution["std_dev"]))*seasonality_factor)
    print(f"Number of base visitors: {n_num_base_visitors}")

    ##TODO: Generate visitors from marketing channel

    ##Generate base visitors, store data in dataframe
    new_visitors = generate_visitors(db_session, n_num_base_visitors, created_at=current_date)
    for visitor in new_visitors:
        visitor.save_to_db()

    ##Generate return visitors
    return_sample = sample_percentage(n_num_base_visitors, pct_return_visitors)

    return_visitors = get_return_visitors(db_session,return_sample,current_date)
    print(f"Number of return visitors: {len(return_visitors)}")

    for visitor in return_visitors:
        visitor.db_session = db_session

    ##Combine visitor types
    visitors = new_visitors + return_visitors
    n_num_total_visitors = len(visitors)
    print(f"Number of total visitors: {n_num_total_visitors}")

    ##Set arrival rates and normally distribute them throughout the day
    hours_of_day = np.arange(0, 24, 1)
    arrival_rates = gaussian_arrivals(hours_of_day, 12, 4) * n_num_total_visitors
    arrival_times = visitor_arrival_times(visitors, arrival_rates)

    ##Initialize and run simulation
    env = simpy.Environment()
    website = Website(env, website_structure, current_date)
    visitor_data = env.process(simulate_visitor_sessions(env, website, visitors, arrival_times))
    env.run()
    
    ##Exract interactions post simulation
    interactions = []
    for visitor in visitor_data.value:
        interactions.extend(visitor.data)
    interactions_df = pd.DataFrame(interactions)

    ##Write visitors, interactions to database table
    ##TODO: - figure out what to do with this - inefficient
    conn = sqlite3.connect(DB_PATH)
    interactions_df.to_sql('interactions', conn,if_exists='append',index=False, chunksize=500)
    conn.close()

    db_session.commit()
    db_session.close()
