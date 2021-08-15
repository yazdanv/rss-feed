import datetime
from typing import List, Optional

from sqlalchemy.sql.elements import and_, not_, or_
from sqlalchemy.orm.session import Session
from pydantic.networks import AnyHttpUrl

from app.utils.i18n import trans
from app.utils.exceptions import CustomException
from app.authnz.schemas import UserPublicProfile
from app.reader.utils import validate_feed_url
from app.reader.tasks import feed_parser
from app.reader.models import (
    Comment,
    Feed,
    FeedEntry,
    UserFeedEntryState,
    UserFeedState,
)
from app.utils.schema import BaseFullModel, BaseIdModel, BaseOrmModel
from app.authnz.models import User


class FeedUserValidator(BaseOrmModel):
    url: AnyHttpUrl

    def subscribe_user(self, db: Session, user: User):
        feed = db.query(Feed).filter(Feed.url == self.url).first()
        if not feed:
            feed_title = validate_feed_url(self.url)
            feed = Feed(url=self.url, title=feed_title)
            feed.save(db)
            feed_parser.s(feed.url, feed.id)
        feed.add_subscriber(db, user)

        return feed

    def unsubscribe_user(self, db: Session, user: User):
        feed = db.query(Feed).filter(Feed.url == self.url).first()
        if not feed:
            raise CustomException(detail=trans("Feed does not exist"))

        feed.remove_subscriber(db, user)

        return feed


class FeedEntryListItem(BaseIdModel):
    title: Optional[str] = None
    summary: Optional[str] = None

    is_read: Optional[bool] = False
    is_favorite: Optional[bool] = False
    is_new: Optional[bool] = True


class FeedResponse(BaseFullModel):
    url: str
    title: Optional[str] = None
    priority: int
    unread_count: Optional[int]

    @classmethod
    def for_user(cls, db: Session, user_id: int, feed: Feed):
        all_feed_entries = len(feed.entries)
        reads = (
            db.query(UserFeedEntryState)
            .filter(
                UserFeedEntryState.feed_entry.has(feed_id=feed.id),
                UserFeedEntryState.user_id == user_id,
                UserFeedEntryState.is_read == True,
            )
            .count()
        )

        validated = cls.from_orm(feed)
        validated.unread_count = all_feed_entries - reads
        return validated


class FeedListItem(BaseIdModel):
    title: Optional[str] = None
    url: Optional[str] = None


class FeedListResponse(BaseOrmModel):
    __root__: List[FeedListItem]


class FeedAdminValidator(BaseIdModel):
    url: Optional[AnyHttpUrl] = None
    priority: Optional[int] = None

    def create_feed(self, db: Session):
        feed_title = validate_feed_url(self.url)
        feed = Feed(
            url=self.url,
            title=feed_title,
            priority=self.priority,
        )
        feed.save(db)
        feed_parser.s(feed.url, feed.id)

        return feed


class FeedEntryListResponse(BaseOrmModel):
    __root__: List[FeedEntryListItem]

    @staticmethod
    def list_for_user(db: Session, feed_id: int, user_id: int, index: int, total: int):
        list_of_entries = []
        # fetch state of the feed
        feed_state = UserFeedState.get_item(db, feed_id, user_id)

        # construct the joined query for entry and state
        user_has_state_filter = and_(
            UserFeedEntryState.user_id == user_id,
            FeedEntry.id == UserFeedEntryState.feed_entry_id,
        )
        filter_statement = and_(
            FeedEntry.feed_id == feed_id,
            or_(user_has_state_filter, not_(
                FeedEntry.states.any(user_id=user_id))),
        )
        query = (
            db.query(FeedEntry, UserFeedEntryState)
            .order_by(FeedEntry.id.desc())
            .distinct(FeedEntry.id)
            .filter(filter_statement)
        )

        # read from query and construct FeedEntryListItems
        for feed_entry, user_state in query.offset(index).limit(total).all():
            item = FeedEntryListItem.from_orm(feed_entry)
            if feed_entry.id == user_state.feed_entry_id:
                item.is_read = user_state.is_read
                item.is_favorite = user_state.is_favorite
            if feed_state:
                item.is_new = feed_state.last_entry_fetch_time < feed_entry.created
            list_of_entries.append(item)
        UserFeedState.update_fetch_time(db, feed_id, user_id)
        return FeedEntryListResponse(__root__=list_of_entries)


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
    is_read: Optional[bool] = False
    read_time: Optional[datetime.datetime] = None
    is_favorite: Optional[bool] = False

    @staticmethod
    def for_user(db: Session, user_id: User, feed_entry: FeedEntry):
        feed_entry_validated = FeedEntryValidator.from_orm(feed_entry)
        user_state = UserFeedEntryState.get_item(db, feed_entry.id, user_id)
        if user_state:
            feed_entry_validated.is_read = user_state.is_read
            feed_entry_validated.is_favorite = user_state.is_favorite
            feed_entry_validated.read_time = user_state.read_time
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


class CommentListItem(BaseIdModel):
    feed_entry: FeedEntryListItem
    content: str
    created: datetime.datetime


class CommentListResponse(BaseOrmModel):
    __root__: List[CommentListItem]
