"""Testes para o módulo de membros."""

from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from republica_facil.database import get_session
from republica_facil.main import app
from republica_facil.model.models import (
    Membro,
    Quarto,
    Republica,
    User,
    table_registry,
)
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
        fullname='Test User',
        email='testuser@example.com',
        password=get_password_hash('testpass123'),
        telephone='11999999999',
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def other_user(session):
    """Cria um outro usuário de teste."""
    user = User(
        fullname='Other User',
        email='otheruser@example.com',
        password=get_password_hash('testpass123'),
        telephone='11988888888',
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
def other_token(other_user):
    """Cria um token de autenticação para outro usuário."""
    return create_access_token(
        data={'sub': other_user.email}, user_id=other_user.id
    )


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


@pytest.fixture
def other_republica(session, other_user):
    """Cria uma república de outro usuário."""
    republica = Republica(
        nome='República Outro',
        cep='98765432',
        rua='Rua Outro',
        numero='456',
        bairro='Bairro',
        cidade='Rio de Janeiro',
        estado='RJ',
        user_id=other_user.id,
    )
    session.add(republica)
    session.commit()
    session.refresh(republica)
    return republica


@pytest.fixture
def quarto(session, republica):
    """Cria um quarto de teste."""
    quarto = Quarto(
        numero=101,
        republica_id=republica.id,
    )
    session.add(quarto)
    session.commit()
    session.refresh(quarto)
    return quarto


@pytest.fixture
def quarto2(session, republica):
    """Cria um segundo quarto de teste."""
    quarto = Quarto(
        numero=102,
        republica_id=republica.id,
    )
    session.add(quarto)
    session.commit()
    session.refresh(quarto)
    return quarto


@pytest.fixture
def membro(session, republica, quarto):
    """Cria um membro de teste."""
    membro = Membro(
        fullname='Membro Teste',
        email='membro@example.com',
        telephone='11977777777',
        republica_id=republica.id,
        quarto_id=quarto.id,
    )
    session.add(membro)
    session.commit()
    session.refresh(membro)
    return membro


# Testes do endpoint POST /membros/{republica_id}


def test_create_member_success(client, token, republica):
    """Testa criação de membro sem quarto com sucesso."""
    member_data = {
        'fullname': 'Novo Membro',
        'email': 'novo@example.com',
        'telephone': '11966666666',
    }

    response = client.post(
        f'/membros/{republica.id}',
        json=member_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data['fullname'] == member_data['fullname']
    assert data['email'] == member_data['email']
    assert data['telephone'] == member_data['telephone']
    assert data['quarto_id'] is None
    assert 'id' in data


def test_create_member_with_quarto_success(client, token, republica, quarto):
    """Testa criação de membro com quarto com sucesso."""
    member_data = {
        'fullname': 'Novo Membro',
        'email': 'novo@example.com',
        'telephone': '11966666666',
        'quarto_id': quarto.id,
    }

    response = client.post(
        f'/membros/{republica.id}',
        json=member_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data['quarto_id'] == quarto.id


def test_create_member_republica_not_found(client, token):
    """Testa criação de membro em república inexistente."""
    member_data = {
        'fullname': 'Novo Membro',
        'email': 'novo@example.com',
        'telephone': '11966666666',
    }

    response = client.post(
        '/membros/999',
        json=member_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert 'Republica nao encontrada' in response.json()['detail']


def test_create_member_unauthorized(client, other_token, republica):
    """Testa criação de membro por usuário não autorizado."""
    member_data = {
        'fullname': 'Novo Membro',
        'email': 'novo@example.com',
        'telephone': '11966666666',
    }

    response = client.post(
        f'/membros/{republica.id}',
        json=member_data,
        headers={'Authorization': f'Bearer {other_token}'},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert 'Permissões negadas' in response.json()['detail']


def test_create_member_quarto_not_found(client, token, republica):
    """Testa criação de membro com quarto inexistente."""
    member_data = {
        'fullname': 'Novo Membro',
        'email': 'novo@example.com',
        'telephone': '11966666666',
        'quarto_id': 999,
    }

    response = client.post(
        f'/membros/{republica.id}',
        json=member_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert 'Quarto não encontrado' in response.json()['detail']


def test_create_member_quarto_outra_republica(  # noqa: PLR0913, PLR0917
    client, token, republica, other_republica, session
):
    """Testa criação de membro com quarto de outra república."""
    # Criar quarto em outra república
    quarto_outro = Quarto(
        numero=201,
        republica_id=other_republica.id,
    )
    session.add(quarto_outro)
    session.commit()
    session.refresh(quarto_outro)

    member_data = {
        'fullname': 'Novo Membro',
        'email': 'novo@example.com',
        'telephone': '11966666666',
        'quarto_id': quarto_outro.id,
    }

    response = client.post(
        f'/membros/{republica.id}',
        json=member_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert 'Quarto não pertence a esta república' in response.json()['detail']


def test_create_member_quarto_ocupado(client, token, republica, membro):
    """Testa criação de membro em quarto já ocupado."""
    member_data = {
        'fullname': 'Novo Membro',
        'email': 'novo@example.com',
        'telephone': '11966666666',
        'quarto_id': membro.quarto_id,
    }

    response = client.post(
        f'/membros/{republica.id}',
        json=member_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert 'Este quarto já está ocupado' in response.json()['detail']


def test_create_member_duplicate_email(client, token, republica, membro):
    """Testa criação de membro com email duplicado."""
    member_data = {
        'fullname': 'Novo Membro',
        'email': membro.email,  # Email já existe
        'telephone': '11955555555',
    }

    response = client.post(
        f'/membros/{republica.id}',
        json=member_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert 'Membro ja existe' in response.json()['detail']


def test_create_member_duplicate_telephone(client, token, republica, membro):
    """Testa criação de membro com telefone duplicado."""
    member_data = {
        'fullname': 'Novo Membro',
        'email': 'novo@example.com',
        'telephone': membro.telephone,  # Telefone já existe
    }

    response = client.post(
        f'/membros/{republica.id}',
        json=member_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert 'Membro ja existe' in response.json()['detail']


def test_create_member_without_token(client, republica):
    """Testa criação de membro sem token de autenticação."""
    member_data = {
        'fullname': 'Novo Membro',
        'email': 'novo@example.com',
        'telephone': '11966666666',
    }

    response = client.post(
        f'/membros/{republica.id}',
        json=member_data,
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED


# Testes do endpoint GET /membros/{republica_id}


def test_read_members_success(client, token, republica, membro):
    """Testa listagem de membros com sucesso."""
    response = client.get(
        f'/membros/{republica.id}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert 'members' in data
    assert len(data['members']) == 1
    assert data['members'][0]['id'] == membro.id


def test_read_members_empty_list(client, token, republica):
    """Testa listagem de membros vazia."""
    response = client.get(
        f'/membros/{republica.id}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert 'members' in data
    assert len(data['members']) == 0


def test_read_members_with_pagination(client, token, republica, session):
    """Testa listagem de membros com paginação."""
    # Criar vários membros
    total_membros = 15
    page_size = 5

    for i in range(total_membros):
        membro = Membro(
            fullname=f'Membro {i}',
            email=f'membro{i}@example.com',
            telephone=f'1196666666{i}',
            republica_id=republica.id,
        )
        session.add(membro)
    session.commit()

    # Testar com limit
    response = client.get(
        f'/membros/{republica.id}?limit={page_size}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert len(data['members']) == page_size

    # Testar com offset
    response = client.get(
        f'/membros/{republica.id}?limit={page_size}&offset={page_size}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert len(data['members']) == page_size


def test_read_members_republica_not_found(client, token):
    """Testa listagem de membros em república inexistente."""
    response = client.get(
        '/membros/999',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert 'Republica nao encontrada' in response.json()['detail']


def test_read_members_unauthorized(client, other_token, republica):
    """Testa listagem de membros por usuário não autorizado."""
    response = client.get(
        f'/membros/{republica.id}',
        headers={'Authorization': f'Bearer {other_token}'},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert 'Permissões negadas' in response.json()['detail']


# Testes do endpoint GET /membros/{republica_id}/{member_id}


def test_read_member_success(client, token, republica, membro):
    """Testa leitura de membro específico com sucesso."""
    response = client.get(
        f'/membros/{republica.id}/{membro.id}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['id'] == membro.id
    assert data['fullname'] == membro.fullname
    assert data['email'] == membro.email


def test_read_member_republica_not_found(client, token, membro):
    """Testa leitura de membro em república inexistente."""
    response = client.get(
        f'/membros/999/{membro.id}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert 'Republica nao encontrada' in response.json()['detail']


def test_read_member_unauthorized(client, other_token, republica, membro):
    """Testa leitura de membro por usuário não autorizado."""
    response = client.get(
        f'/membros/{republica.id}/{membro.id}',
        headers={'Authorization': f'Bearer {other_token}'},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert 'Permissões negadas' in response.json()['detail']


def test_read_member_not_found(client, token, republica):
    """Testa leitura de membro inexistente."""
    response = client.get(
        f'/membros/{republica.id}/999',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert 'Membro nao encontrado' in response.json()['detail']


# Testes do endpoint PUT /membros/{republica_id}/{member_id}


def test_update_member_success(client, token, republica, membro):
    """Testa atualização de membro com sucesso."""
    update_data = {
        'fullname': 'Membro Atualizado',
        'email': 'atualizado@example.com',
        'telephone': '11955555555',
        'quarto_id': membro.quarto_id,  # Manter o quarto atual
    }

    response = client.put(
        f'/membros/{republica.id}/{membro.id}',
        json=update_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['fullname'] == update_data['fullname']
    assert data['email'] == update_data['email']
    assert data['telephone'] == update_data['telephone']


def test_update_member_change_quarto_success(  # noqa: PLR0913, PLR0917
    client, token, republica, membro, quarto2
):
    """Testa mudança de quarto do membro com sucesso."""
    update_data = {
        'fullname': membro.fullname,
        'email': membro.email,
        'telephone': membro.telephone,
        'quarto_id': quarto2.id,
    }

    response = client.put(
        f'/membros/{republica.id}/{membro.id}',
        json=update_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['quarto_id'] == quarto2.id


def test_update_member_remove_quarto_success(client, token, republica, membro):
    """Testa remoção de quarto do membro com sucesso."""
    update_data = {
        'fullname': membro.fullname,
        'email': membro.email,
        'telephone': membro.telephone,
        'quarto_id': None,
    }

    response = client.put(
        f'/membros/{republica.id}/{membro.id}',
        json=update_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['quarto_id'] is None


def test_update_member_quarto_not_found(client, token, republica, membro):
    """Testa atualização de membro com quarto inexistente."""
    update_data = {
        'fullname': membro.fullname,
        'email': membro.email,
        'telephone': membro.telephone,
        'quarto_id': 999,
    }

    response = client.put(
        f'/membros/{republica.id}/{membro.id}',
        json=update_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert 'Quarto não encontrado' in response.json()['detail']


def test_update_member_quarto_outra_republica(  # noqa: PLR0913, PLR0917
    client, token, republica, other_republica, membro, session
):
    """Testa atualização com quarto de outra república."""
    # Criar quarto em outra república
    quarto_outro = Quarto(
        numero=201,
        republica_id=other_republica.id,
    )
    session.add(quarto_outro)
    session.commit()
    session.refresh(quarto_outro)

    update_data = {
        'fullname': membro.fullname,
        'email': membro.email,
        'telephone': membro.telephone,
        'quarto_id': quarto_outro.id,
    }

    response = client.put(
        f'/membros/{republica.id}/{membro.id}',
        json=update_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert 'Quarto não pertence a esta república' in response.json()['detail']


def test_update_member_quarto_ocupado(  # noqa: PLR0913, PLR0917
    client, token, republica, membro, quarto2, session
):
    """Testa atualização para quarto já ocupado."""
    # Criar outro membro no quarto2
    membro2 = Membro(
        fullname='Outro Membro',
        email='outro@example.com',
        telephone='11944444444',
        republica_id=republica.id,
        quarto_id=quarto2.id,
    )
    session.add(membro2)
    session.commit()

    update_data = {
        'fullname': membro.fullname,
        'email': membro.email,
        'telephone': membro.telephone,
        'quarto_id': quarto2.id,
    }

    response = client.put(
        f'/membros/{republica.id}/{membro.id}',
        json=update_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert 'Este quarto já está ocupado' in response.json()['detail']


def test_update_member_duplicate_email(  # noqa: PLR0913, PLR0917
    client, token, republica, membro, session
):
    """Testa atualização com email duplicado."""
    # Criar outro membro
    membro2 = Membro(
        fullname='Outro Membro',
        email='outro@example.com',
        telephone='11944444444',
        republica_id=republica.id,
    )
    session.add(membro2)
    session.commit()

    update_data = {
        'fullname': membro.fullname,
        'email': membro2.email,  # Email já existe
        'telephone': membro.telephone,
    }

    response = client.put(
        f'/membros/{republica.id}/{membro.id}',
        json=update_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert 'Membro ja existe' in response.json()['detail']


def test_update_member_republica_not_found(client, token, membro):
    """Testa atualização de membro em república inexistente."""
    update_data = {
        'fullname': 'Membro Atualizado',
        'email': 'atualizado@example.com',
        'telephone': '11955555555',
    }

    response = client.put(
        f'/membros/999/{membro.id}',
        json=update_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert 'Republica nao encontrada' in response.json()['detail']


def test_update_member_unauthorized(client, other_token, republica, membro):
    """Testa atualização de membro por usuário não autorizado."""
    update_data = {
        'fullname': 'Membro Atualizado',
        'email': 'atualizado@example.com',
        'telephone': '11955555555',
    }

    response = client.put(
        f'/membros/{republica.id}/{membro.id}',
        json=update_data,
        headers={'Authorization': f'Bearer {other_token}'},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert 'Permissões negadas' in response.json()['detail']


# Testes do endpoint DELETE /membros/{republica_id}/{member_id}


def test_delete_member_success(client, token, republica, membro):
    """Testa exclusão de membro com sucesso."""
    response = client.delete(
        f'/membros/{republica.id}/{membro.id}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert 'Membro excluido' in data['message']


def test_delete_member_republica_not_found(client, token, membro):
    """Testa exclusão de membro em república inexistente."""
    response = client.delete(
        f'/membros/999/{membro.id}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert 'Republica nao encontrada' in response.json()['detail']


def test_delete_member_unauthorized(client, other_token, republica, membro):
    """Testa exclusão de membro por usuário não autorizado."""
    response = client.delete(
        f'/membros/{republica.id}/{membro.id}',
        headers={'Authorization': f'Bearer {other_token}'},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert 'Permissões negadas' in response.json()['detail']


def test_delete_member_not_found(client, token, republica):
    """Testa exclusão de membro inexistente."""
    response = client.delete(
        f'/membros/{republica.id}/999',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert 'Republica nao encontrada' in response.json()['detail']
