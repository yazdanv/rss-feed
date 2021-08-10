import sys
from sqlalchemy import create_engine
from sqlalchemy import Boolean, Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker, joinedload
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy.sql import func

from app.core.config import settings


SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{settings.DB_USER}:{settings.DB_PASS}@"
    f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    created = Column(DateTime(timezone=True), server_default=func.now())
    updated = Column(DateTime(timezone=True), onupdate=func.now())

    def before_save(self, *args, **kwargs):
        pass

    def after_save(self, *args, **kwargs):
        pass

    def save(self, db: Session, commit=True):
        self.before_save()
        db.add(self)
        if commit:
            try:
                db.commit()
            except Exception as e:
                db.rollback()
                raise e
        self.after_save()

    def set_fields(self, validated_data, fields=None):
        set_fields_from_validator(self, validated_data, fields)

    def before_update(self, *args, **kwargs):
        pass

    def after_update(self, *args, **kwargs):
        pass

    def update(self, db: Session, validated_data, fields=None, *args, **kwargs):
        self.before_update(*args, **kwargs)
        set_fields_from_validator(self, validated_data, fields)
        db.add(self)
        db.commit()
        self.after_update(*args, **kwargs)
        return self

    def before_delete(self, *args, **kwargs):
        pass

    def after_delete(self, *args, **kwargs):
        pass

    def delete(self, db: Session, commit=True, *args, **kwargs):
        self.before_delete(*args, **kwargs)
        self.is_deleted = True
        db.add(self)
        db.commit()
        self.after_delete(*args, **kwargs)

    @classmethod
    def list(cls, db: Session, skip: int = 0, limit: int = 100):
        return db.query(cls).offset(skip).limit(limit).all()

    @classmethod
    def create(cls, db: Session, validated_data, fields=None):
        item = cls()
        item.set_fields(validated_data, fields=fields)
        item.save(db)
        return item

    @classmethod
    def eager(cls, db: Session, *args):
        cols = [joinedload(arg) for arg in args]
        return db.query.options(*cols)


def setup_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def to_camel_case(snake_str):
    components = snake_str.split("_")
    return components[0].title() + "".join(x.title() for x in components[1:])


# set fields method is used for custom update method written in BaseModel
# using it is completely optional but in some generic cases would avoid using a dedicated crud method
# it works by going through the validator fields one by one and check if it's not none and not filtered by the fields parameter
# it also handles some cases for sqlalchemy relationship
def set_fields_from_validator(db_instance, validator, fields=None):
    validator_dict = validator
    if not isinstance(validator, dict):
        validator_dict = validator.dict()
    for field, value in validator_dict.items():
        if fields is None or field in fields:
            oField = type(db_instance).__dict__.get(field).property
            fieldClass = None
            if isinstance(oField, RelationshipProperty):
                if not db_instance.__refrence_context__:
                    raise Exception(
                        "set_fields_from_validator method requires a __refrence_context__ set to the data class, with the value of __name__")
                fieldClass = getattr(
                    sys.modules[db_instance.__refrence_context__], oField.argument
                )
            oValue = getattr(db_instance, field, None)
            if isinstance(value, dict) and oValue is None:
                oValue = fieldClass()
            elif isinstance(value, list) and oValue is None:
                oValue = []
            if isinstance(value, dict):
                id = value.get("id")
                if id is not None:
                    setattr(db_instance, field + "_id", value.get("id", None))
                else:
                    set_fields_from_validator(oValue, value)
                    setattr(db_instance, field, oValue)
            elif (
                isinstance(value, list)
                and len(value) > 0
                and isinstance(value[0], dict)
            ):
                for item in value:
                    nValue = fieldClass()
                    oValue.append(set_fields_from_validator(nValue, item))
                setattr(db_instance, field, oValue)
            elif (value is not None and value != oValue) or isinstance(value, list):
                setattr(db_instance, field, value)
    return db_instance
