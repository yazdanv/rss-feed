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
        unique_name = (parsed_url.netloc + parsed_url.path).replace("/", "-")

        feed = db.query(Feed).filter(Feed.unique_name == unique_name).first()
        if not feed:
            validate_feed_url(self.url)
            feed = Feed(url=self.url, unique_name=unique_name)
            feed.save(db)
        feed.add_subscriber(db, user)

        return feed


class FeedEntryListItem(BaseIdModel):
    title: Optional[str] = None
    summary: Optional[str] = None


class FeedResponse(BaseFullModel):
    url: str
    title: Optional[str] = None
    unique_name: str
    priority: int
    entries: List[FeedEntryListItem]
    unread_count: Optional[int]

    @classmethod
    def from_user_feed(cls, db: Session, user: User, feed: Feed):
        all_feed_entries = feed.entries.count(db)
        reads = db.query(ReadState).filter(
            ReadState.feed_entry.has(feed_id=feed.id),
            ReadState.user_id == user.id,
            ReadState.is_read == True,
        ).count()

        validated = cls.from_orm(feed)
        validated.unread_count = all_feed_entries - reads
        return validated


class FeedListItem(BaseIdModel):
    title: Optional[str] = None
    unique_name: str


class FeedListResponse(BaseOrmModel):
    __root__: List[FeedListItem]


class FeedAdminValidator(BaseIdModel):
    url: Optional[AnyHttpUrl] = None
    title: Optional[str] = None
    priority: Optional[int] = None

    def create_feed(self, db: Session):
        parsed_url = urlparse(self.url)
        unique_name = (parsed_url.netloc + parsed_url.path).replace("/", "-")
        validate_feed_url(self.url)
        feed = Feed(
            url=self.url,
            unique_name=unique_name,
            title=self.title,
            priority=self.priority,
        )
        feed.save(db)

        return feed


class FeedEntryListResponse(BaseOrmModel):
    __root__: List[FeedEntryListItem]


class FeedEntryValidator(BaseFullModel):
    feed: Optional[FeedListItem] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    link: Optional[str] = None
    author: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
