from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    visitor_id = Column(String, nullable=False)                 
    channel = Column(String)
    page = Column(String)
    interaction = Column(String)
    element = Column(String)
    timestamp = Column(DateTime)