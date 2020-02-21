__author__ = 'infame-io'
import logging

from twilio.rest import Client
from settings import TWILIO_CONNECTION


def create_twilio_call(username, message):
    try:
        client = Client(TWILIO_CONNECTION[username]["TWILIO_SID"], TWILIO_CONNECTION[username]["TWILIO_TOKEN"])

        call = client.calls.create(twiml="<Response><Say>{}</Say></Response>".format(message),
                                   to=TWILIO_CONNECTION[username]["TWILIO_PHONE"],
                                   from_=TWILIO_CONNECTION[username]["TWILIO_PHONE"]
                                   )

        logging.info("Call created: call_id={}, username={}, call_msg={}".format(call.sid, username, message))

    except Exception as ex:
        logging.error("Twilio call failed. error={}, username={}, call_msg={}".format(ex, username, message))
