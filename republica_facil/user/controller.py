from http import HTTPStatus

from fastapi import APIRouter, HTTPException

from republica_facil.user.repository import database
from republica_facil.user.schema import (
    Message,
    UserDB,
    UserList,
    UserPublic,
    UserSchema,
)
from republica_facil.user.service import create_user_service

router = APIRouter()


@router.get('/', status_code=HTTPStatus.OK, response_model=Message)
def read_root():
    return {'message': 'Olá Mundo!'}


@router.post(
    '/users/', status_code=HTTPStatus.CREATED, response_model=UserPublic
)
def create_user(user: UserSchema):
    return create_user_service(user)


@router.get('/users/', status_code=HTTPStatus.OK, response_model=UserList)
def read_users():
    return {'users': database}


@router.get(
    '/users/{user_id}', status_code=HTTPStatus.OK, response_model=UserPublic
)
def read_user(user_id: int):
    if user_id < 1 or user_id > len(database):
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='User NOT FOUND!!!'
        )
    return database[user_id - 1]


@router.put(
    '/users/{user_id}', status_code=HTTPStatus.OK, response_model=UserPublic
)
def update_user(user_id: int, user: UserSchema):
    user_with_id = UserDB(**user.model_dump(), id=user_id)

    if user_id < 1 or user_id > len(database):
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='User NOT FOUND!!!'
        )

    database[user_id - 1] = user_with_id
    return user_with_id


@router.delete(
    '/users/{user_id}', status_code=HTTPStatus.OK, response_model=UserPublic
)
def delete_user(user_id: int):
    if user_id < 1 or user_id > len(database):
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='User NOT FOUND!!!'
        )
    return database.pop(user_id - 1)
