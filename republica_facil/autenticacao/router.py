from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

from republica_facil.autenticacao import schema, service
from republica_facil.database import redis_client
from republica_facil.model.models import User
from republica_facil.security import (
    T_Session,
    create_access_token,
    get_current_user,
    get_current_user_for_reset,
    get_password_hash,
    verify_password,
)
from republica_facil.usuarios.service import verify_strong_password

from .repository import get_user
from .schema import TokenJWT

router = APIRouter(prefix='/auth', tags=['auth'])

OAuth2Form = Annotated[OAuth2PasswordRequestForm, Depends()]


@router.post(
    '/login/',
    status_code=HTTPStatus.OK,
    response_class=JSONResponse,
    response_model=TokenJWT,
)
def login_for_access_token(session: T_Session, form_data: OAuth2Form):
    db_user = get_user(form_data.username, session)
    # nao existe esse email no db
    if not db_user:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Incorrect email or password',
        )
    # verify_passowrd -> True se as senhas batem
    if not verify_password(form_data.password, db_user.password):
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Incorrect password',
        )

    token = create_access_token(
        data={'sub': db_user.email}, user_id=db_user.id
    )

    return {'access_token': token, 'token_type': 'Bearer'}


@router.post('/forgot-password', status_code=HTTPStatus.OK)
def forgot_password(
    request: schema.ForgotPasswordSchema,  # Valida o JSON de entrada
    db: T_Session,
):
    """
    Endpoint para solicitar um código de redefinição de senha.
    """
    # Chama o serviço para fazer todo o trabalho
    service.request_password_reset_code(db, email=request.email)

    return {'message': 'if the email exists, a reset code has been sent'}


@router.post('/verify-code', response_model=schema.ResetTokenSchema)
def verify_code(request: schema.VerifyCodeSchema):
    """
    ROTA 2: Verifica o código de reset e retorna um JWT especial.
    """
    if not redis_client:
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail='Service unavailable',
        )

    redis_key = f'reset_code:{request.email}'
    saved_code = redis_client.get(redis_key)

    if not saved_code or saved_code != request.code:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Invalid or expired code.',
        )

    redis_client.delete(redis_key)

    # 3. Crie o Token JWT especial (com "scope")
    reset_jwt = create_access_token(
        data={'sub': request.email, 'scope': 'reset_password'},
        expires_delta_minutes=15,  # 15 min para definir a nova senha
    )

    return {'reset_token': reset_jwt, 'token_type': 'Bearer'}


@router.patch('/reset-password', status_code=HTTPStatus.OK)
def reset_password(
    request: schema.ResetPasswordSchema,
    session: T_Session,
    # Valida o token da Rota 2 e retorna o objeto User
    current_user: User = Depends(get_current_user_for_reset),
):
    """
    ROTA 3: Define a nova senha usando o token de reset.
    """

    # 1. A dependência já nos deu o 'current_user'

    # 2. Atualiza a senha no objeto
    if not verify_strong_password(request.new_password):
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_CONTENT,
            detail='Weak password',
        )
    current_user.password = get_password_hash(request.new_password)

    session.add(current_user)
    session.commit()

    return {'message': 'password changed successfully.'}


@router.post('/logout', status_code=HTTPStatus.OK)
def logout(current_user: User = Depends(get_current_user)):
    return {'message': 'Logout successful'}
