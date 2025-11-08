"""Testes parametrizados para validação de diferentes cenários."""

from datetime import date
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
    Republica,
    User,
    table_registry,
)
from republica_facil.security import create_access_token, get_password_hash
from republica_facil.usuarios.service import (
    verify_fullname,
    verify_length_telephone,
    verify_strong_password,
)


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
        fullname='Test User Complete',
        email='testuser@example.com',
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


# =============================================================================
# TESTES PARAMETRIZADOS - CRIAÇÃO DE USUÁRIOS
# =============================================================================


@pytest.mark.parametrize(
    ('user_data', 'expected_status', 'expected_detail'),
    [
        # Caso 1: Usuário válido com dados completos
        (
            {
                'fullname': 'Usuario Teste Silva',
                'email': 'usuario1@example.com',
                'password': 'Senha@123',
                'telephone': '11988888888',
            },
            HTTPStatus.CREATED,
            None,
        ),
        # Caso 2: Usuário com senha fraca
        (
            {
                'fullname': 'Usuario Teste Santos',
                'email': 'usuario2@example.com',
                'password': 'senha123',
                'telephone': '11977777777',
            },
            HTTPStatus.UNPROCESSABLE_ENTITY,
            'Weak password',
        ),
        # Caso 3: Usuário com telefone inválido
        (
            {
                'fullname': 'Usuario Teste Oliveira',
                'email': 'usuario3@example.com',
                'password': 'Senha@123',
                'telephone': '1234567',
            },
            HTTPStatus.UNPROCESSABLE_ENTITY,
            'Verifies if a phone number is valid',
        ),
        # Caso 4: Usuário com nome incompleto
        (
            {
                'fullname': 'Usuario',
                'email': 'usuario4@example.com',
                'password': 'Senha@123',
                'telephone': '11966666666',
            },
            HTTPStatus.UNPROCESSABLE_ENTITY,
            'Enter your full name',
        ),
        # Caso 5: Usuário com email inválido
        (
            {
                'fullname': 'Usuario Teste Pereira',
                'email': 'emailinvalido',
                'password': 'Senha@123',
                'telephone': '11955555555',
            },
            HTTPStatus.UNPROCESSABLE_ENTITY,
            None,  # Pydantic validation
        ),
    ],
    ids=[
        'usuario_valido',
        'senha_fraca',
        'telefone_invalido',
        'nome_incompleto',
        'email_invalido',
    ],
)
def test_create_user_parametrized(
    client, user_data, expected_status, expected_detail
):
    """Testa criação de usuário com diferentes cenários."""
    response = client.post('/users', json=user_data)

    assert response.status_code == expected_status

    if expected_detail:
        assert expected_detail in response.json()['detail']


# =============================================================================
# TESTES PARAMETRIZADOS - LOGIN
# =============================================================================


@pytest.mark.parametrize(
    ('credentials', 'expected_status', 'has_token'),
    [
        # Caso 1: Login com credenciais corretas
        (
            {
                'username': 'testuser@example.com',
                'password': 'testpass123',
            },
            HTTPStatus.OK,
            True,
        ),
        # Caso 2: Login com senha incorreta
        (
            {
                'username': 'testuser@example.com',
                'password': 'senhaerrada',
            },
            HTTPStatus.UNAUTHORIZED,
            False,
        ),
        # Caso 3: Login com email inexistente
        (
            {
                'username': 'naoexiste@example.com',
                'password': 'testpass123',
            },
            HTTPStatus.UNAUTHORIZED,
            False,
        ),
        # Caso 4: Login sem username
        (
            {
                'password': 'testpass123',
            },
            HTTPStatus.UNPROCESSABLE_ENTITY,
            False,
        ),
        # Caso 5: Login sem password
        (
            {
                'username': 'testuser@example.com',
            },
            HTTPStatus.UNPROCESSABLE_ENTITY,
            False,
        ),
    ],
    ids=[
        'login_correto',
        'senha_incorreta',
        'email_inexistente',
        'sem_username',
        'sem_password',
    ],
)
def test_login_parametrized(
    client, user, credentials, expected_status, has_token
):
    """Testa login com diferentes cenários."""
    response = client.post('/auth/login', data=credentials)

    assert response.status_code == expected_status

    if has_token:
        assert 'access_token' in response.json()
        assert response.json()['token_type'] == 'Bearer'
    else:
        assert 'access_token' not in response.json()


# =============================================================================
# TESTES PARAMETRIZADOS - CRIAÇÃO DE REPÚBLICAS
# =============================================================================


