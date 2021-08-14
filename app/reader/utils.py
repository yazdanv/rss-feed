import requests
from requests.exceptions import Timeout, ConnectionError

import feedparser

from app.utils.i18n import trans
from app.utils.exceptions import CustomException


def validate_feed_url(url: str):
    try:
        resp = requests.get(url, timeout=3)
    except Timeout:
        raise CustomException(
            detail="Validation Error", errors=trans("Timeout while fetching feed url")
        )
    except ConnectionError:
        raise CustomException(
            detail="Validation Error", errors="Error resolving feed url"
        )

    parsed_feed = feedparser.parse(resp.content)
    if parsed_feed.bozo == 1:
        raise CustomException(detail="Validation Error", errors="Feed is not valid")
    return parsed_feed.feed.title