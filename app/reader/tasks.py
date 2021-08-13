from sqlalchemy.sql.functions import func
from app.reader.models import Feed, FeedEntry
from app.core.database import SessionLocal, setup_db
import time
from datetime import datetime

import pytz
import requests
import feedparser
from requests.exceptions import Timeout
from celery import group, shared_task, current_app


def get_count(q):
    count_q = q.statement.with_only_columns([func.count()]).order_by(None)
    count = q.session.execute(count_q).scalar()
    return count


@shared_task
def feed_indexer_coordinator(priority):
    db = SessionLocal()
    if priority == "HIGH":
        feeds_count = get_count(db.query(Feed).filter(Feed.priority == 0))
    elif priority == "MEDIUM":
        feeds_count = get_count(db.query(Feed).filter(Feed.priority == 1))
    elif priority == "LOW":
        feeds_count = get_count(db.query(Feed).filter(Feed.priority >= 2))
    else:
        raise ValueError("Proirity not provided")
    db.close()

    def interval_seq(start, stop, step=1):
        i = start
        while (i + step) < stop:
            yield i, i + step
            i += step
        if i < stop:
            yield i, stop

    node_count = len(current_app.control.ping())
    group(
        feed_url_distributor.s(priority, i, j)
        for i, j in interval_seq(0, feeds_count, node_count)
    ).delay()


@shared_task
def feed_url_distributor(priority, beg, end):
    db = SessionLocal()
    if priority == "HIGH":
        feeds = db.query(Feed).filter(
            Feed.priority == 0).offset(beg).limit(end).all()
    elif priority == "MEDIUM":
        feeds = db.query(Feed).filter(
            Feed.priority == 1).offset(beg).limit(end).all()
    elif priority == "LOW":
        feeds = db.query(Feed).filter(
            Feed.priority >= 2).offset(beg).limit(end).all()
    else:
        raise ValueError("Proirity not provided")
    group(feed_indexer.s(feed.url, feed.id) for feed in feeds).delay()
    db.close()


@ shared_task
def feed_indexer(url, feed_id):
    db = SessionLocal()
    feed = db.get(Feed, feed_id)
    try:
        resp = requests.get(url, timeout=2)
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

    # update feed title if changed
    if feed.title is not parsed.feed.title:
        feed.title = parsed.feed.title
        db.add(feed)

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
        content = ""
        for item in entry.get("content", [{}]):
            content += item.get("value", "") + "\n"
        db.add(
            FeedEntry(
                feed_id=feed_id,
                title=entry.get("title", ""),
                subtitle=entry.get("subtitle", ""),
                link=entry.get("link", ""),
                author=entry.get("author", ""),
                summary=entry.get("summary", ""),
                content=content,
                published_at=entry.published_parsed,
            )
        )

    if last_entry:
        [
            add_entry(entry, feed_id)
            for entry in parsed.entries
            if entry.published_parsed > last_entry.published_at
        ]
    else:
        [add_entry(entry, feed_id) for entry in parsed.entries]
    db.commit()
    db.close()
