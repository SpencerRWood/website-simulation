import uuid
import random
import pandas as pd
import numpy as np
import sqlite3
from faker import Faker
from sqlalchemy import Column, String, Integer, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLAlchemy ORM base class
Base = declarative_base()

# Create a SQLite database connection

class Visitor(Base):
    __tablename__ = 'visitors'

    visitor_id = Column(String, primary_key=True)
    name = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    email = Column(String, nullable=True)
    signed_up = Column(Boolean, default=False)
    channel = Column(String, default="Direct")
    return_visitor = Column(Boolean, default=False)

    def __init__(self, session, channel='Direct', return_visitor=False, visitor_id=None, name=None, gender=None, age=None, email=None):
        self.session = session  # Attach SQLAlchemy session for DB interactions
        self.visitor_id = visitor_id if visitor_id else str(uuid.uuid4())
        self.channel = channel
        self.return_visitor = return_visitor
        self.signed_up = False
        self.name = name
        self.gender = gender
        self.age = age
        self.email = email

    def complete_signup(self, session=None):
        """Update visitor attributes upon signup."""
        if not self.signed_up:
            fake = Faker()
            self.gender = random.choice(['Male', 'Female'])
            self.name = fake.first_name_male() + " " + fake.last_name() if self.gender == "Male" else fake.first_name_female() + " " + fake.last_name()
            self.age = random.randint(18, 80)
            self.email = fake.email()
            self.signed_up = True

            # Save changes to the database
            if session:
                self.session = session
            if self.session:
                self.save_to_db()

    def save_to_db(self):
        """Insert or update visitor in the database."""
        self.session.merge(self)  # Upsert behavior
        self.session.commit()

    @classmethod
    def get_from_db(cls, session, visitor_id):
        """Retrieve visitor from the database by ID."""
        return session.query(cls).filter_by(visitor_id=visitor_id).first()

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
            'signed_up': self.signed_up
        }
def generate_visitors(session, num_visitors):
    """Create new visitor objects and persist them in the database."""
    visitors = [Visitor(session=session) for _ in range(num_visitors)]
    for visitor in visitors:
        visitor.save_to_db()
    return visitors

# class Visitor:
#     def __init__(self, channel = 'Direct', return_visitor=False, visitor_id=None, name=None, gender=None, age=None, email=None):
              
#         fake = Faker()
#         self.visitor_id = visitor_id if visitor_id else str(uuid.uuid4())
#         self.return_visitor = return_visitor
#         self.channel = channel
#         self.signed_up =False
#         self.name = None
#         self.gender = None
#         self.age = None
#         self.email = None
#         self.signed_up = False  # Track if the visitor has signed up

#     def complete_signup(self):
#         if not self.signed_up:
#             fake = Faker()
#             self.gender = random.choice(['Male', 'Female'])
#             if self.gender == "Male":
#                 self.name = fake.first_name_male() + " " + fake.last_name()
#             else:
#                 self.name = fake.first_name_female() + " " + fake.last_name()
#             self.age = random.randint(18, 80)
#             self.email = fake.email()
#             self.signed_up = True 

#     def to_dict(self):
#         """Convert visitor object to dictionary format."""
#         return {
#             'visitor_id': self.visitor_id,
#             'name': self.name if self.signed_up else None,
#             'gender': self.gender if self.signed_up else None,
#             'age': self.age if self.signed_up else None,
#             'email': self.email if self.signed_up else None,
#         }
# # def assign_channel(channel_distribution):
# #     return np.random.choice(list(channel_distribution.keys()), p=list(channel_distribution.values()))

# def generate_visitors(num_visitors):
#     """Create and return a list of visitor objects."""
#     #channel = assign_channel(channel_distribution)
#     return [Visitor() for _ in range(num_visitors)]

# def get_return_visitors(DB_PATH, n_num_return_visitors):
#     """Fetch past visitors from the database and return a subset as returning visitors."""
#     try:
#         conn = sqlite3.connect(DB_PATH)
#         query = "SELECT * FROM visitors"
#         past_visitors = pd.read_sql(query, conn)
#         conn.close()
#     except:
#         return []
    
#     return_visitors = past_visitors.sample(n=n_num_return_visitors, replace=False).to_dict(orient='records')
#     return return_visitors

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

