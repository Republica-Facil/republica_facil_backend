"""Testes para o módulo de repúblicas."""

from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import republica_facil.republicas.repository as repo_module
from republica_facil.database import get_session
from republica_facil.main import app
from republica_facil.model.models import Republica, User, table_registry
from republica_facil.republicas import repository
from republica_facil.republicas.schema import RepublicaCreate
from republica_facil.security import create_access_token, get_password_hash


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
        fullname='João Silva',
        email='joao@teste.com',
        password=get_password_hash('testpass123'),
        telephone='11999999999',
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def token(user):
    """Cria um token de autenticação."""
    return create_access_token(data={'sub': user.email}, user_id=user.id)


@pytest.fixture
def republica(session, user):
    """Cria uma república de teste."""
    republica = Republica(
        nome='República Teste',
        cep='12345678',
        rua='Rua Teste',
        numero='123',
        bairro='Centro',
        cidade='São Paulo',
        estado='SP',
        user_id=user.id,
    )
    session.add(republica)
    session.commit()
    session.refresh(republica)
    return republica


# Testes do endpoint POST /republicas/


def test_create_republica_success(client, token):
    """Testa criação de república com sucesso."""
    republica_data = {
        'nome': 'Casa dos Estudantes',
        'cep': '72000000',
        'rua': 'Rua Principal',
        'numero': '123',
        'complemento': 'Apto 10',
        'bairro': 'Centro',
        'cidade': 'Brasília',
        'estado': 'DF',
    }

    response = client.post(
        '/republicas/',
        json=republica_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data['nome'] == republica_data['nome']
    assert data['cep'] == republica_data['cep']
    assert data['rua'] == republica_data['rua']
    assert data['cidade'] == republica_data['cidade']
    assert 'id' in data


def test_create_republica_without_complemento(client, token):
    """Testa criação de república sem complemento."""
    republica_data = {
        'nome': 'Casa Simples',
        'cep': '12345678',
        'rua': 'Rua Teste',
        'numero': '456',
        'bairro': 'Bairro Teste',
        'cidade': 'São Paulo',
        'estado': 'SP',
    }

    response = client.post(
        '/republicas/',
        json=republica_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data['nome'] == republica_data['nome']
    assert data['complemento'] is None


def test_create_republica_without_token(client):
    """Testa criação de república sem autenticação."""
    republica_data = {
        'nome': 'Casa dos Estudantes',
        'cep': '72000000',
        'rua': 'Rua Principal',
        'numero': '123',
        'bairro': 'Centro',
        'cidade': 'Brasília',
        'estado': 'DF',
    }

    response = client.post('/republicas/', json=republica_data)

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_create_republica_invalid_data(client, token):
    """Testa criação com dados inválidos (campos faltando)."""
    republica_data = {
        'nome': 'Casa Incompleta',
        # Faltando campos obrigatórios
    }

    response = client.post(
        '/republicas/',
        json=republica_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_create_republica_user_not_found(client, token, session, user):
    """Testa criação quando usuário não existe mais no banco."""
    # Deletar o usuário para simular usuário não encontrado
    session.delete(user)
    session.commit()

    republica_data = {
        'nome': 'Casa Teste',
        'cep': '12345678',
        'rua': 'Rua Teste',
        'numero': '123',
        'bairro': 'Centro',
        'cidade': 'São Paulo',
        'estado': 'SP',
    }

    response = client.post(
        '/republicas/',
        json=republica_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    # Quando o usuário não existe, get_current_user retorna 401
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_create_republica_database_error(client, token, monkeypatch):
    """Testa tratamento de erro genérico do banco."""
    original_create = repo_module.create_republica

    def mock_create_error(*args, **kwargs):
        # Simular erro diferente de ValueError
        raise RuntimeError('Database error')

    monkeypatch.setattr(repo_module, 'create_republica', mock_create_error)

    republica_data = {
        'nome': 'Casa Erro',
        'cep': '12345678',
        'rua': 'Rua Erro',
        'numero': '999',
        'bairro': 'Centro',
        'cidade': 'São Paulo',
        'estado': 'SP',
    }

    response = client.post(
        '/republicas/',
        json=republica_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert 'Erro interno do servidor' in response.json()['detail']

    # Restaurar função original
    monkeypatch.setattr(repo_module, 'create_republica', original_create)


# Testes do endpoint GET /republicas/{republica_id}


def test_get_republica_success(client, republica):
    """Testa busca de república por ID."""
    response = client.get(f'/republicas/{republica.id}')

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['id'] == republica.id
    assert data['nome'] == republica.nome
    assert data['cep'] == republica.cep


def test_get_republica_not_found(client):
    """Testa busca de república inexistente."""
    response = client.get('/republicas/999')

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert 'República não encontrada' in response.json()['detail']


# Testes do endpoint GET /republicas/


def test_list_republicas_empty(client):
    """Testa listagem de repúblicas vazia."""
    response = client.get('/republicas/')

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_list_republicas_success(client, session, user):
    """Testa listagem de repúblicas."""
    # Criar algumas repúblicas
    expected_count = 2
    republicas_data = [
        {
            'nome': 'Casa 1',
            'cep': '11111111',
            'rua': 'Rua 1',
            'numero': '1',
            'bairro': 'Bairro 1',
            'cidade': 'Cidade 1',
            'estado': 'SP',
        },
        {
            'nome': 'Casa 2',
            'cep': '22222222',
            'rua': 'Rua 2',
            'numero': '2',
            'bairro': 'Bairro 2',
            'cidade': 'Cidade 2',
            'estado': 'RJ',
        },
    ]

    for data in republicas_data:
        republica = Republica(**data, user_id=user.id)
        session.add(republica)
    session.commit()

    # Listar repúblicas
    response = client.get('/republicas/')

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert len(data) == expected_count
    assert all('id' in republica for republica in data)
    assert data[0]['nome'] == 'Casa 1'
    assert data[1]['nome'] == 'Casa 2'


def test_list_republicas_with_pagination(client, session, user):
    """Testa listagem com paginação."""
    # Criar várias repúblicas
    for i in range(15):
        republica = Republica(
            nome=f'Casa {i}',
            cep=f'{i:08d}',
            rua=f'Rua {i}',
            numero=str(i),
            bairro='Bairro',
            cidade='Cidade',
            estado='SP',
            user_id=user.id,
        )
        session.add(republica)
    session.commit()

    # Testar com limit
    page_size = 5
    response = client.get(f'/republicas/?limit={page_size}')

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert len(data) == page_size

    # Testar com skip
    response = client.get(f'/republicas/?skip={page_size}&limit={page_size}')

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert len(data) == page_size
    assert data[0]['nome'] == 'Casa 5'


def test_list_republicas_default_pagination(client, session, user):
    """Testa listagem com valores padrão de paginação."""
    # Criar mais de 100 repúblicas para testar o limit padrão
    for i in range(105):
        republica = Republica(
            nome=f'Casa {i}',
            cep=f'{i:08d}',
            rua=f'Rua {i}',
            numero=str(i),
            bairro='Bairro',
            cidade='Cidade',
            estado='SP',
            user_id=user.id,
        )
        session.add(republica)
    session.commit()

    # Listar sem parâmetros (deve retornar no máximo 100)
    response = client.get('/republicas/')

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    default_limit = 100
    assert len(data) == default_limit


# Testes diretos do repository para cobertura completa


def test_repository_create_republica_rollback_on_error(
    session, user, monkeypatch
):
    """Testa rollback no repository quando ocorre erro no commit."""
    republica_data = RepublicaCreate(
        nome='Casa Erro',
        cep='12345678',
        rua='Rua Erro',
        numero='999',
        bairro='Centro',
        cidade='São Paulo',
        estado='SP',
    )

    # Mock do commit para lançar uma exceção genérica
    original_commit = session.commit

    def mock_commit_error():
        raise RuntimeError('Database commit error')

    monkeypatch.setattr(session, 'commit', mock_commit_error)

    # Testar que a exceção é propagada e rollback é chamado
    with pytest.raises(RuntimeError):
        repository.create_republica(session, user.id, republica_data)

    # Restaurar
    monkeypatch.setattr(session, 'commit', original_commit)
