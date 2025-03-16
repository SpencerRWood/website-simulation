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

def sample_percentage(total, mean_percentage=0.10, std_dev_percentage=0.02, min_percentage=0.05, max_percentage=0.15):
    ##TODO: Make it return 10% of total - this means total + adjusted value
    """Returns a fluctuating percentage of a total value, normally distributed around a mean."""
    sampled_percentage = np.random.normal(loc=mean_percentage, scale=std_dev_percentage)
    sampled_percentage = np.clip(sampled_percentage, min_percentage, max_percentage)
    
    return int(total * sampled_percentage)

def run_daily_simulation(current_date, DB_PATH, website_structure, n_num_base_visitor_distribution):
    print(f"Running simulation for {current_date}")
    db_session = get_db_session(DB_PATH)

    ##Iniatilize number of base visitors to the site for that day
    n_num_base_visitors = int(np.random.normal(n_num_base_visitor_distribution["mean"]
                                            , n_num_base_visitor_distribution["std_dev"]))
    print(f"Number of base visitors: {n_num_base_visitors}")

    ##TODO: Generate visitors from marketing channel
    ##TODO: Apply seasonality index to summed visitors

    ##Generate base visitors, store data in dataframe
    new_visitors = generate_visitors(db_session, n_num_base_visitors, created_at=current_date)
    for visitor in new_visitors:
        visitor.save_to_db()

    ##Generate return visitors
    return_sample = sample_percentage(n_num_base_visitors)
    ##TODO: func.random() is a db operation, not impacted by seeds
    # return_visitors = (
    #     db_session.query(Visitor)
    #     .filter(Visitor.created_at < current_date)
    #     .order_by(func.random())
    #     .limit(return_sample)
    #     .all()
    #     )
    
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
    ##TODO - figure out what to do with this
    conn = sqlite3.connect(DB_PATH)
    interactions_df.to_sql('interactions', conn,if_exists='append',index=False)
    conn.close()

    db_session.commit()
    db_session.close()
    return current_date + timedelta(days=1)
