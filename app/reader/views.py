from app.authnz.utils import get_active_user
from fastapi import Depends, APIRouter, status
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from sqlalchemy.orm.session import Session
from sqlalchemy.sql.functions import count

from app.utils.view_types import AdminView
from app.authnz.models import User
from app.core.database import get_db
from app.reader.schemas import (
    FeedEntryListResponse,
    FeedEntryValidator,
    FeedUserValidator,
    FeedResponse,
    FeedListResponse,
    FeedAdminValidator,
)
from app.reader.models import Feed, FeedEntry

from app.utils.schema import SuccessResponse
from app.utils.exceptions import CustomException
from app.utils.i18n import trans


############################
#### Feed Admin methods #####
############################

feed_admin_router = InferringRouter()


@cbv(feed_admin_router)
class FeedAdmin(AdminView):

    serializer = FeedResponse
    list_serializer = FeedListResponse
    model = Feed

    @feed_admin_router.post("/admin/feed")
    async def create(
        self,
        item: FeedAdminValidator,
    ):
        """
        Feed Create
        """
        feed = item.create_feed(self.db)
        SuccessResponse(
            data=self.serializer.from_orm(feed),
            status_code=status.HTTP_201_CREATED,
        )

    @feed_admin_router.patch("/admin/feed/{id}")
    async def edit(
        self,
        id: int,
        item: FeedAdminValidator,
    ):
        """
        Feed Update
        """
        return self.edit_view(id, item)

    @feed_admin_router.get("/admin/feed/{id}")
    async def retrieve(self, id: int):
        """
        Feed Item
        """
        return self.retrieve_view(id)

    @feed_admin_router.delete("/admin/feed/{id}")
    async def delete(self, id: int):
        """
        Feed Delete
        """
        return self.delete_view(id)

    @feed_admin_router.get("/admin/feed")
    async def list(self):
        """
        Feed List
        """
        return self.list_view()


############################
#### Feed User methods #####
############################

feed_user_router = APIRouter()


@feed_user_router.post("/feed/subscribe")
async def subscribe_to_feed(
    feed_validator: FeedUserValidator,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
) -> SuccessResponse:
    """
    Subscrible current user to a feed by url
    """
    feed = feed_validator.subscribe_user(db, current_user)
    return SuccessResponse(
        data=FeedResponse.from_orm(feed),
        status_code=status.HTTP_201_CREATED,
    )


@feed_user_router.get("/my_feed/")
async def feed_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
) -> SuccessResponse:
    """
    Subscrible current user to a feed by url
    """
    user_feed = db.query(Feed).filter(
        Feed.subscribers.any(id=current_user.id)).all()
    return SuccessResponse(
        data=FeedListResponse.from_orm(user_feed),
        status_code=status.HTTP_200_OK,
    )


@feed_user_router.get("/feed/{id}")
async def feed_item(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
) -> SuccessResponse:
    """
    Subscrible current user to a feed by url
    """
    feed_item = db.get(Feed, id)
    if not feed_item:
        raise CustomException(detail=trans("Feed does not exist"))
    return SuccessResponse(
        data=FeedResponse.from_user_feed(
            db, feed=feed_item, user=current_user),
        status_code=status.HTTP_200_OK,
    )


############################
# FeedEntry Admin methods ##
############################

feedentry_admin_router = InferringRouter()


@cbv(feedentry_admin_router)
class FeedEntryAdmin(AdminView):

    serializer = FeedEntryValidator
    list_serializer = FeedEntryListResponse
    model = FeedEntry

    @feedentry_admin_router.post("/admin/feed_entry")
    def create(self, item: FeedEntryValidator,):
        """
        FeedEntry Create
        """
        return self.create_view(item)

    @feedentry_admin_router.patch("/admin/feed_entry/{id}")
    def edit(self, id: int, item: FeedEntryValidator,):
        """
        FeedEntry Update
        """
        return self.edit_view(id, item)

    @feedentry_admin_router.get("/admin/feed_entry/{id}")
    def retrieve(self, id: int):
        """
        FeedEntry Item
        """
        return self.retrieve_view(id)

    @feedentry_admin_router.delete("/admin/feed_entry/{id}")
    def delete(self, id: int):
        """
        FeedEntry Delete
        """
        return self.delete_view(id)

    @feedentry_admin_router.get("/admin/feed_entry")
    def list(self):
        """
        FeedEntry List
        """
        return self.list_view()
