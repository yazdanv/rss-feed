from datetime import datetime
from operator import and_
from sqlalchemy.sql.expression import delete, select
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.sqltypes import Date
from app.utils.i18n import trans
from app.utils.exceptions import CustomException
from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Table, DateTime
from sqlalchemy.orm import Session, relationship
from sqlalchemy.sql.schema import UniqueConstraint

from app.core.database import BaseModel, engine
from app.authnz.models import User


user_feed_table = Table(
    "user_feed",
    BaseModel.metadata,
    Column("user_id", Integer, ForeignKey(
        "users.id", ondelete="CASCADE")),
    Column("feed_id", Integer, ForeignKey(
        "feeds.id", ondelete="CASCADE")),
)


class Feed(BaseModel):
    __refrence_context__ = __name__
    __tablename__ = "feeds"

    subscribers = relationship(
        "User",
        secondary=user_feed_table,
    )
    url = Column(String, unique=True, index=True)
    title = Column(String)
    priority = Column(Integer, default=0, index=True)

    def add_subscriber(self, db: Session, user: User):
        try:
            self.subscribers.append(user)
        except:
            raise CustomException(detail=trans(
                "Already subscribed to this feed"))
        self.save(db)

    def remove_subscriber(self, db: Session, user: User):
        filter_statement = and_(
            user_feed_table.c.feed_id == self.id, user_feed_table.c.user_id == user.id)
        item = db.bind.execute(select(user_feed_table).where(
            filter_statement)).fetchone()
        if item:
            db.bind.execute(delete(user_feed_table).where(filter_statement))
        else:
            raise CustomException(detail=trans(
                "You do not subsribe to this feed"))

    def increase_priority(self, db: Session):
        self.priority += 1
        self.save(db)

    def decrease_priority(self, db: Session):
        if self.priority > 0:
            self.priority -= 1
            self.save(db)


class UserFeedState(BaseModel):
    __refrence_context__ = __name__
    __tablename__ = "user_feed_states"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    user = relationship("User",
                        backref="feed_states")
    feed_id = Column(Integer, ForeignKey("feeds.id", ondelete="CASCADE"))
    feed = relationship("Feed", backref="states")

    last_entry_fetch_time = Column(DateTime(timezone=True), default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "feed_id",
                         name="user_feed_state_unique"),
    )

    @ classmethod
    def get_item(cls, db: Session, feed_id: int, user_id: int):
        return (
            db.query(cls)
            .filter(
                cls.feed_id == feed_id,
                cls.user_id == user_id
            )
            .first()
        )

    @ classmethod
    def update_fetch_time(cls, db: Session, feed_id: int, user_id: int):
        feed_state = cls.get_item(db, feed_id, user_id)
        if not feed_state:
            feed_state = cls(feed_id=feed_id, user_id=user_id)
        feed_state.last_entry_fetch_time = datetime.now()
        feed_state.save(db)


class FeedEntry(BaseModel):
    __refrence_context__ = __name__
    __tablename__ = "entries"

    feed_id = Column(Integer, ForeignKey("feeds.id", ondelete="CASCADE"))
    feed = relationship(
        "Feed", backref="entries")
    title = Column(String)
    subtitle = Column(String)
    link = Column(String)
    author = Column(String)
    content = Column(String)
    summary = Column(String)
    published_at = Column(DateTime(timezone=True), default=func.now())


class UserFeedEntryState(BaseModel):
    __refrence_context__ = __name__
    __tablename__ = "user_feed_entry_states"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    user = relationship("User",
                        backref="feed_entry_states")
    feed_entry_id = Column(Integer, ForeignKey(
        "entries.id", ondelete="CASCADE"))
    feed_entry = relationship(
        "FeedEntry", backref="states")

    is_read = Column(Boolean, default=False)
    read_time = Column(DateTime)

    is_favorite = Column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint("user_id", "feed_entry_id",
                         name="user_feed_entry_state_unique"),
    )

    @ classmethod
    def get_item(cls, db: Session, feed_entry_id: int, user_id: int):
        return (
            db.query(cls)
            .filter(
                cls.feed_entry_id == feed_entry_id,
                cls.user_id == user_id
            )
            .first()
        )

    @ classmethod
    def get_or_create(cls, db: Session, feed_entry_id: int, user_id: int):
        user_state = cls.get_item(db, feed_entry_id, user_id)
        if not user_state:
            user_state = cls(
                feed_entry_id=feed_entry_id, user_id=user_id)
        return user_state

    @ classmethod
    def mark_read(cls, db: Session, feed_entry_id: int, user_id: int):
        user_state = cls.get_or_create(db, feed_entry_id, user_id)
        user_state.is_read = True
        user_state.read_time = datetime.now()
        user_state.save(db)

    @ classmethod
    def mark_unread(cls, db: Session, feed_entry_id: int, user_id: int):
        user_state = cls.get_item(db, feed_entry_id, user_id)
        if user_state and user_state.is_read:
            user_state.is_read = False
            user_state.save(db)

    @ classmethod
    def favorite(cls, db: Session, feed_entry_id: int, user_id: int):
        user_state = cls.get_or_create(db, feed_entry_id, user_id)
        user_state.is_favorite = True
        user_state.save(db)

    @ classmethod
    def unfavorite(cls, db: Session, feed_entry_id: int, user_id: int):
        user_state = cls.get_item(db, feed_entry_id, user_id)
        if user_state and user_state.is_favorite:
            user_state.is_favorite = False
            user_state.save(db)


class Comment(BaseModel):
    __refrence_context__ = __name__
    __tablename__ = "comments"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    user = relationship("User")
    feed_entry_id = Column(Integer, ForeignKey(
        "entries.id", ondelete="CASCADE"))
    feed_entry = relationship(
        "FeedEntry", backref="comments")
    content = Column(String)
