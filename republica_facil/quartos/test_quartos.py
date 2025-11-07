"""Tests for quartos endpoints."""

from http import HTTPStatus

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import object_session

from republica_facil.model.models import Membro, Quarto, Republica, User
from republica_facil.security import get_password_hash


@pytest.fixture
def user(session):
    """Create a test user."""
    user = User(
        fullname='Test User',
        email='testuser@test.com',
        password=get_password_hash('secret123'),
        telephone='61999999999',
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def republica(session, user):
    """Create a test republica."""
    rep = Republica(
        nome='Casa Teste',
        cep='72000-000',
        rua='Rua Teste',
        numero='100',
        bairro='Centro',
        cidade='Brasília',
        estado='DF',
        user_id=user.id,
    )
    session.add(rep)
    session.commit()
    session.refresh(rep)
    return rep


@pytest.fixture
def quarto(session, republica):
    """Create a test quarto."""
    q = Quarto(numero=1, republica_id=republica.id)
    session.add(q)
    session.commit()
    session.refresh(q)
    return q


@pytest.fixture
def membro(session, republica, quarto):
    """Create a test membro assigned to a quarto."""
    m = Membro(
        fullname='Test Membro',
        email='membro@test.com',
        telephone='61988888888',
        republica_id=republica.id,
        quarto_id=quarto.id,
    )
    session.add(m)
    session.commit()
    session.refresh(m)
    return m


@pytest.fixture
def token(client, user):
    """Get authentication token for test user."""
    response = client.post(
        '/auth/login/',
        data={'username': user.email, 'password': 'secret123'},
    )
    return response.json()['access_token']


def test_create_quarto_success(client, token, republica):
    response = client.post(
        '/quartos/',
        params={'republica_id': republica.id},
        json={'numero': 101},
        headers={'Authorization': f'Bearer {token}'},
    )
    NUM = 101
    assert response.status_code == HTTPStatus.CREATED
    assert response.json()['numero'] == NUM
    assert 'id' in response.json()


def test_create_quarto_republica_not_found(client, token):
    max_id = 999999
    response = client.post(
        '/quartos/',
        params={'republica_id': max_id},
        json={'numero': 101},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()['detail'] == 'Republica nao encontrada'


def test_create_quarto_unauthorized(client, token, republica, other_user):
    # Create token for other user who doesn't own the república
    response_other = client.post(
        '/auth/login/',
        data={'username': 'otheruser@test.com', 'password': 'OtherPass123!'},
    )
    other_token = response_other.json()['access_token']

    response = client.post(
        '/quartos/',
        params={'republica_id': republica.id},
        json={'numero': 101},
        headers={'Authorization': f'Bearer {other_token}'},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json()['detail'] == 'Permissões negadas'


def test_list_quartos_success(client, token, republica, quarto):
    response = client.get(
        '/quartos/',
        params={'republica_id': republica.id},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert 'quartos' in data
    assert len(data['quartos']) == 1
    assert data['quartos'][0]['numero'] == quarto.numero


def test_list_quartos_empty(client, token, republica):
    response = client.get(
        '/quartos/',
        params={'republica_id': republica.id},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert 'quartos' in data
    assert len(data['quartos']) == 0


def test_list_quartos_republica_not_found(client, token):
    max_id = 999999
    response = client.get(
        '/quartos/',
        params={'republica_id': max_id},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()['detail'] == 'Republica nao encontrada'


def test_list_quartos_unauthorized(client, token, republica, other_user):
    response_other = client.post(
        '/auth/login/',
        data={'username': 'otheruser@test.com', 'password': 'OtherPass123!'},
    )
    other_token = response_other.json()['access_token']

    response = client.get(
        '/quartos/',
        params={'republica_id': republica.id},
        headers={'Authorization': f'Bearer {other_token}'},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json()['detail'] == 'Permissões negadas'


def test_get_quarto_success(client, token, republica, quarto):
    response = client.get(
        f'/quartos/{quarto.id}',
        params={'republica_id': republica.id},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()['numero'] == quarto.numero
    assert response.json()['id'] == quarto.id


def test_get_quarto_not_found(client, token, republica):
    max_id = 999999
    response = client.get(
        f'/quartos/{max_id}',
        params={'republica_id': republica.id},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()['detail'] == 'Quartos nao encontrados'


def test_get_quarto_republica_not_found(client, token, quarto):
    max_id = 999999
    response = client.get(
        f'/quartos/{quarto.id}',
        params={'republica_id': max_id},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()['detail'] == 'Republica nao encontrada'


def test_get_quarto_unauthorized(client, token, republica, quarto, other_user):
    response_other = client.post(
        '/auth/login/',
        data={'username': 'otheruser@test.com', 'password': 'OtherPass123!'},
    )
    other_token = response_other.json()['access_token']

    response = client.get(
        f'/quartos/{quarto.id}',
        params={'republica_id': republica.id},
        headers={'Authorization': f'Bearer {other_token}'},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json()['detail'] == 'Permissões negadas'


def test_update_quarto_success(client, token, republica, quarto):
    response = client.patch(
        f'/quartos/{quarto.id}',
        params={'republica_id': republica.id},
        json={'numero': 202},
        headers={'Authorization': f'Bearer {token}'},
    )
    NUM = 202
    assert response.status_code == HTTPStatus.OK
    assert response.json()['numero'] == NUM


def test_update_quarto_not_found(client, token, republica):
    max_id = 999999
    response = client.patch(
        f'/quartos/{max_id}',
        params={'republica_id': republica.id},
        json={'numero': 202},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()['detail'] == 'Quartos nao encontrados'


def test_update_quarto_republica_not_found(client, token, quarto):
    max_id = 999999
    response = client.patch(
        f'/quartos/{quarto.id}',
        params={'republica_id': max_id},
        json={'numero': 202},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()['detail'] == 'Republica nao encontrada'


def test_update_quarto_unauthorized(
    client, token, republica, quarto, other_user
):
    response_other = client.post(
        '/auth/login/',
        data={'username': 'otheruser@test.com', 'password': 'OtherPass123!'},
    )
    other_token = response_other.json()['access_token']

    response = client.patch(
        f'/quartos/{quarto.id}',
        params={'republica_id': republica.id},
        json={'numero': 202},
        headers={'Authorization': f'Bearer {other_token}'},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json()['detail'] == 'Permissões negadas'


def test_delete_quarto_success(client, token, republica, quarto):
    # First, ensure quarto is empty (desocupar if needed)
    response = client.delete(
        f'/quartos/{quarto.id}',
        params={'republica_id': republica.id},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()['message'] == 'Quarto excluido'


def test_deletar_quarto_que_esta_sendo_ocupado(
    client, token, republica, quarto, membro
):
    quarto_id = quarto.id
    republica_id = republica.id
    response = client.delete(
        f'/quartos/{quarto_id}',
        params={'republica_id': republica_id},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.CONFLICT


def test_delete_quarto_not_found(client, token, republica):
    max_id = 999999
    response = client.delete(
        f'/quartos/{max_id}',
        params={'republica_id': republica.id},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()['detail'] == 'Quartos nao encontrados'


def test_delete_quarto_republica_not_found(client, token, quarto):
    max_id = 999999
    response = client.delete(
        f'/quartos/{quarto.id}',
        params={'republica_id': max_id},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()['detail'] == 'Republica nao encontrada'


def test_delete_quarto_unauthorized(
    client, token, republica, quarto, other_user
):
    response_other = client.post(
        '/auth/login/',
        data={'username': 'otheruser@test.com', 'password': 'OtherPass123!'},
    )
    other_token = response_other.json()['access_token']

    response = client.delete(
        f'/quartos/{quarto.id}',
        params={'republica_id': republica.id},
        headers={'Authorization': f'Bearer {other_token}'},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json()['detail'] == 'Permissões negadas'


def test_adicionar_membro_ao_quarto_success(
    client, token, republica, quarto, session
):
    # Create a member without a room
    data = {
        'fullname': 'Novo membro',
        'email': 'novo@membro.com',
        'telephone': '999999999',
    }
    response_create = client.post(
        f'/membros/{republica.id}',
        json=data,
        headers={'Authorization': f'Bearer {token}'},
    )
    membro = response_create.json()

    response = client.patch(
        f'/quartos/{quarto.id}/membros',
        json={'membro_id': membro['id']},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['message'] == 'Membro adicionado ao quarto'


def test_create_membro_sem_quarto(client, token, republica, quarto, session):
    data = {
        'fullname': 'Novo membro',
        'email': 'novo@membro.com',
        'telephone': '999999999',
    }
    response = client.post(
        f'/membros/{republica.id}',
        json=data,
        headers={'Authorization': f'Bearer {token}'},
    )

    membro = response.json()

    response_membro_no_quarto = client.patch(
        f'/quartos/{quarto.id}/membros',
        json={'membro_id': membro['id']},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response_membro_no_quarto.status_code == status.HTTP_200_OK


def test_adicionar_membro_quarto_not_found(client, token):
    max_id = 999999
    response = client.patch(
        f'/quartos/{max_id}/membros',
        json={'membro_id': 1},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()['detail'] == 'Quarto não encontrado'


def test_adicionar_membro_unauthorized(client, token, quarto, other_user):
    response_other = client.post(
        '/auth/login/',
        data={'username': 'otheruser@test.com', 'password': 'OtherPass123!'},
    )
    other_token = response_other.json()['access_token']

    response = client.patch(
        f'/quartos/{quarto.id}/membros',
        json={'membro_id': 1},
        headers={'Authorization': f'Bearer {other_token}'},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json()['detail'] == 'Permissões negadas'


def test_adicionar_membro_not_found(client, token, quarto):
    max_id = 999999
    response = client.patch(
        f'/quartos/{quarto.id}/membros',
        json={'membro_id': max_id},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()['detail'] == 'Membro não encontrado'


def test_adicionar_membro_different_republica(
    client, token, republica, quarto, session
):
    # Create another república
    republica2_data = {
        'nome': 'República Teste 2',
        'cep': '54321000',
        'rua': 'Rua B',
        'numero': '200',
        'bairro': 'Bairro B',
        'cidade': 'Cidade B',
        'estado': 'Estado B',
    }
    response_rep2 = client.post(
        '/republicas',
        json=republica2_data,
        headers={'Authorization': f'Bearer {token}'},
    )
    republica2 = response_rep2.json()

    # Create a member in the second república
    membro_data = {
        'fullname': 'Membro Rep 2',
        'email': 'membro2@test.com',
        'telephone': '777777777',
    }
    response_membro = client.post(
        f'/membros/{republica2["id"]}',
        json=membro_data,
        headers={'Authorization': f'Bearer {token}'},
    )
    membro2 = response_membro.json()

    # Try to add member from república 2 to quarto from república 1
    response = client.patch(
        f'/quartos/{quarto.id}/membros',
        json={'membro_id': membro2['id']},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert (
        response.json()['detail']
        == 'Membro não pertence à mesma república do quarto'
    )


def test_adicionar_membro_quarto_already_occupied(  # noqa: PLR0913, PLR0917
    client, token, republica, quarto, membro, session
):
    # Create another member
    data = {
        'fullname': 'Segundo Membro',
        'email': 'segundo@test.com',
        'telephone': '666666666',
    }
    response_create = client.post(
        f'/membros/{republica.id}',
        json=data,
        headers={'Authorization': f'Bearer {token}'},
    )
    membro2 = response_create.json()

    # Try to add second member to already occupied quarto
    response = client.patch(
        f'/quartos/{quarto.id}/membros',
        json={'membro_id': membro2['id']},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.CONFLICT
    assert 'Quarto já está ocupado por' in response.json()['detail']


def test_remover_membro_do_quarto_success(  # noqa: PLR0913, PLR0917
    client, token, republica, quarto, membro, session
):
    # Create a second quarto
    response_quarto2 = client.post(
        '/quartos/',
        params={'republica_id': republica.id},
        json={'numero': 202},
        headers={'Authorization': f'Bearer {token}'},
    )
    quarto2 = response_quarto2.json()

    # Transfer member from quarto to quarto2
    response = client.delete(
        f'/quartos/{quarto.id}/membros/{membro.id}?novo_quarto_id={quarto2["id"]}',
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()['message'] == 'Membro transferido'


def test_remover_membro_quarto_not_found(client, token, membro):
    max_id = 999999
    response = client.delete(
        f'/quartos/{max_id}/membros/{membro.id}?novo_quarto_id=1',
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()['detail'] == 'Quarto não encontrado'


def test_remover_membro_unauthorized(  # noqa: PLR0913, PLR0917
    client, token, quarto, membro, other_user, session
):
    response_other = client.post(
        '/auth/login/',
        data={'username': 'otheruser@test.com', 'password': 'OtherPass123!'},
    )
    other_token = response_other.json()['access_token']

    # Create a second quarto for the transfer
    response_quarto2 = client.post(
        '/quartos/',
        params={'republica_id': quarto.republica_id},
        json={'numero': 303},
        headers={'Authorization': f'Bearer {token}'},
    )
    quarto2 = response_quarto2.json()

    response = client.delete(
        f'/quartos/{quarto.id}/membros/{membro.id}?novo_quarto_id={quarto2["id"]}',
        headers={'Authorization': f'Bearer {other_token}'},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json()['detail'] == 'Permissões negadas'


def test_remover_membro_not_found(client, token, quarto, session):
    max_id = 999999

    # Create a second quarto
    response_quarto2 = client.post(
        '/quartos/',
        params={'republica_id': quarto.republica_id},
        json={'numero': 404},
        headers={'Authorization': f'Bearer {token}'},
    )
    quarto2 = response_quarto2.json()

    response = client.delete(
        f'/quartos/{quarto.id}/membros/{max_id}?novo_quarto_id={quarto2["id"]}',
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()['detail'] == 'Membro não encontrado'


def test_remover_membro_not_in_quarto(
    client, token, republica, quarto, session
):
    # Create a member without a room
    data = {
        'fullname': 'Membro Sem Quarto',
        'email': 'semquarto@test.com',
        'telephone': '555555555',
    }
    response_create = client.post(
        f'/membros/{republica.id}',
        json=data,
        headers={'Authorization': f'Bearer {token}'},
    )
    membro_sem_quarto = response_create.json()

    # Create a second quarto
    response_quarto2 = client.post(
        '/quartos/',
        params={'republica_id': republica.id},
        json={'numero': 505},
        headers={'Authorization': f'Bearer {token}'},
    )
    quarto2 = response_quarto2.json()

    response = client.delete(
        f'/quartos/{quarto.id}/membros/{membro_sem_quarto["id"]}?novo_quarto_id={quarto2["id"]}',
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json()['detail'] == 'Membro não está neste quarto'


def test_remover_membro_novo_quarto_not_found(
    client, token, quarto, membro, session
):
    max_id = 999999
    response = client.delete(
        f'/quartos/{quarto.id}/membros/{membro.id}?novo_quarto_id={max_id}',
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()['detail'] == 'Novo quarto não encontrado'


def test_remover_membro_novo_quarto_different_republica(  # noqa: PLR0913, PLR0917
    client, token, republica, quarto, membro, session
):
    # Create another república
    republica2_data = {
        'nome': 'República Teste 3',
        'cep': '11111000',
        'rua': 'Rua C',
        'numero': '300',
        'bairro': 'Bairro C',
        'cidade': 'Cidade C',
        'estado': 'Estado C',
    }
    response_rep2 = client.post(
        '/republicas',
        json=republica2_data,
        headers={'Authorization': f'Bearer {token}'},
    )
    republica2 = response_rep2.json()

    # Create a quarto in the second república
    response_quarto2 = client.post(
        '/quartos/',
        params={'republica_id': republica2['id']},
        json={'numero': 606},
        headers={'Authorization': f'Bearer {token}'},
    )
    quarto2 = response_quarto2.json()

    # Try to transfer member to quarto in different república
    response = client.delete(
        f'/quartos/{quarto.id}/membros/{membro.id}?novo_quarto_id={quarto2["id"]}',
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert (
        response.json()['detail']
        == 'Novo quarto não pertence à mesma república'
    )


def test_desocupar_membro_should_succeed(
    client: TestClient, token, republica, quarto, membro
):
    """Test that desocupar endpoint sets membro.quarto_id to None."""

    # Verify membro is assigned to quarto
    assert membro.quarto_id == quarto.id

    response = client.patch(
        f'/quartos/{quarto.id}/desocupar',
        json={'membro_id': membro.id},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert 'desocupado' in data['message'].lower()

    # Verify membro.quarto_id is now None
    session = object_session(membro)
    session.refresh(membro)
    assert membro.quarto_id is None


def test_delete_quarto_after_desocupar_should_succeed(
    client: TestClient, token, republica, quarto, membro
):
    """Test that after desocupar, quarto can be deleted."""
    # First desocupar
    client.patch(
        f'/quartos/{quarto.id}/desocupar',
        json={'membro_id': membro.id},
        headers={'Authorization': f'Bearer {token}'},
    )

    # Now delete should work
    response = client.delete(
        f'/quartos/{quarto.id}?republica_id={republica.id}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert 'excluido' in data['message'].lower()


def test_create_membro_without_quarto_should_succeed(
    client: TestClient, token, republica
):
    membro_data = {
        'fullname': 'New Membro',
        'email': 'newmembro@test.com',
        'telephone': '61977777777',
        'quarto_id': None,
    }

    response = client.post(
        f'/membros/{republica.id}',
        json=membro_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data['fullname'] == membro_data['fullname']
    assert data['quarto_id'] is None
