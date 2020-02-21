__author__ = 'infame-io'
import os
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Alerts(Base):
    __tablename__ = 'alerts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, default="")
    price_type = Column(String)
    alert_type = Column(String, default="alert")
    crypto_currency = Column(String)
    price = Column(String)
    was_triggered = Column(Boolean, default=False)


DB_NAME = os.environ.get("DB_NAME")
engine = create_engine("sqlite:///db/{}".format(DB_NAME), pool_recycle=3600)

Base.metadata.create_all(engine)
