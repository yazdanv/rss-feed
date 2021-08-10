from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import true

from app.authnz.schemas import UserRegister, UserProfile
from app.authnz.hashers import make_password
from app.core.database import BaseModel
from app.utils.exceptions import CustomException
from app.utils.i18n import trans


class User(BaseModel):
    __tablename__ = "users"

    username = Column(String, unique=True, index=True)
    name = Column(
        String,
    )
    profile_picture = Column(String)
    password = Column(String)

    is_provider = Column(Boolean, default=True)
    is_staff = Column(Boolean, default=True)

    permissions = Column(String)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return self.password == make_password(raw_password)

    @staticmethod
    def get_user(db: Session, user_id: int):
        return db.query(User).get(user_id)

    @staticmethod
    def get_user_by_username(db: Session, username: str):
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_users(db: Session, skip: int = 0, limit: int = 100):
        return db.query(User).offset(skip).limit(limit).all()

    @staticmethod
    def create_user(db: Session, user: UserRegister):
        db_user = User(username=user.username)
        db_user.set_password(user.password)
        db_user.save(db)
        return db_user

    def update_user(self, db: Session, user_data: UserProfile):
        self.update(db, user_data, ["name", "profile_picture"])
        return self
