__author__ = 'infame-io'
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from model import Alerts
from settings import LOG_FILENAME, session

scheduler = BackgroundScheduler()
scheduler.start()

logging.getLogger(__name__)

logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(module)s:%(lineno)d - %(funcName)s: %(message)s')


def get_db_session():
    """ Gets database session

    :return: database session

    """

    return session()


def alerts_cleaner():
    """ Performs a bulk delete query """
    try:
        session = get_db_session()

        alerts = session.query(Alerts).filter_by(was_triggered=True)

        if alerts.count() > 0:
            alerts_cleaned = alerts.delete(synchronize_session=False)
            session.commit()
            logging.info("{} alerts cleaned from the database".format(alerts_cleaned))

        session.close()

    except Exception as e:
        logging.error("Alerts cleaner exception raised {}".format(e))
