from app.utils.i18n import trans
from app.utils.exceptions import CustomException
import datetime
from app.authnz.schemas import UserProfile, UserPublicProfile
from app.reader.utils import validate_feed_url
from typing import List, Optional
from urllib.parse import urlparse
from pydantic.networks import AnyHttpUrl
from sqlalchemy.orm.session import Session

from app.reader.models import Comment, Favorite, Feed, FeedEntry, ReadState
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

    def unsubscribe_user(self, db: Session, user: User):
        parsed_url = urlparse(self.url)
        unique_name = (parsed_url.netloc + parsed_url.path).replace("/", "-")

        feed = db.query(Feed).filter(Feed.unique_name == unique_name).first()
        if not feed:
            raise CustomException(
                detail=trans(
                    "You do not subsribe to this feed, Feed does not exist")
            )

        feed.remove_subscriber(db, user)

        return feed


class FeedEntryListItem(BaseIdModel):
    title: Optional[str] = None
    summary: Optional[str] = None


class FeedResponse(BaseFullModel):
    url: str
    title: Optional[str] = None
    unique_name: str
    priority: int
    unread_count: Optional[int]

    @classmethod
    def for_user(cls, db: Session, user: User, feed: Feed):
        all_feed_entries = len(feed.entries)
        reads = (
            db.query(ReadState)
            .filter(
                ReadState.feed_entry.has(feed_id=feed.id),
                ReadState.user_id == user.id,
                ReadState.is_read == True,
            )
            .count()
        )

        validated = cls.from_orm(feed)
        validated.unread_count = all_feed_entries - reads
        return validated


class FeedListItem(BaseIdModel):
    title: Optional[str] = None
    unique_name: Optional[str] = None


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


class FeedEntryCommentItem(BaseOrmModel):
    user: UserPublicProfile
    content: str
    created: datetime.datetime


class FeedEntryValidator(BaseFullModel):
    feed: Optional[FeedListItem] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    link: Optional[str] = None
    author: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None

    comments: List[FeedEntryCommentItem]
    is_read: Optional[bool] = None
    is_favorite: Optional[bool] = None

    @staticmethod
    def for_user(db: Session, user: User, feed_entry: FeedEntry):
        feed_entry_validated = FeedEntryValidator.from_orm(feed_entry)
        feed_entry_validated.is_read = (
            db.query(ReadState)
            .filter(
                ReadState.feed_entry_id == feed_entry.id,
                ReadState.user_id == user.id,
                ReadState.is_read == True,
            )
            .first()
            is not None
        )
        feed_entry_validated.is_favorite = (
            db.query(Favorite)
            .filter(
                Favorite.feed_entry_id == feed_entry.id,
                Favorite.user_id == user.id,
                Favorite.is_favorite == True,
            )
            .first()
            is not None
        )
        return feed_entry_validated


class FavoriteStateValidator(BaseOrmModel):
    is_favorite: bool


class CommentValidator(BaseIdModel):
    content: str

    def create(self, db: Session, feed_entry_id: int, user: User):
        comment = Comment(
            feed_entry_id=feed_entry_id, user_id=user.id, content=self.content
        )
        comment.save(db)
        return comment


class CommentResponse(BaseFullModel):
    feed_entry: FeedEntryListItem
    content: str


class CommentListItem(BaseOrmModel):
    feed_entry: FeedEntryListItem
    content: str
    created: datetime.datetime


class CommentListResponse(BaseOrmModel):
    __root__: List[CommentListItem]
