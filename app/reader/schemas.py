from sqlalchemy.orm.session import Session
from app.reader.models import Feed, ReadState
from typing import List, Optional

from pydantic.networks import AnyHttpUrl
from app.utils.schema import BaseIdModel, BaseOrmModel
from app.authnz.models import User


class FeedUserValidator(BaseOrmModel):
    url: AnyHttpUrl


class FeedUserResponse(BaseOrmModel):
    url: str
    title: Optional[str] = None
    unique_name: str
    priority: int
    unread_count: Optional[int]

    @classmethod
    def from_user_feed(cls, db: Session, user: User, feed: Feed):
        all_feed_entries = feed.entries.count()
        reads = db.query(ReadState).filter(ReadState.feed_entry.has(feed_id=feed.id),
                                           ReadState.user_id == user.id,
                                           ReadState.is_read == True).count()
        validated = cls.from_orm(feed)
        validated.unread_count = all_feed_entries - reads
