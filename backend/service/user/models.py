from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(String(22), primary_key=True)
    slid = Column(String(22))
    google_auth = Column(String(2048))
