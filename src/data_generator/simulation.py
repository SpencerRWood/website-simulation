import pandas as pd
import simpy
import numpy as np
import sqlite3
from datetime import timedelta
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func 
from sqlalchemy import create_engine

from .website import Session, Website
from .visitor import Visitor,generate_visitors,get_return_visitors, visitor_arrival_times,gaussian_arrivals
from .channel import Email, Display
from .models import Interaction

def simulate_visitor_sessions(env, website, visitors, arrival_times):
    ##TODO: Optimize this function
    """Simulates visitors arriving at specific times."""
    visitor_sessions = []

    for visitor, arrival_time in zip(visitors, arrival_times):
        delay = arrival_time - env.now
        if delay > 0:
            yield env.timeout(delay)

        session = Session(env, website, visitor, channel=visitor.channel)
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
    """Returns a fluctuating percentage of a total value, normally distributed around a mean."""
    min_percentage = 0.0
    max_percentage = None

    mean_percentage = params_dict["mean"]
    std_dev_percentage = params_dict["std_dev"]

    sampled_percentage = np.random.normal(loc=mean_percentage, scale=std_dev_percentage)
    sampled_percentage = np.clip(sampled_percentage, min_percentage, max_percentage)
    
    return int(total * sampled_percentage)

def run_daily_simulation(current_date
                         , db_session
                         , website_structure
                         , n_num_base_visitor_distribution
                         , campaign_activity_by_day
                         , seasonality_factor=1):
    current_date = current_date.date() if isinstance(current_date, pd.Timestamp) else current_date
    print(f"Running simulation for {current_date}")

    campaigns_today = campaign_activity_by_day.get(current_date, [])


    ##Iniatilize number of base visitors to the site for that day and multiple by seasonality_factor
    n_num_base_visitors = int((np.random.normal(n_num_base_visitor_distribution["mean"]
                                            , n_num_base_visitor_distribution["std_dev"]))*seasonality_factor)

    ##TODO: Generate visitors from marketing channel

    ##Generate base visitors, store data in dataframe
    new_visitors = generate_visitors(db_session, n_num_base_visitors, created_at=current_date)
    
    display_visitors, email_visitors = [], []

    for campaign in campaigns_today:
        if campaign['channel'] == 'Display':
            display = Display(campaign)
            display_visitors += display.generate_visitors(current_date, db_session)
        elif campaign['channel'] == 'Email':
            email_users = db_session.query(Visitor).filter(Visitor.email != None, Visitor.converted == False).all()
            email = Email(campaign)
            email_visitors += email.generate_visitors(current_date, db_session, email_users)
    
    db_session.bulk_save_objects(display_visitors + new_visitors)
    db_session.commit()

    for visitor in email_visitors:
        visitor.db_session = db_session

        if visitor.signed_up and visitor.marketing_funnel_stage == 'Consideration - Low Intent':
            visitor.marketing_funnel_stage = 'Consideration - High Intent'
            visitor.stage_last_updated_date = current_date
            visitor.save_to_db()

    ##Combine visitor types
    visitors = new_visitors + display_visitors + email_visitors
    n_num_total_visitors = len(visitors)
    
    print(f"Number of new visitors: {n_num_base_visitors}")
    print(f"Number of email visitors: {len(email_visitors)}")
    print(f"Number of display visitors: {len(display_visitors)}")
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
    interaction_objects = [Interaction(**record) for visitor in visitor_data.value for record in visitor.data]

    db_session.bulk_save_objects(interaction_objects)
    db_session.commit()