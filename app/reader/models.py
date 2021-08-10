from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import Session, relationship
from sqlalchemy.sql.schema import UniqueConstraint

from app.core.database import BaseModel
from app.authnz.models import User


class Feed(BaseModel):
    __refrence_context__ = __name__
    __tablename__ = "feeds"

    subscribers = relationship(
        "User",
        secondary=Table(
            "user_feed",
            BaseModel.metadata,
            Column("user_id", Integer, ForeignKey("users.id")),
            Column("feed_id", Integer, ForeignKey("feeds.id")),
        ),
    )
    unique_name = Column(String, unique=True, index=True)
    url = Column(String)
    title = Column(String)
    priority = Column(Integer, default=1, index=True)

    __table_args__ = (UniqueConstraint(
        "unique_name", "url", name="name_url_unique"),)

    def add_subscriber(self, db: Session, user: User):
        self.subscribers.extend([user])
        self.save(db)


class FeedEntry(BaseModel):
    __refrence_context__ = __name__
    __tablename__ = "entries"

    feed_id = Column(Integer, ForeignKey("feeds.id"))
    feed = relationship("Feed", backref="entries")
    title = Column(String)
    subtitle = Column(String)
    link = Column(String)
    author = Column(String)
    content = Column(String)
    summary = Column(String)


class ReadState(BaseModel):
    __refrence_context__ = __name__
    __tablename__ = "read_states"

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", backref="reads")
    feed_entry_id = Column(Integer, ForeignKey("feeds.id"))
    feed_entry = relationship("FeedEntry", backref="reads")
    is_read = Column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint("user_id", "feed_entry_id",
                         name="user_entry_read_unique"),
    )


class Favorite(BaseModel):
    __refrence_context__ = __name__
    __tablename__ = "favorites"

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", backref="favorites")
    feed_entry_id = Column(Integer, ForeignKey("feeds.id"))
    feed_entry = relationship("FeedEntry")
    is_bookmarked = Column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint("user_id", "feed_entry_id",
                         name="user_entry_favorite_unique"),
    )


class Comment(BaseModel):
    __refrence_context__ = __name__
    __tablename__ = "comments"

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User")
    feed_entry_id = Column(Integer, ForeignKey("feeds.id"))
    feed_entry = relationship("FeedEntry", backref="comments")
    content = Column(String)
