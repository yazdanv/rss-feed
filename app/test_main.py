import pytest
from fastapi.testclient import TestClient

from app.core.main import app
from app.test_data import test_data
from app.authnz.schemas import UserRegister
from app.reader.models import Feed
from app.core.database import SessionLocal
from app.reader.tasks import feed_parser

client = TestClient(app)


@pytest.fixture
def user_token():
    res = client.post("/user/login", json=test_data.user_validator.dict())
    return res.json().get("data").get("access_token")


@pytest.fixture
def user_headers(user_token):
    return {"Authorization": "Bearer %s" % (user_token)}


class BaseTest:
    def has_data(self, res):
        assert res.json().get("data") is not None
        return res.json().get("data")

    def has_data_code_200(self, res):
        assert res.status_code == 200
        return self.has_data(res)

    def has_data_code_201(self, res):
        assert res.status_code == 201
        return self.has_data(res)

    def code_200(self, res):
        assert res.status_code == 200
        return res


class TestUserBefore(BaseTest):
    user_login_data = UserRegister(
        username="yazdanv", password="123456").dict()

    @pytest.mark.order(1)
    def test_register_user(self):
        login_response = client.post("/user/login", json=self.user_login_data)
        if login_response.status_code == 200:
            client.delete(
                "/user/delete",
                headers={
                    "Authorization": "Bearer %s"
                    % (login_response.json().get("data").get("access_token"))
                },
            )
        self.has_data_code_200(client.post(
            "/user/register", json=self.user_login_data))

    @pytest.mark.order(2)
    def test_login_user(self):
        data = self.has_data_code_200(
            client.post("/user/login", json=self.user_login_data)
        )
        assert data.get("access_token") is not None


class TestFeed(BaseTest):
    @pytest.mark.order(21)
    def test_subscribe_to_feed(self, user_headers):
        data = self.has_data_code_200(
            client.post(
                "/feed/subscribe",
                json=test_data.feed_validator_item.dict(),
                headers=user_headers,
            )
        )
        assert data.get("url") == test_data.feed_validator_item.url
        test_data.feed_id = data.get("id")

    @pytest.mark.order(22)
    def test_retrieve_my_feed(self, user_headers):
        data = self.has_data_code_200(client.get(
            "/feed/my_feed", headers=user_headers))
        assert len(data) > 0

    @pytest.mark.order(22)
    def test_retrive_feed(self, user_headers):
        data = self.has_data_code_200(
            client.get("/feed/%d" % test_data.feed_id, headers=user_headers)
        )
        assert data.get("url") == test_data.feed_validator_item.url

    @pytest.mark.order(22)
    def test_priority_increase_should_succeed_on_failing_feed_retrieve(self):
        db = SessionLocal()
        feed = db.query(Feed).get(test_data.feed_id)
        feed.decrease_priority(db)
        old_priority = feed.priority
        db.close()

        feed_parser("https://google.com", feed.id)

        db = SessionLocal()
        feed = db.query(Feed).get(test_data.feed_id)
        assert old_priority < feed.priority
        db.close()

    @pytest.mark.order(23)
    def test_priority_decrease_should_succeed_on_successful_feed_retrieve(self):
        db = SessionLocal()
        feed = db.query(Feed).get(test_data.feed_id)
        feed.increase_priority(db)
        old_priority = feed.priority
        db.close()

        feed_parser(feed.url, feed.id)

        db = SessionLocal()
        feed = db.query(Feed).get(test_data.feed_id)
        assert feed.priority < old_priority
        db.close()

    @pytest.mark.order(24)
    def test_retrieve_feed_entry_list(self, user_headers):
        data = self.has_data_code_200(
            client.get("/feed_entry/list/%d" %
                       test_data.feed_id, headers=user_headers)
        )
        assert len(data) > 0
        test_data.feed_entry_id = data[0].get("id")

    # Fetch feed entry and Check Read State after fetching the feed entry
    @pytest.mark.order(26)
    def test_retrieve_feed_entry(self, user_headers):
        data = self.has_data_code_200(
            client.get("/feed_entry/%d" %
                       test_data.feed_entry_id, headers=user_headers)
        )
        assert data.get("id") == test_data.feed_entry_id

    @pytest.mark.order(27)
    def test_feed_entry_check_is_read(self, user_headers):
        data = self.has_data_code_200(
            client.get("/feed_entry/%d" %
                       test_data.feed_entry_id, headers=user_headers)
        )
        assert data.get("is_read") == True

    # mark as unread and check the read state
    @pytest.mark.order(28)
    def test_feed_entry_mark_unread(self, user_headers):
        self.code_200(
            client.post(
                "/feed_entry/mark_unread/%d" % test_data.feed_entry_id,
                headers=user_headers,
            )
        )

    @pytest.mark.order(29)
    def test_feed_entry_check_is_unread(self, user_headers):
        data = self.has_data_code_200(
            client.get("/feed_entry/%d" %
                       test_data.feed_entry_id, headers=user_headers)
        )
        assert data.get("is_read") == False

    # set to favorite and check
    @pytest.mark.order(26)
    def test_feed_entry_set_favorite_status_to_true(self, user_headers):
        self.code_200(
            client.post(
                "/feed_entry/set_favorite/%d" % test_data.feed_entry_id,
                json=test_data.set_favorite_data,
                headers=user_headers,
            )
        )

    @pytest.mark.order(27)
    def test_feed_entry_favorite_status_is_true(self, user_headers):
        data = self.has_data_code_200(
            client.get("/feed_entry/%d" %
                       test_data.feed_entry_id, headers=user_headers)
        )
        assert data.get("is_favorite") == True

    # set to unfavorite and check

    @pytest.mark.order(28)
    def test_feed_entry_set_favorite_status_to_false(self, user_headers):
        self.code_200(
            client.post(
                "/feed_entry/set_favorite/%d" % test_data.feed_entry_id,
                json=test_data.set_unfavorite_data,
                headers=user_headers,
            )
        )

    @pytest.mark.order(29)
    def test_feed_entry_favorite_status_is_false(self, user_headers):
        data = self.has_data_code_200(
            client.get("/feed_entry/%d" %
                       test_data.feed_entry_id, headers=user_headers)
        )
        assert data.get("is_favorite") == False

    # add and check if the comment is added
    @pytest.mark.order(26)
    def test_feed_entry_add_comment(self, user_headers):
        data = self.has_data_code_200(
            client.post(
                "/feed_entry/%d/add_comment" % test_data.feed_entry_id,
                json=test_data.comment_validator_item.dict(),
                headers=user_headers,
            )
        )
        assert data.get("content") == test_data.comment_validator_item.content

    @pytest.mark.order(27)
    def test_feed_entry_comment_list_should_be_more_than_zero(self, user_headers):
        data = self.has_data_code_200(
            client.get(
                "/feed_entry/%d/comments" % test_data.feed_entry_id,
                headers=user_headers,
            )
        )
        assert len(data) > 0

    @pytest.mark.order(27)
    def test_feed_entry_my_comment_list_should_be_more_than_zero(self, user_headers):
        data = self.has_data_code_200(
            client.get("/feed_entry/%d/my_comments" %
                       test_data.feed_entry_id, headers=user_headers)
        )
        print(data)
        assert len(data) > 0

    # unsubscribe from the feed

    @pytest.mark.order(49)
    def test_unsubscribe_from_feed_should_be_successful(self, user_headers):
        data = self.has_data_code_200(
            client.post(
                "/feed/unsubscribe",
                json=test_data.feed_validator_item.dict(),
                headers=user_headers,
            )
        )
        assert data.get("url") == test_data.feed_validator_item.url
