##FIXME: Fix visitor channel attribute - need it to be at the session level
##FIXME: Total visitors generated aren't 100% interacting with the website - need to debug what is going on
##TODO: Implement logging

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
Base = declarative_base()

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

    def __init__(self, db_session, channel='Direct', return_visitor=False, visitor_id=None, name=None, gender=None, age=None, email=None, created_at=None):
        self.db_session = db_session  # Attach SQLAlchemy session for DB interactions
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

            # print(f"[DEBUG] Visitor {self.visitor_id} signed up at {self.sign_up_timestamp}")

            # Save changes to the database
            if db_session:
                self.db_session = db_session
            if self.db_session:
                self.save_to_db()

    def save_to_db(self):
        """Insert or update visitor in the database."""
        self.db_session.merge(self)  # Upsert behavior
        self.db_session.commit()

    @classmethod
    def get_from_db(cls, db_session, visitor_id):
        """Retrieve visitor from the database by ID."""
        return db_session.query(cls).filter_by(visitor_id=visitor_id).first()

    def to_dict(self):
        """Convert visitor object to dictionary format."""
        return {
            'visitor_id': self.visitor_id,
            'name': self.name if self.signed_up else None,
            'gender': self.gender if self.signed_up else None,
            'age': self.age if self.signed_up else None,
            'email': self.email if self.signed_up else None,
            'channel': self.channel,
            'return_visitor': self.return_visitor,
            'signed_up': self.signed_up,
            'sign_up_timestamp': self.sign_up_timestamp
        }
def generate_visitors(db_session, num_visitors, created_at):
    """Create new visitor objects and persist them in the database."""
    visitors = [Visitor(db_session=db_session, created_at=created_at) for _ in range(num_visitors)]
    db_session.bulk_save_objects(visitors)
    db_session.commit()

    return visitors

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