@pytest.mark.parametrize(
    ('republica_data', 'expected_status', 'should_have_id'),
    [
        # Caso 1: República válida completa
        (
            {
                'nome': 'República Central',
                'cep': '12345678',
                'rua': 'Rua das Flores',
                'numero': '100',
                'bairro': 'Centro',
                'cidade': 'São Paulo',
                'estado': 'SP',
                'complemento': 'Apto 101',
            },
            HTTPStatus.CREATED,
            True,
        ),
        # Caso 2: República válida sem complemento
        (
            {
                'nome': 'República Zona Norte',
                'cep': '87654321',
                'rua': 'Avenida Principal',
                'numero': '200',
                'bairro': 'Santana',
                'cidade': 'São Paulo',
                'estado': 'SP',
            },
            HTTPStatus.CREATED,
            True,
        ),
        # Caso 3: República com nome muito curto
        (
            {
                'nome': 'Rep',
                'cep': '11111111',
                'rua': 'Rua Teste',
                'numero': '300',
                'bairro': 'Bairro',
                'cidade': 'São Paulo',
                'estado': 'SP',
            },
            HTTPStatus.CREATED,
            True,
        ),
        # Caso 4: República com CEP diferente
        (
            {
                'nome': 'República Zona Sul',
                'cep': '04567890',
                'rua': 'Rua do Sul',
                'numero': '400',
                'bairro': 'Vila Mariana',
                'cidade': 'São Paulo',
                'estado': 'SP',
            },
            HTTPStatus.CREATED,
            True,
        ),
        # Caso 5: República em outro estado
        (
            {
                'nome': 'República Carioca',
                'cep': '20000000',
                'rua': 'Avenida Atlântica',
                'numero': '500',
                'bairro': 'Copacabana',
                'cidade': 'Rio de Janeiro',
                'estado': 'RJ',
            },
            HTTPStatus.CREATED,
            True,
        ),
    ],
    ids=[
        'republica_completa',
        'sem_complemento',
        'nome_curto',
        'cep_diferente',
        'outro_estado',
    ],
)
def test_create_republica_parametrized(
    client, token, republica_data, expected_status, should_have_id
):
    """Testa criação de república com diferentes cenários."""
    headers = {'Authorization': f'Bearer {token}'}
    response = client.post('/republicas', json=republica_data, headers=headers)

    assert response.status_code == expected_status

    if should_have_id:
        assert 'id' in response.json()
        assert response.json()['nome'] == republica_data['nome']


# =============================================================================
# TESTES PARAMETRIZADOS - CRIAÇÃO DE QUARTOS
# =============================================================================


@pytest.mark.parametrize(
    ('quarto_data', 'expected_status', 'should_succeed'),
    [
        # Caso 1: Quarto com número baixo
        (
            {'numero': 1},
            HTTPStatus.CREATED,
            True,
        ),
        # Caso 2: Quarto com número médio
        (
            {'numero': 101},
            HTTPStatus.CREATED,
            True,
        ),
        # Caso 3: Quarto com número alto
        (
            {'numero': 999},
            HTTPStatus.CREATED,
            True,
        ),
        # Caso 4: Quarto com número zero
        (
            {'numero': 0},
            HTTPStatus.CREATED,
            True,
        ),
        # Caso 5: Quarto com número negativo
        (
            {'numero': -1},
            HTTPStatus.CREATED,
            True,
        ),
    ],
    ids=[
        'numero_baixo',
        'numero_medio',
        'numero_alto',
        'numero_zero',
        'numero_negativo',
    ],
)
def test_create_quarto_parametrized(  # noqa: PLR0913, PLR0917
    client, token, republica, quarto_data, expected_status, should_succeed
):
    """Testa criação de quarto com diferentes números."""
    headers = {'Authorization': f'Bearer {token}'}
    response = client.post(
        f'/quartos/?republica_id={republica.id}',
        json=quarto_data,
        headers=headers,
    )

    assert response.status_code == expected_status

    if should_succeed:
        assert response.json()['numero'] == quarto_data['numero']


# =============================================================================
# TESTES PARAMETRIZADOS - CRIAÇÃO DE MEMBROS
# =============================================================================


