import requests
import logging

from settings import MARKET_ID, API_BASE_URL


def get_market_ticker(crypto_currency):
    market_id = MARKET_ID.format(crypto_currency)
    url = "{}/v3/markets/{}/ticker".format(API_BASE_URL, market_id)
    logging.info("Requesting market data for {}: url={}".format(market_id, url))

    response = requests.get(url)
    response.raise_for_status()

    return response.json()
