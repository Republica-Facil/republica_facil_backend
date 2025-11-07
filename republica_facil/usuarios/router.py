from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from republica_facil.database import get_session
from republica_facil.security import (
    get_current_user,
    get_password_hash,
    verify_password,
)

from .repository import (
    create_user_db,
    get_user_by_email,
    get_user_by_id,
    get_user_by_telephone,
    get_users,
)
from .schema import (
    Message,
    UserList,
    UserPublic,
    UserSchema,
    UserUpdate,
    UserUpdatePassword,
)
from .service import (
    verify_fullname,
    verify_length_telephone,
    verify_strong_password,
)

router = APIRouter(prefix='/users', tags=['users'])


@router.post(
    '/',
    status_code=HTTPStatus.CREATED,
    response_class=JSONResponse,
    response_model=UserPublic,
)
def create_user(user: UserSchema, session=Depends(get_session)):
    if not verify_strong_password(user.password):
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail='Weak password'
        )
    if not verify_length_telephone(user.telephone):
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail='Verifies if a phone number is valid, including its area '
            'code (DDD)',
        )
    if not verify_fullname(user.fullname):
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail='Enter your full name',
        )
    existing_email = get_user_by_email(session, user.email)
    if existing_email:
        raise HTTPException(
            detail='Email already exists',
            status_code=HTTPStatus.CONFLICT,
        )

    existing_telephone = get_user_by_telephone(session, user.telephone)
    if existing_telephone:
        raise HTTPException(
            detail='Telephone already exists',
            status_code=HTTPStatus.CONFLICT,
        )
    if not verify_strong_password(user.password):
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail='Weak password'
        )

    user_data = {
        'fullname': user.fullname,
        'email': user.email,
        'telephone': user.telephone,
        'password': get_password_hash(user.password),
    }

    db_user = create_user_db(session, user_data)

    return db_user


@router.get('/', status_code=HTTPStatus.OK, response_model=UserList)
def read_users(
    limit: int = 10, offset: int = 0, session: Session = Depends(get_session)
):
    users = get_users(session, limit, offset)
    return {'users': users}


@router.put(
    '/{user_id}',
    status_code=HTTPStatus.OK,
    response_class=JSONResponse,
    response_model=UserPublic,
)
def update_user(
    user_id: int,
    user: UserUpdate,
    session=Depends(get_session),
    current_user=Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Not enough permissions'
        )

    try:
        current_user.fullname = user.fullname
        current_user.email = user.email
        current_user.telephone = user.telephone

        session.commit()
        session.refresh(current_user)

        return current_user

    except IntegrityError:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Email already exists',
        )


@router.patch(
    '/change-password/{user_id}',
    status_code=HTTPStatus.OK,
    response_class=JSONResponse,
    response_model=Message,
)
def update_password(
    user_id: int,
    user: UserUpdatePassword,
    session=Depends(get_session),
    current_user=Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail='Not enough permissions'
        )

    if not verify_password(
        plain_password=user.old_password,
        hashed_password=current_user.password,
    ):
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_CONTENT,
            detail='Erro ao processar senha antiga',
        )
    if user.new_password != user.confirm_password:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_CONTENT,
            detail='As senhas devem ser iguais',
        )

    if not verify_strong_password(user.new_password):
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_CONTENT,
            detail='Senha fraca',
        )

    current_user.password = get_password_hash(user.new_password)
    session.commit()
    session.refresh(current_user)

    return {'message': 'Senha alterada com sucesso'}


@router.delete('/{user_id}', status_code=HTTPStatus.OK, response_model=Message)
def delete_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    # 2                # 124
    if current_user.id != user_id:
        raise HTTPException(
            detail='Not enough permissions', status_code=HTTPStatus.FORBIDDEN
        )

    session.delete(current_user)
    session.commit()

    return {'message': 'User deleted'}


@router.get('/{user_id}', response_model=UserPublic)
def read_user__exercicio(
    user_id: int, session: Session = Depends(get_session)
):
    db_user = get_user_by_id(session, user_id)

    if not db_user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='User not found'
        )

    return db_user
