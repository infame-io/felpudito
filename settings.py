__author__ = 'infame-io'
import os

from sqlalchemy.orm import sessionmaker, scoped_session
from slackclient import SlackClient

from model import engine

DB_NAME = os.environ.get("DB_NAME")
LOG_FILENAME = "giro.log"

API_BASE_URL = os.environ.get("API_BASE_URL")
MARKET_ID = os.environ.get("MARKET_ID")

SLACK_DEFAULT_MSG = "Computer says no"
SLACK_API_TOKEN = os.environ.get("SLACK_API_TOKEN")
BOT_ID = os.environ.get("BOT_ID")
CRYPTO_CHANNEL = os.environ.get("CRYPTO_CHANNEL")
AT_BOT = "<@" + BOT_ID + ">"

TWILIO_CONNECTION = {
    "GOKU":
        {
            "TWILIO_SID": os.environ.get("TWILIO_SID"),
            "TWILIO_TOKEN": os.environ.get("TWILIO_TOKEN"),
            "TWILIO_PHONE": os.environ.get("TWILIO_PHONE")
        },
}

DBSession = sessionmaker(bind=engine, autoflush=True, autocommit=False)
session = scoped_session(DBSession)

slack_client = SlackClient(SLACK_API_TOKEN)
