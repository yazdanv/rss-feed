from app.authnz.schemas import UserRegister
from app.reader.schemas import (
    CommentValidator,
    FavoriteStateValidator,
    FeedUserValidator,
)


class TestData:
    user_validator = UserRegister(username="yazdanv", password="123456")

    feed_validator_item = FeedUserValidator(
        url="https://lincolnproject.libsyn.com/rss")

    set_favorite_data = FavoriteStateValidator(is_favorite=True).dict()
    set_unfavorite_data = FavoriteStateValidator(is_favorite=False).dict()

    comment_validator_item = CommentValidator(content="Hello From Yazdan")


test_data = TestData()
