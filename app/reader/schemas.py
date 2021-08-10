from app.reader.utils import validate_feed_url
from typing import List, Optional
from urllib.parse import urlparse
from pydantic.networks import AnyHttpUrl
from sqlalchemy.orm.session import Session

from app.reader.models import Feed, ReadState
from app.utils.schema import BaseFullModel, BaseIdModel, BaseOrmModel
from app.authnz.models import User


class FeedUserValidator(BaseOrmModel):
    url: AnyHttpUrl

    def subscribe_user(self, db: Session, user: User):
        parsed_url = urlparse(self.url)
        unique_name = (parsed_url.netloc + parsed_url.path).replace('/', '-')

        feed = db.query(Feed).get(Feed.unique_name == unique_name)
        if not feed:
            validate_feed_url(self.url)
            feed = Feed(url=self.url, unique_name=unique_name)
            feed.save(db)
        feed.add_subscriber(db, user)

        return feed


class FeedUserResponse(BaseFullModel):
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


class FeedUserListResponse(BaseIdModel):
    title: Optional[str] = None
    unique_name: str
