__author__ = 'infame-io'
import time

from datetime import datetime, timedelta
from settings import slack_client, session

from libs import logging, scheduler, alerts_cleaner
from libs.slack_bot import parse_slack_output, handle_command, sniff

if __name__ == "__main__":
    logging.info("Starting Felpudito")
    start_time = datetime.now()
    scheduler.add_job(sniff, "cron", id="sniff", day="*", minute="*/1")
    # scheduler.add_job(sniff, "interval", id="sniff", seconds=30)
    scheduler.add_job(alerts_cleaner, "cron", id="alerts_cleaner", day="*", hour="*/6")

    if slack_client.rtm_connect(with_team_state=False):
        logging.info("Felpudito bot is connected and running")

        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel)
            time.sleep(3)

            if start_time + timedelta(hours=8) < datetime.now():
                logging.info("Freeing memory")
                scheduler.shutdown()
                session.remove()
                break
    else:
        logging.error("Connection failed to Felpudito")
        time.sleep(5)
