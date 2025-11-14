from datetime import datetime, timedelta
from http import HTTPStatus
from typing import Annotated
from zoneinfo import ZoneInfo

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import DecodeError, decode, encode
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from republica_facil.database import get_session
from republica_facil.model.models import User
from republica_facil.settings import Settings

settings = Settings()
pwd_context = PasswordHash.recommended()

T_Session = Annotated[Session, Depends(get_session)]


def create_access_token(
    data: dict, user_id: int = None, expires_delta_minutes: int = None
):
    to_encode = data.copy()

    if user_id is not None:
        to_encode.update({'id': user_id})

    if expires_delta_minutes:
        expire = datetime.now(tz=ZoneInfo('UTC')) + timedelta(
            minutes=expires_delta_minutes
        )
    else:
        expire = datetime.now(tz=ZoneInfo('UTC')) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({'exp': expire})

    encoded_jwt = encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def get_password_hash(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/login')


def get_current_user(
    session: T_Session,
    token: str = Depends(oauth2_scheme),
):
    credentials_exception = HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    try:
        payload = decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id = payload.get('id')
        subject_email = payload.get('sub')

        if not subject_email or not user_id:
            raise credentials_exception

    except DecodeError:
        raise credentials_exception

    user = session.scalar(select(User).where(User.email == subject_email))

    if not user:
        raise credentials_exception

    return user


def get_current_user_for_reset(
    session: T_Session,
    token: str = Depends(oauth2_scheme),
):
    credentials_exception = HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    try:
        payload = decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        subject_email = payload.get('sub')
        scope: str = payload.get('scope')

        if not subject_email or scope != 'reset_password':
            raise credentials_exception

    except (jwt.DecodeError, jwt.ExpiredSignatureError):
        raise credentials_exception

    user = session.scalar(select(User).where(User.email == subject_email))

    if not user:
        raise credentials_exception

    return user
