from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from republica_facil.database import get_session
from republica_facil.model.models import User
from republica_facil.security import create_access_token, verify_password

from .schema import TokenJWT

router = APIRouter(prefix='/auth', tags=['auth'])

OAuth2Form = Annotated[OAuth2PasswordRequestForm, Depends()]
T_Session = Annotated[Session, Depends(get_session)]


# T_Session


@router.post(
    '/login/',
    status_code=HTTPStatus.OK,
    response_class=JSONResponse,
    response_model=TokenJWT,
)
def login_for_access_token(session: T_Session, form_data: OAuth2Form):
    db_user = session.scalar(
        select(User).where(User.username == form_data.username)
    )

    if not db_user:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Incorrect username or password',
        )

    if not verify_password(form_data.password, db_user.password):
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Incorrect username or password',
        )

    token = create_access_token({'sub': form_data.username})

    return {'access_token': token, 'token_type': 'Bearer'}
