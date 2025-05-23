import uuid
import random
import pandas as pd
import numpy as np
import sqlite3
from faker import Faker
from sqlalchemy import Column, String, Integer, Boolean, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# SQLAlchemy ORM base class
from .models import Base

# Create a SQLite database connection

class Visitor(Base):
    __tablename__ = 'visitors'
    created_at = Column(DateTime, nullable=False)
    visitor_id = Column(String, primary_key=True)
    name = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    email = Column(String, nullable=True)
    signed_up = Column(Boolean, default=False)
    sign_up_timestamp = Column(DateTime, nullable=True)
    # channel = Column(String, default="Direct")
    return_visitor = Column(Boolean, default=False)
    marketing_funnel_stage = Column(String, default='Awareness')
    stage_last_updated_date = Column(DateTime, nullable=True)
    converted = Column(String, default=False)
    converted_timestamp = Column(DateTime, nullable=True)

    def __init__(self, db_session, channel='Direct', return_visitor=False, visitor_id=None, name=None, gender=None, age=None, email=None, created_at=None):
        self.db_session = db_session
        self.visitor_id = visitor_id if visitor_id else str(uuid.uuid4())
        self.channel = channel
        self.return_visitor = return_visitor
        self.signed_up = False
        self.sign_up_timestamp = None
        self.name = name
        self.gender = gender
        self.age = age
        self.email = email
        self.created_at = created_at
        self.marketing_funnel_stage = 'Awareness'
        self.stage_last_updated_date = None
        self.converted = False
        self.converted_timestamp = None
    
    def complete_signup(self, db_session=None, timestamp=None):
        """Update visitor attributes upon signup."""
        if not self.signed_up:
            fake = Faker()
            self.gender = random.choice(['Male', 'Female'])
            self.name = fake.first_name_male() + " " + fake.last_name() if self.gender == "Male" else fake.first_name_female() + " " + fake.last_name()
            self.age = random.randint(18, 80)
            self.email = fake.email()
            self.signed_up = True
            if isinstance(timestamp, str):
                timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            self.sign_up_timestamp = timestamp
            self.marketing_funnel_stage = 'Consideration - Low Intent'
            self.stage_last_updated_date = timestamp.date()

            # print(f"[DEBUG] Visitor {self.visitor_id} signed up at {self.sign_up_timestamp}")

            # Save changes to the database
            if db_session:
                self.db_session = db_session
            if self.db_session:
                self.save_to_db()
    
    def complete_conversion(self, db_session=None, timestamp=None):
        """Update visitor attributes upon conversion."""
        if not self.converted:
            self.converted_timestamp = timestamp
            self.converted = True
            self.marketing_funnel_stage = 'Conversion'
            self.stage_last_updated_date = timestamp.date()
            # print(f"[DEBUG] Visitor {self.visitor_id} signed up at {self.sign_up_timestamp}")

            # Save changes to the database
            if db_session:
                self.db_session = db_session
            if self.db_session:
                self.save_to_db()

    def save_to_db(self):
        """Insert or update visitor in the database."""
        self.db_session.merge(self)  # Upsert behavior

def generate_visitors(db_session, num_visitors, created_at):
    """Create new visitor objects and persist them in the database."""
    return [Visitor(db_session=db_session, created_at=created_at) for _ in range(num_visitors)]

def get_return_visitors(db_session, num_visitors, current_date):
    # Fetch visitor IDs first
    visitor_ids = [row[0] for row in db_session.query(Visitor.visitor_id).filter(Visitor.created_at < current_date).all()]
    if not visitor_ids:
        return []
    # Randomly sample visitor IDs
    sampled_ids = random.sample(visitor_ids, min(len(visitor_ids), num_visitors))
    # Fetch full visitor records based on sampled IDs
    return db_session.query(Visitor).filter(Visitor.visitor_id.in_(sampled_ids)).all()

def gaussian_arrivals(x, mean, sigma):
    """Set arrival rates based on gaussian (normal) distribution"""
    gaussian_constant = 1 / np.sqrt(2 * np.pi)
    x = (x - mean) / sigma
    arrival_rates = (gaussian_constant * np.exp(-0.5 * x ** 2)) / sigma
    return arrival_rates

def visitor_arrival_times(visitors, arrival_rates):
    """Generate arrival times for the exact visitors created in generate_visitors."""
    arrival_times = []
    for hour in range(24):
        num_visitors_hour = np.random.poisson(arrival_rates[hour])  # Sample visitors for this hour

        # Generate arrival times within the current hour
        for _ in range(num_visitors_hour):
            if visitors:
                arrival_time = (hour * 60) + np.random.randint(0, 60) # Random minute within the hour
                arrival_times.append(arrival_time)
            else:
                break

    return arrival_times
