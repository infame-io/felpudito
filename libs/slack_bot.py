__author__ = 'infame-io'
import re

from model import Alerts
from libs import logging, get_db_session, scheduler
from libs.btcmarkets import get_market_ticker
from libs.twilio_bot import create_twilio_call
from settings import slack_client, AT_BOT, CRYPTO_CHANNEL, SLACK_DEFAULT_MSG, TWILIO_CONNECTION


def sniff():
    """ Keeps an eye on market prices and triggers alert when price match the desire condition"""

    session = get_db_session()

    try:

        alerts = session.query(Alerts).filter_by(was_triggered=False, alert_type="call")

        if alerts.count() > 0:
            logging.info("Processing {} alert(s)".format(alerts.count()))

            for alert in alerts:
                trigger_call = False
                twilio_message = ""

                try:
                    username = alert.username.upper()
                    crypto_currency = alert.crypto_currency.upper()
                    price = float(alert.price)
                    price_type = alert.price_type

                    market_ticker = get_market_ticker(crypto_currency)

                    best_bid = market_ticker.get("bestBid", 0.0)
                    best_ask = market_ticker.get("bestAsk", 0.0)

                    logging.info("Alert: alert_id={}, username={}, price_type={}, price=${:0,.2f}, "
                                 "crypto_currency={},".format(alert.id, username, price_type, price, crypto_currency))

                    if price_type == "ask" and float(best_ask) <= price:
                        trigger_call = True
                        twilio_message = "{} {} price is ${}".format(crypto_currency, price_type, float(best_ask))

                    if price_type == "bid" and float(best_bid) >= price:
                        trigger_call = True
                        twilio_message = "{} {} price is ${}".format(crypto_currency, price_type, float(best_bid))

                    if twilio_message and trigger_call:
                        scheduler.add_job(create_twilio_call, args=[username, twilio_message])

                    if not alert.was_triggered:
                        alert.was_triggered = True
                        session.commit()

                except Exception as ex:
                    logging.error("Exception raised when processing alert_id={}, error={}".format(alert.id, ex))

    except Exception as ex:
        logging.error("Exception raised: {}".format(ex))

    session.close()