@pytest.mark.parametrize(
    ('membro_data', 'expected_status', 'error_key'),
    [
        # Caso 1: Membro válido completo
        (
            {
                'fullname': 'Maria Silva Santos',
                'email': 'maria@example.com',
                'telephone': '11988888888',
            },
            HTTPStatus.CREATED,
            None,
        ),
        # Caso 2: Membro com nome diferente
        (
            {
                'fullname': 'João Pedro Oliveira',
                'email': 'joao@example.com',
                'telephone': '11977777777',
            },
            HTTPStatus.CREATED,
            None,
        ),
        # Caso 3: Membro com telefone de área diferente
        (
            {
                'fullname': 'Ana Carolina Souza',
                'email': 'ana@example.com',
                'telephone': '21966666666',
            },
            HTTPStatus.CREATED,
            None,
        ),
        # Caso 4: Membro com nome composto
        (
            {
                'fullname': 'Carlos Eduardo Mendes',
                'email': 'carlos@example.com',
                'telephone': '31955555555',
            },
            HTTPStatus.CREATED,
            None,
        ),
        # Caso 5: Membro com sobrenome composto
        (
            {
                'fullname': 'Juliana Alves Costa',
                'email': 'juliana@example.com',
                'telephone': '41944444444',
            },
            HTTPStatus.CREATED,
            None,
        ),
    ],
    ids=[
        'membro_maria',
        'membro_joao',
        'telefone_rj',
        'nome_composto',
        'sobrenome_composto',
    ],
)
def test_create_membro_parametrized(  # noqa: PLR0913, PLR0917
    client, token, republica, membro_data, expected_status, error_key
):
    """Testa criação de membro com diferentes dados."""
    headers = {'Authorization': f'Bearer {token}'}
    response = client.post(
        f'/membros/{republica.id}', json=membro_data, headers=headers
    )

    assert response.status_code == expected_status

    if error_key is None:
        assert response.json()['fullname'] == membro_data['fullname']
        assert response.json()['email'] == membro_data['email']


# =============================================================================
# TESTES PARAMETRIZADOS - CRIAÇÃO DE DESPESAS
# =============================================================================


@pytest.mark.parametrize(
    ('despesa_data', 'expected_status', 'should_succeed'),
    [
        # Caso 1: Despesa de luz
        (
            {
                'descricao': 'Conta de Luz - Janeiro',
                'valor_total': 200.0,
                'data_vencimento': '2024-01-31',
                'categoria': 'luz',
            },
            HTTPStatus.CREATED,
            True,
        ),
        # Caso 2: Despesa de água
        (
            {
                'descricao': 'Conta de Água - Fevereiro',
                'valor_total': 150.0,
                'data_vencimento': '2024-02-28',
                'categoria': 'agua',
            },
            HTTPStatus.CREATED,
            True,
        ),
        # Caso 3: Despesa de internet
        (
            {
                'descricao': 'Internet Fibra 500MB',
                'valor_total': 99.90,
                'data_vencimento': '2024-03-10',
                'categoria': 'internet',
            },
            HTTPStatus.CREATED,
            True,
        ),
        # Caso 4: Despesa de condomínio
        (
            {
                'descricao': 'Condomínio Março',
                'valor_total': 350.0,
                'data_vencimento': '2024-03-05',
                'categoria': 'condominio',
            },
            HTTPStatus.CREATED,
            True,
        ),
        # Caso 5: Despesa de limpeza
        (
            {
                'descricao': 'Produtos de Limpeza',
                'valor_total': 80.0,
                'data_vencimento': '2024-04-15',
                'categoria': 'limpeza',
            },
            HTTPStatus.CREATED,
            True,
        ),
    ],
    ids=[
        'despesa_luz',
        'despesa_agua',
        'despesa_internet',
        'despesa_condominio',
        'despesa_limpeza',
    ],
)
def test_create_despesa_parametrized(  # noqa: PLR0913, PLR0917
    client, token, republica, despesa_data, expected_status, should_succeed
):
    """Testa criação de despesa com diferentes categorias."""
    headers = {'Authorization': f'Bearer {token}'}
    response = client.post(
        f'/despesas/{republica.id}', json=despesa_data, headers=headers
    )

    assert response.status_code == expected_status

    if should_succeed:
        assert response.json()['descricao'] == despesa_data['descricao']
        assert response.json()['valor_total'] == despesa_data['valor_total']
        assert response.json()['categoria'] == despesa_data['categoria']
        assert response.json()['status'] == 'pendente'


# =============================================================================
# TESTES PARAMETRIZADOS - VALIDAÇÃO DE SENHA
# =============================================================================


@pytest.mark.parametrize(
    ('password', 'expected_valid', 'error_message'),
    [
        # Caso 1: Senha válida forte
        ('Senha@123', True, None),
        # Caso 2: Senha sem caractere especial
        ('Senha1234', False, 'one special character'),
        # Caso 3: Senha sem letra maiúscula
        ('senha@123', False, 'one uppercase letter'),
        # Caso 4: Senha sem número
        ('Senha@abc', False, 'one digit'),
        # Caso 5: Senha muito curta
        ('Se@1', False, 'at least 8 characters'),
        # Caso 6: Senha válida com múltiplos caracteres especiais
        ('S3nh@!For', True, None),
    ],
    ids=[
        'senha_forte',
        'sem_especial',
        'sem_maiuscula',
        'sem_numero',
        'muito_curta',
        'multiplos_especiais',
    ],
)
def test_password_validation_parametrized(
    password,
    expected_valid,
    error_message,  # noqa: ARG001
):
    """Testa validação de senha com diferentes padrões."""
    result = verify_strong_password(password)

    assert result == expected_valid


