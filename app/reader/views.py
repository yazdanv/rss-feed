from fastapi import Depends, APIRouter, status
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from sqlalchemy.orm.session import Session
from sqlalchemy.sql.functions import count

from app.core.database import get_db
from app.utils.schema import SuccessResponse
from app.utils.exceptions import CustomException
from app.utils.i18n import trans
from app.authnz.utils import get_active_user
from app.utils.view_types import AdminView
from app.authnz.models import User
from app.reader.schemas import (
    CommentListResponse,
    CommentResponse,
    CommentValidator,
    FavoriteStateValidator,
    FeedEntryListResponse,
    FeedEntryValidator,
    FeedUserValidator,
    FeedResponse,
    FeedListResponse,
    FeedAdminValidator,
)
from app.reader.models import Comment, Feed, FeedEntry, UserFeedEntryState


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
    def create(
        self,
        item: FeedAdminValidator,
    ):
        """
        Feed Create
        """
        feed = item.create_feed(self.db)
        return SuccessResponse(
            data=self.serializer.from_orm(feed),
            status_code=status.HTTP_201_CREATED,
        )

    @feed_admin_router.patch("/admin/feed/{id}")
    def edit(
        self,
        id: int,
        item: FeedAdminValidator,
    ):
        """
        Feed Update
        """
        return self.edit_view(id, item)

    @feed_admin_router.get("/admin/feed/{id}")
    def retrieve(self, id: int):
        """
        Feed Item
        """
        return self.retrieve_view(id)

    @feed_admin_router.delete("/admin/feed/{id}")
    def delete(self, id: int):
        """
        Feed Delete
        """
        return self.delete_view(id)

    @feed_admin_router.get("/admin/feed")
    def list(self):
        """
        Feed List
        """
        return self.list_view()


############################
#### Feed User methods #####
############################

feed_user_router = APIRouter()


@feed_user_router.post("/feed/subscribe")
def subscribe_to_feed(
    feed_validator: FeedUserValidator,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
) -> SuccessResponse:
    """
    Subscrible current user to a feed by url
    """
    feed = feed_validator.subscribe_user(db, current_user)
    return SuccessResponse(
        message=trans("Subscribed to feed"),
        data=FeedResponse.from_orm(feed),
        status_code=status.HTTP_200_OK,
    )


@feed_user_router.post("/feed/unsubscribe")
def unsubscribe_to_feed(
    feed_validator: FeedUserValidator,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
) -> SuccessResponse:
    """
    Unsubscrible current user from a feed by url
    """
    feed = feed_validator.unsubscribe_user(db, current_user)
    return SuccessResponse(
        message=trans("Unsubscribed from feed"),
        data=FeedResponse.from_orm(feed),
        status_code=status.HTTP_200_OK,
    )


@feed_user_router.get("/feed/my_feed")
def feed_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
) -> SuccessResponse:
    """
    Current User (Logged in user) subscribed feed list
    """
    user_feed = db.query(Feed).filter(
        Feed.subscribers.any(id=current_user.id)).all()
    return SuccessResponse(
        data=FeedListResponse.from_orm(user_feed),
        status_code=status.HTTP_200_OK,
    )


@feed_user_router.get("/feed/{id}")
def feed_item(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
) -> SuccessResponse:
    """
    Detail of feed
    """
    feed_item = db.get(Feed, id)
    if not feed_item:
        raise CustomException(detail=trans("Feed does not exist"))
    return SuccessResponse(
        data=FeedResponse.for_user(
            db, feed=feed_item, user_id=current_user.id),
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
    def create(
        self,
        item: FeedEntryValidator,
    ):
        """
        FeedEntry Create
        """
        return self.create_view(item)

    @feedentry_admin_router.patch("/admin/feed_entry/{id}")
    def edit(
        self,
        id: int,
        item: FeedEntryValidator,
    ):
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


############################
## FeedEntry User methods ##
############################


feedentry_user_router = APIRouter()


@feedentry_user_router.post("/feed_entry/mark_unread/{feed_entry_id}")
def mark_entry_unread(
    feed_entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
) -> SuccessResponse:
    """
    Mark FeedEntry with the given feed_entry_id to unread (for current user)
    """
    UserFeedEntryState.mark_unread(db, feed_entry_id, current_user.id)
    return SuccessResponse(
        message=trans("Set feedentry as unread"),
        status_code=status.HTTP_200_OK,
    )


@feedentry_user_router.post("/feed_entry/set_favorite/{feed_entry_id}")
def set_entry_favorite(
    feed_entry_id: int,
    favorite_state: FavoriteStateValidator,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
) -> SuccessResponse:
    """
    Mark FeedEntry with the given feed_entry_id to favorite (for current user)
    """
    message = trans("Set feedentry state to favorite")
    if favorite_state.is_favorite:
        UserFeedEntryState.favorite(db, feed_entry_id, current_user.id)
    else:
        UserFeedEntryState.unfavorite(db, feed_entry_id, current_user.id)
        message = trans("Set feedentry state to unfavorite")
    return SuccessResponse(
        message=message,
        status_code=status.HTTP_200_OK,
    )


@feedentry_user_router.get("/feed_entry/list/{feed_id}")
def feed_entry_list(
    feed_id: int,
    index: int = 0,
    total: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
) -> SuccessResponse:
    """
    FeedEntry list for certain feed id
    """
    item_list = FeedEntryListResponse.list_for_user(
        db, feed_id, current_user.id, index, total
    )
    return SuccessResponse(
        index=index,
        total=len(item_list.__root__),
        data=item_list,
        status_code=status.HTTP_200_OK,
    )


@feedentry_user_router.get("/feed_entry/{id}")
def feed_entry_item(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
) -> SuccessResponse:
    """
    Detail of FeedEntry
    """
    feed_entry_item = db.get(FeedEntry, id)
    if not feed_entry_item:
        raise CustomException(detail=trans("FeedEntry does not exist"))
    data = FeedEntryValidator.for_user(
        db, feed_entry=feed_entry_item, user_id=current_user.id
    )
    UserFeedEntryState.mark_read(db, id, current_user.id)
    return SuccessResponse(
        data=data,
        status_code=status.HTTP_200_OK,
    )


@feedentry_user_router.post("/feed_entry/{feed_entry_id}/add_comment")
def add_comment_to_feed_entry(
    feed_entry_id: int,
    comment_validator: CommentValidator,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
) -> SuccessResponse:
    """
    Add Comment to FeedEntry
    """
    comment = comment_validator.create(db, feed_entry_id, current_user)
    return SuccessResponse(
        message=trans("Added new Comment"),
        data=CommentResponse.from_orm(comment),
        status_code=status.HTTP_200_OK,
    )


@feedentry_user_router.get("/feed_entry/{id}/my_comments")
def get_my_comment_on_feed_entries(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
) -> SuccessResponse:
    """
    My comments list
    """
    comments = db.query(Comment).filter(
        Comment.user_id == current_user.id, Comment.feed_entry_id == id).all()
    return SuccessResponse(
        data=CommentListResponse.from_orm(comments),
        status_code=status.HTTP_200_OK,
    )


@feedentry_user_router.get("/feed_entry/{id}/comments")
def get_feed_entry_comments(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
) -> SuccessResponse:
    """
    FeedEntry comments list
    """
    comments = db.query(Comment).filter(Comment.feed_entry_id == id).all()
    return SuccessResponse(
        data=CommentListResponse.from_orm(comments),
        status_code=status.HTTP_200_OK,
    )
