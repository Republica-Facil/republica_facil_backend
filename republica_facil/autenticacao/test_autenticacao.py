"""Testes para o módulo de autenticação."""

from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import republica_facil.autenticacao.router as router_module
import republica_facil.autenticacao.service as service_module
from republica_facil.database import get_session, redis_client
from republica_facil.main import app
from republica_facil.model.models import User, table_registry
from republica_facil.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)

JWT_TOKEN_PARTS_COUNT = 3  # Token JWT tem 3 partes: header.payload.signature


@pytest.fixture
def session():
    """Cria uma sessão de teste."""
    engine = create_engine(
        'sqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    table_registry.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


@pytest.fixture
def client(session):
    """Cria um cliente de teste."""

    def get_session_override():
        return session

    with TestClient(app) as client:
        app.dependency_overrides[get_session] = get_session_override
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def user(session):
    """Cria um usuário de teste."""
    user = User(
        fullname='Test User',
        email='testuser@example.com',
        password=get_password_hash('testpass123'),
        telephone='11999999999',
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def test_login_success(client, user):
    """Testa login com credenciais válidas."""
    response = client.post(
        '/auth/login/',
        data={
            'username': user.email,
            'password': 'testpass123',  # senha padrão do fixture
        },
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert 'access_token' in data
    assert data['token_type'] == 'Bearer'


def test_login_wrong_username(client):
    """Testa login com username inexistente."""
    response = client.post(
        '/auth/login/',
        data={
            'username': 'wrong_user@example.com',
            'password': 'testpass123',
        },
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert 'Incorrect email or password' in response.json()['detail']


def test_login_wrong_password(client, user):
    """Testa login com senha incorreta."""
    response = client.post(
        '/auth/login/',
        data={
            'username': user.email,
            'password': 'wrong_password',
        },
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert 'Incorrect password' in response.json()['detail']


def test_login_missing_credentials(client):
    """Testa login sem credenciais."""
    response = client.post('/auth/login/', data={})
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_login_missing_username(client):
    """Testa login sem username."""
    response = client.post(
        '/auth/login/',
        data={
            'password': 'testpass123',
        },
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_login_missing_password(client, user):
    """Testa login sem password."""
    response = client.post(
        '/auth/login/',
        data={
            'username': user.email,
        },
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_token_format(client, user):
    """Testa se o token retornado tem o formato correto."""
    response = client.post(
        '/auth/login/',
        data={
            'username': user.email,
            'password': 'testpass123',
        },
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()

    # Verificar estrutura da resposta
    assert 'access_token' in data
    assert 'token_type' in data
    assert data['token_type'] == 'Bearer'

    # Verificar que o token não está vazio
    assert len(data['access_token']) > 0

    # Token JWT tem 3 partes separadas por '.'
    token_parts = data['access_token'].split('.')
    assert len(token_parts) == JWT_TOKEN_PARTS_COUNT


def test_login_case_sensitive_username(client, user):
    """Testa se o username é case-sensitive."""
    response = client.post(
        '/auth/login/',
        data={
            'username': user.email.upper(),  # Maiúsculo
            'password': 'testpass123',
        },
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert 'Incorrect email or password' in response.json()['detail']


def test_forgot_password_success(client, user):
    """Testa solicitação de código de reset para email existente."""
    response = client.post(
        '/auth/forgot-password',
        json={'email': user.email},
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert 'message' in data
    assert 'reset code has been sent' in data['message'].lower()


def test_forgot_password_nonexistent_email(client):
    response = client.post(
        '/auth/forgot-password',
        json={'email': 'nonexistent@example.com'},
    )
    # Deve retornar sucesso mesmo que o email não exista (segurança)
    assert response.status_code == HTTPStatus.OK


def test_forgot_password_invalid_email_format(client):
    """Testa forgot-password com formato de email inválido."""
    response = client.post(
        '/auth/forgot-password',
        json={'email': 'invalid-email-format'},
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_forgot_password_redis_unavailable(client, user, monkeypatch):
    """Testa forgot-password quando Redis não está disponível."""

    monkeypatch.setattr(service_module, 'redis_client', None)

    response = client.post(
        '/auth/forgot-password',
        json={'email': user.email},
    )

    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    assert 'Service unavailable' in response.json()['detail']


def test_forgot_password_redis_error(client, user, monkeypatch):
    """Testa forgot-password quando Redis lança exceção."""

    class MockRedisError:
        @staticmethod
        def setr(key, value, ex):
            raise Exception('Redis connection error')

    monkeypatch.setattr(service_module, 'redis_client', MockRedisError())

    response = client.post(
        '/auth/forgot-password',
        json={'email': user.email},
    )

    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    assert 'Erro no serviço de cache' in response.json()['detail']


def test_verify_code_success(client, user):
    """Testa verificação de código válido."""

    if not redis_client:
        pytest.skip('Redis not available')

    # Simular código salvo no Redis
    redis_key = f'reset_code:{user.email}'
    redis_client.setex(redis_key, 300, '123456')

    response = client.post(
        '/auth/verify-code',
        json={'email': user.email, 'code': '123456'},
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert 'reset_token' in data
    assert data['token_type'] == 'Bearer'
    assert len(data['reset_token']) > 0

    # Verificar que o código foi removido do Redis
    assert redis_client.get(redis_key) is None


def test_verify_code_invalid_code(client, user):
    """Testa verificação com código inválido."""

    if not redis_client:
        pytest.skip('Redis not available')

    # Simular código diferente no Redis
    redis_key = f'reset_code:{user.email}'
    redis_client.setex(redis_key, 300, '123456')

    response = client.post(
        '/auth/verify-code',
        json={'email': user.email, 'code': '999999'},
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert 'Invalid or expired code' in response.json()['detail']


def test_verify_code_expired_code(client, user):
    """Testa verificação com código expirado/inexistente."""

    if not redis_client:
        pytest.skip('Redis not available')

    # Garantir que não existe código no Redis
    redis_key = f'reset_code:{user.email}'
    redis_client.delete(redis_key)

    response = client.post(
        '/auth/verify-code',
        json={'email': user.email, 'code': '123456'},
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert 'Invalid or expired code' in response.json()['detail']


def test_verify_code_redis_unavailable(client, user, monkeypatch):
    """Testa verificação quando o Redis não está disponível."""
    # Simular que redis_client é None

    monkeypatch.setattr(router_module, 'redis_client', None)

    response = client.post(
        '/auth/verify-code',
        json={'email': user.email, 'code': '123456'},
    )

    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    assert 'Service unavailable' in response.json()['detail']


def test_reset_password_success(client, user, session):
    """Testa reset de senha com token válido."""

    # Criar token de reset válido
    reset_token = create_access_token(
        data={'sub': user.email, 'scope': 'reset_password'},
        expires_delta_minutes=15,
    )

    new_password = 'NewSecurePass123!'

    response = client.patch(
        '/auth/reset-password',
        json={'new_password': new_password},
        headers={'Authorization': f'Bearer {reset_token}'},
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert 'password changed successfully' in data['message'].lower()

    # Verificar que a senha foi alterada no banco
    session.refresh(user)
    assert verify_password(new_password, user.password)


def test_reset_password_weak_password(client, user):
    """Testa reset de senha com senha fraca."""

    reset_token = create_access_token(
        data={'sub': user.email, 'scope': 'reset_password'},
        expires_delta_minutes=15,
    )

    response = client.patch(
        '/auth/reset-password',
        json={'new_password': '12345678'},  # 8 chars mas senha fraca
        headers={'Authorization': f'Bearer {reset_token}'},
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT
    assert 'Weak password' in response.json()['detail']


def test_reset_password_invalid_length(client, user):
    """Testa reset de senha com senha muito curta."""

    reset_token = create_access_token(
        data={'sub': user.email, 'scope': 'reset_password'},
        expires_delta_minutes=15,
    )

    response = client.patch(
        '/auth/reset-password',
        json={'new_password': '123'},  # Menos de 8 caracteres
        headers={'Authorization': f'Bearer {reset_token}'},
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_reset_password_invalid_token(client):
    """Testa reset de senha com token inválido."""
    response = client.patch(
        '/auth/reset-password',
        json={'new_password': 'NewSecurePass123!'},
        headers={'Authorization': 'Bearer invalid_token'},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_reset_password_without_token(client):
    """Testa reset de senha sem token."""
    response = client.patch(
        '/auth/reset-password',
        json={'new_password': 'NewSecurePass123!'},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_reset_password_regular_token(client, user):
    """Testa reset de senha com token regular (sem scope reset_password)."""

    # Token normal, sem scope de reset
    regular_token = create_access_token(
        data={'sub': user.email}, user_id=user.id
    )

    response = client.patch(
        '/auth/reset-password',
        json={'new_password': 'NewSecurePass123!'},
        headers={'Authorization': f'Bearer {regular_token}'},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert 'Could not validate credentials' in response.json()['detail']


def test_logout_success(client, user):
    """Testa logout com token válido."""
    # Fazer login primeiro
    login_response = client.post(
        '/auth/login/',
        data={'username': user.email, 'password': 'testpass123'},
    )
    token = login_response.json()['access_token']

    # Fazer logout
    response = client.post(
        '/auth/logout', headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert 'Logout successful' in data['message']


def test_logout_without_token(client):
    """Testa logout sem token."""
    response = client.post('/auth/logout')

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_logout_invalid_token(client):
    """Testa logout com token inválido."""
    response = client.post(
        '/auth/logout', headers={'Authorization': 'Bearer invalid_token'}
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