# =============================================================================
# TESTES PARAMETRIZADOS - VALIDAÇÃO DE TELEFONE
# =============================================================================


@pytest.mark.parametrize(
    ('telephone', 'expected_valid'),
    [
        # Caso 1: Telefone válido de SP
        ('11999999999', True),
        # Caso 2: Telefone válido do RJ
        ('21988888888', True),
        # Caso 3: Telefone válido de MG
        ('31977777777', True),
        # Caso 4: Telefone muito curto
        ('119999', False),
        # Caso 5: Telefone muito longo
        ('119999999999999', False),
        # Caso 6: Telefone com 10 dígitos (fixo)
        ('1199999999', True),
    ],
    ids=[
        'sp_valido',
        'rj_valido',
        'mg_valido',
        'muito_curto',
        'muito_longo',
        'fixo_valido',
    ],
)
def test_telephone_validation_parametrized(telephone, expected_valid):
    """Testa validação de telefone com diferentes formatos."""
    result = verify_length_telephone(telephone)

    assert result == expected_valid


# =============================================================================
# TESTES PARAMETRIZADOS - VALIDAÇÃO DE NOME COMPLETO
# =============================================================================


@pytest.mark.parametrize(
    ('fullname', 'expected_valid'),
    [
        # Caso 1: Nome completo válido
        ('João Silva Santos', True),
        # Caso 2: Nome com sobrenome composto
        ('Maria Silva Costa', True),
        # Caso 3: Nome simples (inválido)
        ('João', False),
        # Caso 4: Nome com sobrenome muito curto
        ('João Li', False),
        # Caso 5: Nome válido com três partes
        ('Ana Paula Oliveira', True),
        # Caso 6: Nome com duas palavras curtas
        ('João Da', False),
    ],
    ids=[
        'nome_valido',
        'sobrenome_composto',
        'nome_simples',
        'sobrenome_curto',
        'tres_partes',
        'duas_curtas',
    ],
)
def test_fullname_validation_parametrized(fullname, expected_valid):
    """Testa validação de nome completo com diferentes formatos."""
    result = verify_fullname(fullname)

    assert result == expected_valid


# =============================================================================
# TESTES PARAMETRIZADOS - ATUALIZAÇÃO DE DESPESAS
# =============================================================================


@pytest.mark.parametrize(
    ('update_data', 'field_to_check', 'expected_value'),
    [
        # Caso 1: Atualizar descrição
        (
            {
                'descricao': 'Conta de Luz - ATUALIZADA',
                'valor_total': 200.0,
                'data_vencimento': '2024-01-31',
                'categoria': 'luz',
            },
            'descricao',
            'Conta de Luz - ATUALIZADA',
        ),
        # Caso 2: Atualizar valor
        (
            {
                'descricao': 'Conta de Luz',
                'valor_total': 250.0,
                'data_vencimento': '2024-01-31',
                'categoria': 'luz',
            },
            'valor_total',
            250.0,
        ),
        # Caso 3: Atualizar data de vencimento
        (
            {
                'descricao': 'Conta de Luz',
                'valor_total': 200.0,
                'data_vencimento': '2024-02-15',
                'categoria': 'luz',
            },
            'data_vencimento',
            '2024-02-15',
        ),
        # Caso 4: Atualizar categoria
        (
            {
                'descricao': 'Conta de Luz',
                'valor_total': 200.0,
                'data_vencimento': '2024-01-31',
                'categoria': 'gas',
            },
            'categoria',
            'gas',
        ),
        # Caso 5: Atualizar múltiplos campos
        (
            {
                'descricao': 'Nova Despesa',
                'valor_total': 300.0,
                'data_vencimento': '2024-03-20',
                'categoria': 'outros',
            },
            'valor_total',
            300.0,
        ),
    ],
    ids=[
        'atualizar_descricao',
        'atualizar_valor',
        'atualizar_data',
        'atualizar_categoria',
        'atualizar_multiplos',
    ],
)
def test_update_despesa_parametrized(  # noqa: PLR0913, PLR0917
    client,
    token,
    republica,
    session,
    update_data,
    field_to_check,
    expected_value,
):
    """Testa atualização de despesa com diferentes campos."""
    # Criar despesa inicial
    despesa = Despesa(
        descricao='Conta de Luz',
        valor_total=200.0,
        data_vencimento=date(2024, 1, 31),
        categoria='luz',
        republica_id=republica.id,
    )
    session.add(despesa)
    session.commit()
    session.refresh(despesa)

    headers = {'Authorization': f'Bearer {token}'}
    response = client.patch(
        f'/despesas/{republica.id}/{despesa.id}',
        json=update_data,
        headers=headers,
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json()[field_to_check] == expected_value
