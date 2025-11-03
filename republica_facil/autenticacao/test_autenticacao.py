"""Testes para o módulo de autenticação."""

from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from republica_facil.database import get_session
from republica_facil.main import app
from republica_facil.model.models import User, table_registry
from republica_facil.security import get_password_hash

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
