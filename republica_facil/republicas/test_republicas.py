"""Testes para o módulo de repúblicas."""

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
    user = User(
        fullname='João Silva',
        email='joao@teste.com',
        password=get_password_hash('testpass123'),  # Senha hasheada
        telephone='11999999999',
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


# @pytest.fixture
# def client_with_auth(client, user):
#     """Cliente com autenticação."""

#     def get_current_user_override():
#         return user

#     app.dependency_overrides[get_current_user] = get_current_user_override
#     yield client
#     app.dependency_overrides.clear()


@pytest.fixture
def token(user, client):
    response = client.post(
        '/auth/login/',
        data={'username': user.email, 'password': 'testpass123'},
    )
    return response.json()['access_token']


def test_create_republica_success(client, token, user):
    republica_data = {
        'name': 'Casa dos Estudantes',
        'address': 'GAMA',
        'user_id': user.id,
    }

    response = client.post(
        '/republicas/',
        json=republica_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    # Debug temporário
    print(f'Status: {response.status_code}')
    print(f'Response: {response.json()}')

    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data['name'] == republica_data['name']
    assert data['address'] == republica_data['address']
    assert 'id' in data


# def test_create_republica_without_auth(client):
#     """Testa criação de república sem autenticação."""
#     republica_data = {
#         'name': 'Casa dos Estudantes',
#         'description': 'República estudantil no centro da cidade',
#     }

#     response = client.post('/republicas/', json=republica_data)

#     assert response.status_code == HTTPStatus.UNAUTHORIZED


# def test_create_republica_invalid_data(client_with_auth):
#     """Testa criação com dados inválidos."""
#     republica_data = {
#         'name': '',  # Nome vazio
#         'description': 'Descrição válida',
#     }

#     response = client_with_auth.post('/republicas/', json=republica_data)

#     assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


# def test_get_republica_success(client_with_auth):
#     """Testa busca de república por ID."""
#     # Criar uma república primeiro
#     republica_data = {
#         'name': 'Casa dos Estudantes',
#         'description': 'República estudantil no centro da cidade',
#     }

#     create_response = client_with_auth.post(
#         '/republicas/', json=republica_data
#     )
#     republica_id = create_response.json()['id']

#     # Buscar a república
#     response = client_with_auth.get(f'/republicas/{republica_id}')

#     assert response.status_code == HTTPStatus.OK
#     data = response.json()
#     assert data['id'] == republica_id
#     assert data['name'] == republica_data['name']


# def test_get_republica_not_found(client_with_auth):
#     """Testa busca de república inexistente."""
#     response = client_with_auth.get('/republicas/999')

#     assert response.status_code == HTTPStatus.NOT_FOUND
#     assert 'não encontrada' in response.json()['detail']


# def test_list_republicas(client_with_auth):
#     """Testa listagem de repúblicas."""
#     # Criar algumas repúblicas
#     republicas_data = [
#         {'name': 'Casa 1', 'description': 'Descrição 1'},
#         {'name': 'Casa 2', 'description': 'Descrição 2'},
#     ]

#     for data in republicas_data:
#         client_with_auth.post('/republicas/', json=data)

#     # Listar repúblicas
#     response = client_with_auth.get('/republicas/')

#     assert response.status_code == HTTPStatus.OK
#     data = response.json()
#     expected_count = 2
#     assert len(data) == expected_count
#     assert all('id' in republica for republica in data)
