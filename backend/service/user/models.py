from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(String(22), primary_key=True)
    slid = Column(String(22)) # user id from slack
    google_auth = Column(String(2048))
    team_id = Column(String(255))

class SlackTeam(Base):
	__tablename__ = 'slack_teams'
	id = Column(String(22), primary_key=True)
	team_name = Column(String(255))
	team_id = Column(String(255))
	access_token = Column(String(255)) # according to https://api.slack.com/changelog/2016-08-23-token-lengthening
	bot_token = Column(String(255)) # according to https://api.slack.com/changelog/2016-08-23-token-lengthening
	bot_user_id = Column(String(255)) # according to https://api.slack.com/changelog/2016-08-23-token-lengthening