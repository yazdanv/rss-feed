from sqlalchemy.sql.functions import func
from app.utils.i18n import trans
from app.utils.exceptions import CustomException
from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Table, DateTime
from sqlalchemy.orm import Session, relationship
from sqlalchemy.sql.schema import UniqueConstraint

from app.core.database import BaseModel
from app.authnz.models import User


class Feed(BaseModel):
    __refrence_context__ = __name__
    __tablename__ = "feeds"

    subscribers = relationship(
        "User",
        cascade="all",
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
        try:
            self.subscribers.append(user)
        except:
            raise CustomException(detail=trans(
                "Already subscribed to this feed"))
        self.save(db)

    def remove_subscriber(self, db: Session, user: User):
        try:
            index = -1
            for i in range(0, len(self.subscribers)):
                if self.subscribers[i].id == user.id:
                    index = i
                    break
            del self.subscribers[index]
        except:
            raise CustomException(detail=trans(
                "You do not subsribe to this feed"))
        self.save(db)

    def increase_priority(self, db: Session):
        if self.priority > 0:
            self.priority -= 1
            self.save(db)

    def decrease_priority(self, db: Session):
        self.priority += 1
        self.save(db)


class FeedEntry(BaseModel):
    __refrence_context__ = __name__
    __tablename__ = "entries"

    feed_id = Column(Integer, ForeignKey("feeds.id"))
    feed = relationship("Feed", cascade="all", backref="entries")
    title = Column(String)
    subtitle = Column(String)
    link = Column(String)
    author = Column(String)
    content = Column(String)
    summary = Column(String)
    published_at = Column(DateTime(timezone=True), default=func.now())


class ReadState(BaseModel):
    __refrence_context__ = __name__
    __tablename__ = "read_states"

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", cascade="all", backref="reads")
    feed_entry_id = Column(Integer, ForeignKey("entries.id"))
    feed_entry = relationship("FeedEntry", cascade="all", backref="reads")
    is_read = Column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint("user_id", "feed_entry_id",
                         name="user_entry_read_unique"),
    )

    @staticmethod
    def mark_read(db: Session, feed_entry_id: int, user: User):
        read_state = (
            db.query(ReadState)
            .filter(
                ReadState.feed_entry_id == feed_entry_id,
                ReadState.user_id == user.id
            )
            .first()
        )
        if not read_state:
            read_state = ReadState(
                feed_entry_id=feed_entry_id, user_id=user.id)
        read_state.is_read = True
        read_state.save(db)

    @staticmethod
    def mark_unread(db: Session, feed_entry_id: int, user: User):
        read_state = (
            db.query(ReadState)
            .filter(
                ReadState.feed_entry_id == feed_entry_id,
                ReadState.user_id == user.id,
                ReadState.is_read == True
            )
            .first()
        )
        if read_state:
            read_state.is_read = False
            read_state.save(db)


class Favorite(BaseModel):
    __refrence_context__ = __name__
    __tablename__ = "favorites"

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", cascade="all", backref="favorites")
    feed_entry_id = Column(Integer, ForeignKey("entries.id"))
    feed_entry = relationship("FeedEntry", cascade="all")
    is_favorite = Column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint("user_id", "feed_entry_id",
                         name="user_entry_favorite_unique"),
    )

    @staticmethod
    def favorite(db: Session, feed_entry_id: int, user: User):
        favorite = (
            db.query(Favorite)
            .filter(
                Favorite.feed_entry_id == feed_entry_id,
                Favorite.user_id == user.id
            )
            .first()
        )
        if not favorite:
            favorite = Favorite(feed_entry_id=feed_entry_id, user_id=user.id)
        favorite.is_favorite = True
        favorite.save(db)

    @staticmethod
    def unfavorite(db: Session, feed_entry_id: int, user: User):
        favorite = (
            db.query(Favorite)
            .filter(
                Favorite.feed_entry_id == feed_entry_id,
                Favorite.user_id == user.id,
                Favorite.is_favorite == True,
            )
            .first()
        )
        if favorite:
            favorite.is_favorite = False
            favorite.save(db)


class Comment(BaseModel):
    __refrence_context__ = __name__
    __tablename__ = "comments"

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", cascade="all")
    feed_entry_id = Column(Integer, ForeignKey("entries.id"))
    feed_entry = relationship("FeedEntry", cascade="all", backref="comments")
    content = Column(String)
