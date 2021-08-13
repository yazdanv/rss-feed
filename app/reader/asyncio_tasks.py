import time
from datetime import datetime

import asyncio
import requests
from requests.exceptions import Timeout, ConnectionError
import feedparser
import pytz

from app.core.database import SessionLocal
from app.reader.models import Feed, FeedEntry


async def parse_feeds():
    while True:
        db = SessionLocal()
        feeds = db.query(Feed).order_by(
            Feed.updated.asc(), Feed.priority.asc()).all()
        for feed in feeds:
            asyncio.ensure_future(parse_feed(feed_id=feed.id))
        db.close()
        await asyncio.sleep(30)


async def parse_feed(feed_id: int):
    db = SessionLocal()
    feed = db.get(Feed, feed_id)
    try:
        resp = requests.get(feed.url, timeout=2)
        feed.increase_priority(db)
    except Timeout:
        feed.decrease_priority(db)
        return

    parsed = feedparser.parse(resp.content)
    # if feed is invalid, decrease priority and return the method
    if parsed.bozo == 1:
        feed.decrease_priority(db)
        return
    else:
        feed.increase_priority(db)

    # Replace time.struct_time with datetime.datetime
    for entry in parsed.entries:
        published_time = time.gmtime(time.time())
        for attr in ("published_parsed", "updated_parsed", "created_parsed"):
            try:
                published_time = getattr(entry, attr)
                break
            except AttributeError:
                continue
        entry.published_parsed = datetime.fromtimestamp(
            time.mktime(published_time)
        ).replace(tzinfo=pytz.UTC)

    last_entry = (
        db.query(FeedEntry)
        .filter(FeedEntry.feed_id == feed_id)
        .order_by(FeedEntry.published_at.desc())
        .first()
    )

    def add_entry(entry, feed_id):
        db.add(
            FeedEntry(
                feed_id=feed_id,
                title=entry.get("title", ""),
                subtitle=entry.get("subtitle", ""),
                link=entry.get("link", ""),
                author=entry.get("author", ""),
                summary=entry.get("summary", ""),
                content=entry.get("content", [{}])[0].get("value", ""),
                published_at=entry.published_parsed,
            )
        )

    if last_entry:
        add_count = len(
            [
                add_entry(entry, feed_id)
                for entry in parsed.entries
                if entry.published_parsed > last_entry.published_at
            ]
        )
    else:
        add_count = len([add_entry(entry, feed_id)
                        for entry in parsed.entries])
    db.commit()
    return add_count
