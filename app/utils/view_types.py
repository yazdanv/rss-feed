from typing import List

from app.utils.schema import BaseOrmModel, SuccessResponse
from fastapi import Depends, status
from sqlalchemy.orm import session

from app.authnz.utils import get_admin_user
from app.core.database import get_db
from app.authnz.models import User


class AdminView:
    db: session = Depends(get_db)
    current_user: User = Depends(get_admin_user)

    def __init__(self):
        if not self.serializer:
            raise Exception("AdminView needs a serializer type defined")
        if not self.model:
            raise Exception("AdminView needs a model type defined")

    def create_view(self, input_payload):
        return SuccessResponse(
            data=self.serializer.from_orm(
                self.model.create(self.db, input_payload)),
            status_code=status.HTTP_201_CREATED,
        )

    def edit_view(self, id, input_payload):
        db_item = self.db.query(self.model).get(
            id).update(self.db, input_payload)
        print(db_item)
        return SuccessResponse(data=self.serializer.from_orm(db_item))

    def retrieve_view(self, id):
        db_item = self.db.query(self.model).get(id)
        return SuccessResponse(data=self.serializer.from_orm(db_item))

    def delete_view(self, id):
        db_item = self.db.query(self.model).get(id)
        db_item.delete(self.db)
        return SuccessResponse(data={})

    def list_view(self):
        if self.list_serializer:
            return SuccessResponse(
                data=self.list_serializer.from_orm(self.model.list(self.db)),
            )

        class ListResponse(BaseOrmModel):
            __root__: List[self.serializer]

        return SuccessResponse(
            data=ListResponse.from_orm(self.model.list(self.db)),
        )