def handle_command(command, channel):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    logging.info("Handling command {} on channel {}".format(command, channel))

    if channel == CRYPTO_CHANNEL:
        if command.startswith("help"):
            slack_msg = "Alert: alert when XRP bid price 9000\n " \
                        "Call: call Goku when XRP ask price 10000\n" \
                        "Cancel: cancel 1,2,3\n" \
                        "Info: info XRP\n" \
                        "Pending: pending"
            slack_client.api_call("chat.postMessage", channel=CRYPTO_CHANNEL, text=slack_msg, as_user=True)

        if command.startswith("reset"):
            slack_msg = "All alerts deleted"

            session = get_db_session()
            session.query(Alerts).delete()
            logging.info(slack_msg)
            session.close()

            slack_client.api_call("chat.postMessage", channel=CRYPTO_CHANNEL, text=slack_msg, as_user=True)

        if command.startswith("pending"):
            session = get_db_session()
            alerts = session.query(Alerts).filter_by(was_triggered=False)

            if alerts.count() > 0:
                slack_msg = ""
                for alert in alerts:
                    msg = "{}.- {} {} when {} {} price reaches ${:0,.2f}".format(alert.id, alert.alert_type.title(),
                                                                                 alert.username,
                                                                                 alert.crypto_currency.upper(),
                                                                                 alert.price_type, float(alert.price))
                    logging.info(msg)

                    slack_msg += msg + "\n"

            else:
                slack_msg = "No alerts have been set"
                logging.info(slack_msg)

            session.close()

            slack_client.api_call("chat.postMessage", channel=channel, text=slack_msg, as_user=True)

        if command.startswith("cancel"):
            slack_msg = SLACK_DEFAULT_MSG
            if re.match(r'^\d+(?:,\d+)?', command[len("cancel "):]):
                _alerts = re.sub(r'\s+', '', command[len("cancel "):])
                ids = _alerts.split(",")
                session = get_db_session()

                alerts = session.query(Alerts).filter_by(was_triggered=False)
                if alerts.count() > 0:
                    for alert in alerts:
                        if str(alert.id) in ids:
                            session.delete(alert)
                            session.commit()

                            ids.remove(str(alert.id))

                    slack_msg = "Alert(s) deleted"

                session.close()

                slack_client.api_call("chat.postMessage", channel=channel, text=slack_msg, as_user=True)

        if command.startswith("call"):
            slack_msg = SLACK_DEFAULT_MSG
            try:
                price_types = ["ask", "bid"]
                data = command[len('call '):].split(" ")

                if len(data) != 6:
                    raise ValueError("Unexpected data size")

                username = data[0].upper()
                crypto_currency = data[2].upper()
                price_type = data[3].lower()
                price = float(data[5])

                if "S" in data[5]:
                    raise ValueError("Unexpected character in price")

                if username not in TWILIO_CONNECTION.keys():
                    raise ValueError("User {} not in settings")

                if all([price_type in price_types, bool(re.match(r"^\w{3}$", crypto_currency)), price > 0, username]):
                    session = get_db_session()

                    alert = Alerts(crypto_currency=crypto_currency, price_type=price_type, price=price,
                                   username=username, alert_type="call")

                    session.add(alert)
                    session.commit()

                    logging.info("Call {} added: crypto_currency={}, price_type={}, "
                                 "price=${:0,.2f}".format(username, crypto_currency, price_type, float(price)))

                    session.close()

                    slack_msg = "{} will receive a call when {} {} price " \
                                "reaches ${:0,.2f}".format(username, crypto_currency, price_type, float(price))

            except Exception as ex:
                logging.error("Call creation failed. Error: {}".format(ex))

            slack_client.api_call("chat.postMessage", channel=channel, text=slack_msg, as_user=True)

        if command.startswith("alert"):
            slack_msg = SLACK_DEFAULT_MSG
            try:
                price_types = ["ask", "bid"]
                data = command[len('alert '):].split(" ")

                if len(data) != 5:
                    raise ValueError("Unexpected data size")

                crypto_currency = data[1].upper()
                price_type = data[2].lower()
                price = float(data[4])

                if "S" in data[4]:
                    raise ValueError("Unexpected character in price")

                if all([price_type in price_types, bool(re.match(r"^\w{3}$", crypto_currency)), price > 0]):
                    session = get_db_session()

                    alert = Alerts(crypto_currency=crypto_currency, price_type=price_type, price=price)

                    session.add(alert)
                    session.commit()

                    logging.info("Alert added: crypto_currency={}, price_type={}, "
                                 "price=${:0,.2f}".format(crypto_currency, price_type, float(price)))

                    session.close()

                    slack_msg = "Alert for {} {} price ${:0,.2f} created".format(crypto_currency, price_type,
                                                                                 float(price))

            except Exception as ex:
                logging.error("Alert creation failed. Error: {}".format(ex))

            slack_client.api_call("chat.postMessage", channel=channel, text=slack_msg, as_user=True)

        if command.startswith("info"):
            slack_msg = SLACK_DEFAULT_MSG
            try:
                data = command[len('info '):].split(" ")

                if len(data) != 1:
                    raise ValueError("Unexpected data size")

                crypto_currency = data[0].upper()

                if len(crypto_currency) != 3:
                    raise ValueError("Unexpected crypto name")

                data = get_market_ticker(crypto_currency)

                best_bid = data.get("bestBid", 0.0)
                best_ask = data.get("bestAsk", 0.0)
                volume_24h = data.get("volume24h", 0.0)
                price_24h = data.get("price24h", 0.0)
                low_24h = data.get("low24h", 0.0)
                high_24h = data.get("high24h", 0.0)

                slack_msg = "Best BID:\t{}\nBest ASK:\t{}\nVolume 24h:\t{}\n" \
                            "Price 24h:\t{}\n Low 24h:\t{}\nHigh 24h:\t{}".format(best_bid, best_ask, volume_24h,
                                                                                  price_24h, low_24h, high_24h)

            except Exception as ex:
                logging.error("Market data failed. Error: {}".format(ex))

            slack_client.api_call("chat.postMessage", channel=channel, text=slack_msg, as_user=True)


def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output

    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                return output['text'].split(AT_BOT)[1].strip(), output['channel']

    return None, None
