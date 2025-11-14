"""Testes para o módulo de despesas."""

from datetime import date, timedelta
from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from republica_facil.database import get_session
from republica_facil.main import app
from republica_facil.model.models import (
    Despesa,
    Membro,
    Pagamento,
    Republica,
    StatusDespesa,
    TipoDespesa,
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
def despesa(session, republica):
    """Cria uma despesa de teste."""
    despesa = Despesa(
        descricao='Conta de Luz',
        valor_total=150.00,
        data_vencimento=date.today() + timedelta(days=7),
        categoria=TipoDespesa.LUZ,
        republica_id=republica.id,
    )
    session.add(despesa)
    session.commit()
    session.refresh(despesa)
    return despesa


@pytest.fixture
def membro(session, republica):
    """Cria um membro de teste."""
    membro = Membro(
        fullname='Membro Teste',
        email='membro@example.com',
        telephone='11977777777',
        republica_id=republica.id,
    )
    session.add(membro)
    session.commit()
    session.refresh(membro)
    return membro


@pytest.fixture
def membro2(session, republica):
    """Cria um segundo membro de teste."""
    membro = Membro(
        fullname='Membro Teste 2',
        email='membro2@example.com',
        telephone='11966666666',
        republica_id=republica.id,
    )
    session.add(membro)
    session.commit()
    session.refresh(membro)
    return membro


# Testes do endpoint POST /despesas/{republica_id}


def test_create_despesa_success(client, token, republica):
    """Testa criação de despesa com sucesso."""
    despesa_data = {
        'descricao': 'Conta de Água',
        'valor_total': 100.00,
        'data_vencimento': str(date.today() + timedelta(days=10)),
        'categoria': TipoDespesa.AGUA.value,
    }

    response = client.post(
        f'/despesas/{republica.id}',
        json=despesa_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data['descricao'] == despesa_data['descricao']
    assert data['valor_total'] == despesa_data['valor_total']
    assert data['categoria'] == despesa_data['categoria']
    assert data['status'] == StatusDespesa.PENDENTE.value
    assert 'id' in data


def test_create_despesa_republica_not_found(client, token):
    """Testa criação de despesa em república inexistente."""
    despesa_data = {
        'descricao': 'Conta de Água',
        'valor_total': 100.00,
        'data_vencimento': str(date.today() + timedelta(days=10)),
        'categoria': TipoDespesa.AGUA.value,
    }

    response = client.post(
        '/despesas/999',
        json=despesa_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert 'República não encontrada' in response.json()['detail']


def test_create_despesa_unauthorized(client, other_token, republica):
    """Testa criação de despesa por usuário não autorizado."""
    despesa_data = {
        'descricao': 'Conta de Água',
        'valor_total': 100.00,
        'data_vencimento': str(date.today() + timedelta(days=10)),
        'categoria': TipoDespesa.AGUA.value,
    }

    response = client.post(
        f'/despesas/{republica.id}',
        json=despesa_data,
        headers={'Authorization': f'Bearer {other_token}'},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert 'Permissões negadas' in response.json()['detail']


def test_create_despesa_without_token(client, republica):
    """Testa criação de despesa sem token de autenticação."""
    despesa_data = {
        'descricao': 'Conta de Água',
        'valor_total': 100.00,
        'data_vencimento': str(date.today() + timedelta(days=10)),
        'categoria': TipoDespesa.AGUA.value,
    }

    response = client.post(
        f'/despesas/{republica.id}',
        json=despesa_data,
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED


# Testes do endpoint GET /despesas/{republica_id}


def test_read_despesas_success(client, token, republica, despesa):
    """Testa listagem de despesas com sucesso."""
    response = client.get(
        f'/despesas/{republica.id}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert 'despesas' in data
    assert len(data['despesas']) == 1
    assert data['despesas'][0]['id'] == despesa.id


def test_read_despesas_empty_list(client, token, republica):
    """Testa listagem de despesas vazia."""
    response = client.get(
        f'/despesas/{republica.id}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert 'despesas' in data
    assert len(data['despesas']) == 0


def test_read_despesas_republica_not_found(client, token):
    """Testa listagem de despesas em república inexistente."""
    response = client.get(
        '/despesas/999',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert 'República não encontrada' in response.json()['detail']


def test_read_despesas_unauthorized(client, other_token, republica):
    """Testa listagem de despesas por usuário não autorizado."""
    response = client.get(
        f'/despesas/{republica.id}',
        headers={'Authorization': f'Bearer {other_token}'},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert 'Permissões negadas' in response.json()['detail']


# Testes do endpoint GET /despesas/{republica_id}/{despesa_id}


def test_read_despesa_success(client, token, republica, despesa):
    """Testa leitura de despesa específica com sucesso."""
    response = client.get(
        f'/despesas/{republica.id}/{despesa.id}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['id'] == despesa.id
    assert data['descricao'] == despesa.descricao
    assert data['valor_total'] == despesa.valor_total


def test_read_despesa_republica_not_found(client, token, despesa):
    """Testa leitura de despesa em república inexistente."""
    response = client.get(
        f'/despesas/999/{despesa.id}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert 'República não encontrada' in response.json()['detail']


def test_read_despesa_unauthorized(client, other_token, republica, despesa):
    """Testa leitura de despesa por usuário não autorizado."""
    response = client.get(
        f'/despesas/{republica.id}/{despesa.id}',
        headers={'Authorization': f'Bearer {other_token}'},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert 'Permissões negadas' in response.json()['detail']


def test_read_despesa_not_found(client, token, republica):
    """Testa leitura de despesa inexistente."""
    response = client.get(
        f'/despesas/{republica.id}/999',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert 'Despesa não encontrada' in response.json()['detail']


# Testes do endpoint PATCH /despesas/{republica_id}/{despesa_id}


def test_update_despesa_success(client, token, republica, despesa):
    """Testa atualização de despesa com sucesso."""
    update_data = {
        'descricao': 'Conta de Luz Atualizada',
        'valor_total': 200.00,
        'data_vencimento': str(date.today() + timedelta(days=15)),
        'categoria': TipoDespesa.LUZ.value,
    }

    response = client.patch(
        f'/despesas/{republica.id}/{despesa.id}',
        json=update_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['descricao'] == update_data['descricao']
    assert data['valor_total'] == update_data['valor_total']


def test_update_despesa_republica_not_found(client, token, despesa):
    """Testa atualização de despesa em república inexistente."""
    update_data = {
        'descricao': 'Conta de Luz Atualizada',
        'valor_total': 200.00,
        'data_vencimento': str(date.today() + timedelta(days=15)),
        'categoria': TipoDespesa.LUZ.value,
    }

    response = client.patch(
        f'/despesas/999/{despesa.id}',
        json=update_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert 'República não encontrada' in response.json()['detail']


def test_update_despesa_unauthorized(client, other_token, republica, despesa):
    """Testa atualização de despesa por usuário não autorizado."""
    update_data = {
        'descricao': 'Conta de Luz Atualizada',
        'valor_total': 200.00,
        'data_vencimento': str(date.today() + timedelta(days=15)),
        'categoria': TipoDespesa.LUZ.value,
    }

    response = client.patch(
        f'/despesas/{republica.id}/{despesa.id}',
        json=update_data,
        headers={'Authorization': f'Bearer {other_token}'},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert 'Permissões negadas' in response.json()['detail']


def test_update_despesa_not_found(client, token, republica):
    """Testa atualização de despesa inexistente."""
    update_data = {
        'descricao': 'Conta de Luz Atualizada',
        'valor_total': 200.00,
        'data_vencimento': str(date.today() + timedelta(days=15)),
        'categoria': TipoDespesa.LUZ.value,
    }

    response = client.patch(
        f'/despesas/{republica.id}/999',
        json=update_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert 'Despesa não encontrada' in response.json()['detail']


# Testes do endpoint DELETE /despesas/{republica_id}/{despesa_id}


def test_delete_despesa_success(client, token, republica, despesa):
    """Testa exclusão de despesa com sucesso."""
    response = client.delete(
        f'/despesas/{republica.id}/{despesa.id}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert 'Despesa excluída com sucesso' in data['message']


def test_delete_despesa_republica_not_found(client, token, despesa):
    """Testa exclusão de despesa em república inexistente."""
    response = client.delete(
        f'/despesas/999/{despesa.id}',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert 'República não encontrada' in response.json()['detail']


def test_delete_despesa_unauthorized(client, other_token, republica, despesa):
    """Testa exclusão de despesa por usuário não autorizado."""
    response = client.delete(
        f'/despesas/{republica.id}/{despesa.id}',
        headers={'Authorization': f'Bearer {other_token}'},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert 'Permissões negadas' in response.json()['detail']


def test_delete_despesa_not_found(client, token, republica):
    """Testa exclusão de despesa inexistente."""
    response = client.delete(
        f'/despesas/{republica.id}/999',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert 'Despesa não encontrada' in response.json()['detail']


# Testes do endpoint POST /despesas/{republica_id}/{despesa_id}/pagamento


def test_registrar_pagamento_success(
    client, token, republica, despesa, membro
):
    """Testa registro de pagamento com sucesso."""
    pagamento_data = {'membro_id': membro.id}

    response = client.post(
        f'/despesas/{republica.id}/{despesa.id}/pagamento',
        json=pagamento_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data['membro_id'] == membro.id
    assert data['despesa_id'] == despesa.id
    assert data['valor_pago'] == despesa.valor_total  # 1 membro
    assert 'id' in data
    assert 'data_pagamento' in data


def test_registrar_pagamento_republica_not_found(
    client, token, despesa, membro
):
    """Testa registro de pagamento em república inexistente."""
    pagamento_data = {'membro_id': membro.id}

    response = client.post(
        f'/despesas/999/{despesa.id}/pagamento',
        json=pagamento_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert 'República não encontrada' in response.json()['detail']


def test_registrar_pagamento_unauthorized(
    client, other_token, republica, despesa, membro
):
    """Testa registro de pagamento por usuário não autorizado."""
    pagamento_data = {'membro_id': membro.id}

    response = client.post(
        f'/despesas/{republica.id}/{despesa.id}/pagamento',
        json=pagamento_data,
        headers={'Authorization': f'Bearer {other_token}'},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert 'Permissões negadas' in response.json()['detail']


def test_registrar_pagamento_despesa_not_found(
    client, token, republica, membro
):
    """Testa registro de pagamento em despesa inexistente."""
    pagamento_data = {'membro_id': membro.id}

    response = client.post(
        f'/despesas/{republica.id}/999/pagamento',
        json=pagamento_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert 'Despesa não encontrada' in response.json()['detail']


def test_registrar_pagamento_despesa_ja_paga(  # noqa: PLR0913, PLR0917
    client, token, republica, despesa, membro, session
):
    """Testa registro de pagamento em despesa já paga."""
    # Marcar despesa como paga
    despesa.status = StatusDespesa.PAGO
    session.commit()
    session.refresh(despesa)

    pagamento_data = {'membro_id': membro.id}

    response = client.post(
        f'/despesas/{republica.id}/{despesa.id}/pagamento',
        json=pagamento_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert 'já está marcada como paga' in response.json()['detail']


def test_registrar_pagamento_membro_not_found(
    client, token, republica, despesa
):
    """Testa registro de pagamento com membro inexistente."""
    pagamento_data = {'membro_id': 999}

    response = client.post(
        f'/despesas/{republica.id}/{despesa.id}/pagamento',
        json=pagamento_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert 'Membro não encontrado' in response.json()['detail']


def test_registrar_pagamento_membro_outra_republica(  # noqa: PLR0913, PLR0917
    client, token, republica, other_republica, despesa, session
):
    """Testa pagamento com membro de outra república."""
    # Criar membro em outra república
    membro_outro = Membro(
        fullname='Membro Outro',
        email='outro@example.com',
        telephone='11955555555',
        republica_id=other_republica.id,
    )
    session.add(membro_outro)
    session.commit()
    session.refresh(membro_outro)

    pagamento_data = {'membro_id': membro_outro.id}

    response = client.post(
        f'/despesas/{republica.id}/{despesa.id}/pagamento',
        json=pagamento_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert 'não pertence a esta república' in response.json()['detail']


def test_registrar_pagamento_duplicado(  # noqa: PLR0913, PLR0917
    client, token, republica, despesa, membro, session
):
    """Testa registro de pagamento duplicado."""
    # Criar primeiro pagamento
    pagamento = Pagamento(
        membro_id=membro.id,
        despesa_id=despesa.id,
        valor_pago=despesa.valor_total,
    )
    session.add(pagamento)
    session.commit()

    pagamento_data = {'membro_id': membro.id}

    response = client.post(
        f'/despesas/{republica.id}/{despesa.id}/pagamento',
        json=pagamento_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert 'já pagou esta despesa' in response.json()['detail']


def test_registrar_pagamento_sem_membros(client, token, session, user):
    """Testa registro de pagamento em república sem membros."""
    # Criar república sem membros
    republica_sem_membros = Republica(
        nome='República Sem Membros',
        cep='00000000',
        rua='Rua Vazia',
        numero='000',
        bairro='Vazio',
        cidade='Cidade',
        estado='XX',
        user_id=user.id,
    )
    session.add(republica_sem_membros)
    session.commit()
    session.refresh(republica_sem_membros)

    despesa_sem_membros = Despesa(
        descricao='Conta de Teste',
        valor_total=100.00,
        data_vencimento=date.today() + timedelta(days=7),
        categoria=TipoDespesa.LUZ,
        republica_id=republica_sem_membros.id,
    )
    session.add(despesa_sem_membros)
    session.commit()
    session.refresh(despesa_sem_membros)

    # Criar membro fake apenas para teste (mas não vinculado à república)
    membro_fake = Membro(
        fullname='Membro Fake',
        email='fake@example.com',
        telephone='11944444444',
        republica_id=republica_sem_membros.id,
    )
    session.add(membro_fake)
    session.commit()
    session.refresh(membro_fake)

    # Remover membro para simular república sem membros
    session.delete(membro_fake)
    session.commit()

    # Tentar registrar pagamento
    pagamento_data = {'membro_id': 999}

    response = client.post(
        f'/despesas/{republica_sem_membros.id}/{despesa_sem_membros.id}/pagamento',
        json=pagamento_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    # Deve falhar por membro não encontrado antes
    # de chegar na validação de república sem membros
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_registrar_pagamento_divide_valor(  # noqa: PLR0913, PLR0917
    client, token, republica, despesa, membro, membro2
):
    """Testa que o valor é dividido corretamente entre membros."""
    pagamento_data = {'membro_id': membro.id}

    response = client.post(
        f'/despesas/{republica.id}/{despesa.id}/pagamento',
        json=pagamento_data,
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    # Valor deve ser dividido por 2 membros
    assert data['valor_pago'] == despesa.valor_total / 2


def test_registrar_pagamento_marca_pago_quando_todos_pagam(  # noqa: PLR0913, PLR0917
    client, token, republica, despesa, membro, membro2, session
):
    """Testa que despesa é marcada como PAGO quando todos pagam."""
    # Primeiro pagamento
    pagamento_data1 = {'membro_id': membro.id}
    response1 = client.post(
        f'/despesas/{republica.id}/{despesa.id}/pagamento',
        json=pagamento_data1,
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response1.status_code == HTTPStatus.CREATED

    # Segundo pagamento
    pagamento_data2 = {'membro_id': membro2.id}
    response2 = client.post(
        f'/despesas/{republica.id}/{despesa.id}/pagamento',
        json=pagamento_data2,
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response2.status_code == HTTPStatus.CREATED

    # Verificar que despesa foi marcada como paga
    session.refresh(despesa)
    assert despesa.status == StatusDespesa.PAGO


# Testes do endpoint GET /despesas/{republica_id}/{despesa_id}/pagamentos


def test_listar_pagamentos_success(  # noqa: PLR0913, PLR0917
    client, token, republica, despesa, membro, session
):
    """Testa listagem de pagamentos com sucesso."""
    # Criar pagamento
    pagamento = Pagamento(
        membro_id=membro.id,
        despesa_id=despesa.id,
        valor_pago=despesa.valor_total,
    )
    session.add(pagamento)
    session.commit()

    response = client.get(
        f'/despesas/{republica.id}/{despesa.id}/pagamentos',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert 'pagamentos' in data
    assert len(data['pagamentos']) == 1
    assert data['pagamentos'][0]['membro_id'] == membro.id


def test_listar_pagamentos_empty(client, token, republica, despesa):
    """Testa listagem de pagamentos vazia."""
    response = client.get(
        f'/despesas/{republica.id}/{despesa.id}/pagamentos',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert 'pagamentos' in data
    assert len(data['pagamentos']) == 0


def test_listar_pagamentos_republica_not_found(client, token, despesa):
    """Testa listagem de pagamentos em república inexistente."""
    response = client.get(
        f'/despesas/999/{despesa.id}/pagamentos',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert 'República não encontrada' in response.json()['detail']


def test_listar_pagamentos_unauthorized(
    client, other_token, republica, despesa
):
    """Testa listagem de pagamentos por usuário não autorizado."""
    response = client.get(
        f'/despesas/{republica.id}/{despesa.id}/pagamentos',
        headers={'Authorization': f'Bearer {other_token}'},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert 'Permissões negadas' in response.json()['detail']


def test_listar_pagamentos_despesa_not_found(client, token, republica):
    """Testa listagem de pagamentos de despesa inexistente."""
    response = client.get(
        f'/despesas/{republica.id}/999/pagamentos',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert 'Despesa não encontrada' in response.json()['detail']
