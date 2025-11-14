"""Testes de integração - Fluxos completos da aplicação."""

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
    Pagamento,
    User,
    table_registry,
)
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


class TestFluxoCompletoRepublica:
    """Testa o fluxo completo de criação e gerenciamento de uma república."""

    def test_fluxo_completo_criar_e_gerenciar_republica(  # noqa: PLR0915, PLR0914, PLR6301
        self, client, session
    ):
        """
        Testa o fluxo completo:
        1. Criar usuário
        2. Fazer login
        3. Criar república
        4. Criar quartos
        5. Criar membros
        6. Alocar membros em quartos
        7. Criar despesa
        8. Registrar pagamentos
        9. Verificar status da despesa
        """
        # 1. Criar usuário
        user_data = {
            'fullname': 'João Silva',
            'email': 'joao@example.com',
            'password': 'Senha@123',
            'telephone': '11999999999',
        }
        response = client.post('/users', json=user_data)
        assert response.status_code == HTTPStatus.CREATED

        # 2. Fazer login
        login_data = {
            'username': 'joao@example.com',
            'password': 'Senha@123',
        }
        response = client.post('/auth/login', data=login_data)
        assert response.status_code == HTTPStatus.OK
        token = response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        # 3. Criar república
        republica_data = {
            'nome': 'República do João',
            'cep': '12345678',
            'rua': 'Rua das Flores',
            'numero': '123',
            'bairro': 'Centro',
            'cidade': 'São Paulo',
            'estado': 'SP',
        }
        response = client.post(
            '/republicas', json=republica_data, headers=headers
        )
        assert response.status_code == HTTPStatus.CREATED
        republica_id = response.json()['id']

        # 4. Criar quartos
        quarto1_data = {'numero': 101}
        response = client.post(
            f'/quartos/?republica_id={republica_id}',
            json=quarto1_data,
            headers=headers,
        )
        assert response.status_code == HTTPStatus.CREATED
        quarto1_id = response.json()['id']

        quarto2_data = {'numero': 102}
        response = client.post(
            f'/quartos/?republica_id={republica_id}',
            json=quarto2_data,
            headers=headers,
        )
        assert response.status_code == HTTPStatus.CREATED
        quarto2_id = response.json()['id']

        # 5. Criar membros (sem quarto inicialmente)
        membro1_data = {
            'fullname': 'Maria Santos',
            'email': 'maria@example.com',
            'telephone': '11988888888',
        }
        response = client.post(
            f'/membros/{republica_id}', json=membro1_data, headers=headers
        )
        assert response.status_code == HTTPStatus.CREATED
        membro1_id = response.json()['id']
        assert response.json()['quarto_id'] is None

        membro2_data = {
            'fullname': 'Pedro Oliveira',
            'email': 'pedro@example.com',
            'telephone': '11977777777',
        }
        response = client.post(
            f'/membros/{republica_id}', json=membro2_data, headers=headers
        )
        assert response.status_code == HTTPStatus.CREATED
        membro2_id = response.json()['id']

        # 6. Alocar membros em quartos
        response = client.patch(
            f'/quartos/{quarto1_id}/membros',
            json={'membro_id': membro1_id},
            headers=headers,
        )
        assert response.status_code == HTTPStatus.OK

        response = client.patch(
            f'/quartos/{quarto2_id}/membros',
            json={'membro_id': membro2_id},
            headers=headers,
        )
        assert response.status_code == HTTPStatus.OK

        # Verificar alocação
        expected_members_count = 2
        response = client.get(f'/membros/{republica_id}', headers=headers)
        assert response.status_code == HTTPStatus.OK
        membros = response.json()['members']
        assert len(membros) == expected_members_count
        assert all(m['quarto_id'] is not None for m in membros)

        # 7. Criar despesa
        despesa_data = {
            'descricao': 'Conta de Luz - Janeiro',
            'valor_total': 200.0,
            'data_vencimento': '2024-01-31',
            'categoria': 'luz',
        }
        response = client.post(
            f'/despesas/{republica_id}', json=despesa_data, headers=headers
        )
        assert response.status_code == HTTPStatus.CREATED
        despesa_id = response.json()['id']
        assert response.json()['status'] == 'pendente'

        # 8. Registrar pagamentos
        # Valor esperado por membro (200/2)
        expected_payment_value = 100.0

        # Primeiro membro paga
        pagamento1_data = {'membro_id': membro1_id}
        response = client.post(
            f'/despesas/{republica_id}/{despesa_id}/pagamento',
            json=pagamento1_data,
            headers=headers,
        )
        assert response.status_code == HTTPStatus.CREATED
        assert response.json()['valor_pago'] == expected_payment_value

        # Verificar que despesa ainda está pendente
        response = client.get(
            f'/despesas/{republica_id}/{despesa_id}', headers=headers
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json()['status'] == 'pendente'

        # Segundo membro paga
        pagamento2_data = {'membro_id': membro2_id}
        response = client.post(
            f'/despesas/{republica_id}/{despesa_id}/pagamento',
            json=pagamento2_data,
            headers=headers,
        )
        assert response.status_code == HTTPStatus.CREATED

        # 9. Verificar que despesa foi marcada como paga
        response = client.get(
            f'/despesas/{republica_id}/{despesa_id}', headers=headers
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json()['status'] == 'pago'

        # Verificar pagamentos registrados
        expected_payments_count = 2
        expected_total_value = 200.0
        response = client.get(
            f'/despesas/{republica_id}/{despesa_id}/pagamentos',
            headers=headers,
        )
        assert response.status_code == HTTPStatus.OK
        pagamentos = response.json()['pagamentos']
        assert len(pagamentos) == expected_payments_count
        assert sum(p['valor_pago'] for p in pagamentos) == expected_total_value


class TestFluxoSoftDeleteMembro:
    """Testa o fluxo de soft delete de membro e preservação de histórico."""

    def test_fluxo_remover_membro_preserva_historico(  # noqa: PLR0914, PLR6301
        self, client, session
    ):
        """
        Testa o fluxo:
        1. Criar república com membros
        2. Criar despesa e registrar pagamento
        3. Remover membro (soft delete)
        4. Verificar que histórico de pagamento foi preservado
        5. Verificar que membro não aparece na listagem ativa
        6. Verificar que quarto ficou disponível
        7. Adicionar novo membro no mesmo quarto
        """
        # Setup inicial
        user = User(
            fullname='Test User',
            email='test@example.com',
            password=get_password_hash('Senha@123'),
            telephone='11999999999',
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        # Login
        login_data = {'username': 'test@example.com', 'password': 'Senha@123'}
        response = client.post('/auth/login', data=login_data)
        token = response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        # 1. Criar república
        republica_data = {
            'nome': 'República Teste',
            'cep': '12345678',
            'rua': 'Rua Teste',
            'numero': '123',
            'bairro': 'Centro',
            'cidade': 'São Paulo',
            'estado': 'SP',
        }
        response = client.post(
            '/republicas', json=republica_data, headers=headers
        )
        republica_id = response.json()['id']

        # 2. Criar quarto
        quarto_data = {'numero': 101}
        response = client.post(
            f'/quartos/?republica_id={republica_id}',
            json=quarto_data,
            headers=headers,
        )
        quarto_id = response.json()['id']

        # Criar membro
        membro_data = {
            'fullname': 'Membro Teste',
            'email': 'membro@example.com',
            'telephone': '11988888888',
            'quarto_id': quarto_id,
        }
        response = client.post(
            f'/membros/{republica_id}', json=membro_data, headers=headers
        )
        membro_id = response.json()['id']

        # 2. Criar despesa
        expected_despesa_value = 100.0
        despesa_data = {
            'descricao': 'Conta de Água',
            'valor_total': expected_despesa_value,
            'data_vencimento': '2024-01-31',
            'categoria': 'agua',
        }
        response = client.post(
            f'/despesas/{republica_id}', json=despesa_data, headers=headers
        )
        despesa_id = response.json()['id']

        # Registrar pagamento
        pagamento_data = {'membro_id': membro_id}
        response = client.post(
            f'/despesas/{republica_id}/{despesa_id}/pagamento',
            json=pagamento_data,
            headers=headers,
        )
        assert response.status_code == HTTPStatus.CREATED
        pagamento_id = response.json()['id']

        # 3. Remover membro (soft delete)
        response = client.patch(
            f'/membros/{republica_id}/{membro_id}', headers=headers
        )
        assert response.status_code == HTTPStatus.OK

        # 4. Verificar que histórico foi preservado no banco
        db_pagamento = session.get(Pagamento, pagamento_id)
        assert db_pagamento is not None
        assert db_pagamento.membro_id == membro_id
        assert db_pagamento.valor_pago == expected_despesa_value

        db_membro = session.get(Membro, membro_id)
        assert db_membro is not None
        assert db_membro.ativo is False
        assert db_membro.data_saida is not None

        # 5. Verificar que membro não aparece na listagem ativa
        response = client.get(f'/membros/{republica_id}', headers=headers)
        membros_ativos = response.json()['members']
        assert len(membros_ativos) == 0

        # Verificar que aparece quando incluir inativos
        response = client.get(
            f'/membros/{republica_id}?incluir_inativos=true', headers=headers
        )
        todos_membros = response.json()['members']
        assert len(todos_membros) == 1
        assert todos_membros[0]['ativo'] is False

        # 6. Verificar que quarto ficou disponível
        response = client.get(
            f'/quartos/{quarto_id}?republica_id={republica_id}',
            headers=headers,
        )
        quarto = response.json()
        assert len(quarto['membros']) == 0

        # 7. Adicionar novo membro no mesmo quarto
        novo_membro_data = {
            'fullname': 'Novo Membro',
            'email': 'novo@example.com',
            'telephone': '11977777777',
            'quarto_id': quarto_id,
        }
        response = client.post(
            f'/membros/{republica_id}', json=novo_membro_data, headers=headers
        )
        assert response.status_code == HTTPStatus.CREATED
        assert response.json()['quarto_id'] == quarto_id


class TestFluxoTransferenciaMembro:
    """Testa o fluxo de transferência de membro entre quartos."""

    def test_fluxo_transferir_membro_entre_quartos(  # noqa: PLR6301
        self, client, session
    ):
        """
        Testa o fluxo:
        1. Criar república com 2 quartos
        2. Criar membro no quarto 1
        3. Transferir membro para quarto 2
        4. Verificar que quarto 1 ficou vazio
        5. Verificar que quarto 2 está ocupado
        6. Tentar adicionar outro membro no quarto 2 (deve falhar)
        """
        # Setup
        user = User(
            fullname='Test User',
            email='test@example.com',
            password=get_password_hash('Senha@123'),
            telephone='11999999999',
        )
        session.add(user)
        session.commit()

        login_data = {'username': 'test@example.com', 'password': 'Senha@123'}
        response = client.post('/auth/login', data=login_data)
        token = response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        # Criar república
        republica_data = {
            'nome': 'República Teste',
            'cep': '12345678',
            'rua': 'Rua Teste',
            'numero': '123',
            'bairro': 'Centro',
            'cidade': 'São Paulo',
            'estado': 'SP',
        }
        response = client.post(
            '/republicas', json=republica_data, headers=headers
        )
        republica_id = response.json()['id']

        # 1. Criar 2 quartos
        response = client.post(
            f'/quartos/?republica_id={republica_id}',
            json={'numero': 101},
            headers=headers,
        )
        quarto1_id = response.json()['id']

        response = client.post(
            f'/quartos/?republica_id={republica_id}',
            json={'numero': 102},
            headers=headers,
        )
        quarto2_id = response.json()['id']

        # 2. Criar membro no quarto 1
        membro_data = {
            'fullname': 'Membro Teste',
            'email': 'membro@example.com',
            'telephone': '11988888888',
            'quarto_id': quarto1_id,
        }
        response = client.post(
            f'/membros/{republica_id}', json=membro_data, headers=headers
        )
        membro_id = response.json()['id']

        # 3. Transferir membro para quarto 2
        update_data = {
            'fullname': 'Membro Teste',
            'email': 'membro@example.com',
            'telephone': '11988888888',
            'quarto_id': quarto2_id,
        }
        response = client.put(
            f'/membros/{republica_id}/{membro_id}',
            json=update_data,
            headers=headers,
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json()['quarto_id'] == quarto2_id

        # 4. Verificar que quarto 1 ficou vazio
        response = client.get(
            f'/quartos/{quarto1_id}?republica_id={republica_id}',
            headers=headers,
        )
        quarto1 = response.json()
        assert len(quarto1['membros']) == 0

        # 5. Verificar que quarto 2 está ocupado
        response = client.get(
            f'/quartos/{quarto2_id}?republica_id={republica_id}',
            headers=headers,
        )
        quarto2 = response.json()
        assert len(quarto2['membros']) == 1
        assert quarto2['membros'][0]['id'] == membro_id

        # 6. Tentar adicionar outro membro no quarto 2 (deve falhar)
        outro_membro_data = {
            'fullname': 'Outro Membro',
            'email': 'outro@example.com',
            'telephone': '11977777777',
            'quarto_id': quarto2_id,
        }
        response = client.post(
            f'/membros/{republica_id}', json=outro_membro_data, headers=headers
        )
        assert response.status_code == HTTPStatus.CONFLICT
        assert 'já está ocupado' in response.json()['detail']


class TestFluxoMultiplasRepublicas:
    """Testa isolamento entre múltiplas repúblicas."""

    def test_isolamento_entre_republicas(  # noqa: PLR0914, PLR6301
        self, client, session
    ):
        """
        Testa o fluxo:
        1. Criar 2 usuários
        2. Cada usuário cria sua república
        3. Criar membros e quartos em cada república
        4. Verificar que um usuário não acessa recursos de outra república
        5. Verificar que membros e quartos são isolados
        """
        # 1. Criar usuário 1
        user1_data = {
            'fullname': 'Usuario Silva Oliveira',
            'email': 'user1_multiplas@example.com',
            'password': 'Senha@123',
            'telephone': '11991111111',
        }
        response = client.post('/users', json=user1_data)
        assert response.status_code == HTTPStatus.CREATED

        # Login usuário 1
        login1 = {
            'username': 'user1_multiplas@example.com',
            'password': 'Senha@123',
        }
        response = client.post('/auth/login', data=login1)
        token1 = response.json()['access_token']
        headers1 = {'Authorization': f'Bearer {token1}'}

        # 2. Criar república do usuário 1
        rep1_data = {
            'nome': 'República 1',
            'cep': '12345678',
            'rua': 'Rua 1',
            'numero': '100',
            'bairro': 'Bairro 1',
            'cidade': 'Cidade 1',
            'estado': 'SP',
        }
        response = client.post('/republicas', json=rep1_data, headers=headers1)
        rep1_id = response.json()['id']

        # Criar usuário 2
        user2_data = {
            'fullname': 'Usuario Santos Pereira',
            'email': 'user2_multiplas@example.com',
            'password': 'Senha@123',
            'telephone': '11992222222',
        }
        response = client.post('/users', json=user2_data)
        assert response.status_code == HTTPStatus.CREATED

        # Login usuário 2
        login2 = {
            'username': 'user2_multiplas@example.com',
            'password': 'Senha@123',
        }
        response = client.post('/auth/login', data=login2)
        token2 = response.json()['access_token']
        headers2 = {'Authorization': f'Bearer {token2}'}

        # Criar república do usuário 2
        rep2_data = {
            'nome': 'República 2',
            'cep': '87654321',
            'rua': 'Rua 2',
            'numero': '200',
            'bairro': 'Bairro 2',
            'cidade': 'Cidade 2',
            'estado': 'RJ',
        }
        response = client.post('/republicas', json=rep2_data, headers=headers2)
        rep2_id = response.json()['id']

        # 3. Criar recursos em cada república
        # Quarto na república 1
        response = client.post(
            f'/quartos/?republica_id={rep1_id}',
            json={'numero': 101},
            headers=headers1,
        )
        quarto1_id = response.json()['id']

        # Membro na república 1
        membro1_data = {
            'fullname': 'Membro Rep 1',
            'email': 'membro1@example.com',
            'telephone': '11977777777',
        }
        response = client.post(
            f'/membros/{rep1_id}', json=membro1_data, headers=headers1
        )
        membro1_id = response.json()['id']

        # Quarto na república 2
        response = client.post(
            f'/quartos/?republica_id={rep2_id}',
            json={'numero': 201},
            headers=headers2,
        )
        quarto2_id = response.json()['id']

        # 4. Verificar isolamento - usuário 2 não deve acessar república 1
        # TODO: O endpoint GET /republicas/{republica_id} não verifica
        # permissões. Este é um problema de segurança que deve ser corrigido
        # response = client.get(f'/republicas/{rep1_id}', headers=headers2)
        # assert response.status_code == HTTPStatus.NOT_FOUND

        response = client.get(
            f'/quartos/?republica_id={rep1_id}', headers=headers2
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED

        response = client.get(f'/membros/{rep1_id}', headers=headers2)
        assert response.status_code == HTTPStatus.UNAUTHORIZED

        # 5. Verificar que cada república só vê seus próprios recursos
        # República 1
        response = client.get(
            f'/quartos/?republica_id={rep1_id}', headers=headers1
        )
        quartos_rep1 = response.json()['quartos']
        assert len(quartos_rep1) == 1
        assert quartos_rep1[0]['id'] == quarto1_id

        response = client.get(f'/membros/{rep1_id}', headers=headers1)
        membros_rep1 = response.json()['members']
        assert len(membros_rep1) == 1
        assert membros_rep1[0]['id'] == membro1_id

        # República 2
        response = client.get(
            f'/quartos/?republica_id={rep2_id}', headers=headers2
        )
        quartos_rep2 = response.json()['quartos']
        assert len(quartos_rep2) == 1
        assert quartos_rep2[0]['id'] == quarto2_id

        response = client.get(f'/membros/{rep2_id}', headers=headers2)
        membros_rep2 = response.json()['members']
        assert len(membros_rep2) == 0  # Nenhum membro criado


class TestFluxoDesocuparQuarto:
    """Testa o fluxo de desocupar quarto."""

    def test_fluxo_desocupar_e_deletar_quarto(  # noqa: PLR6301
        self, client, session
    ):
        """
        Testa o fluxo:
        1. Criar república com quarto e membro
        2. Alocar membro no quarto
        3. Tentar deletar quarto ocupado (deve falhar)
        4. Desocupar quarto
        5. Deletar quarto com sucesso
        """
        # Setup
        user = User(
            fullname='Test User',
            email='test@example.com',
            password=get_password_hash('Senha@123'),
            telephone='11999999999',
        )
        session.add(user)
        session.commit()

        login_data = {'username': 'test@example.com', 'password': 'Senha@123'}
        response = client.post('/auth/login', data=login_data)
        token = response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        # Criar república
        republica_data = {
            'nome': 'República Teste',
            'cep': '12345678',
            'rua': 'Rua Teste',
            'numero': '123',
            'bairro': 'Centro',
            'cidade': 'São Paulo',
            'estado': 'SP',
        }
        response = client.post(
            '/republicas', json=republica_data, headers=headers
        )
        republica_id = response.json()['id']

        # 1. Criar quarto
        response = client.post(
            f'/quartos/?republica_id={republica_id}',
            json={'numero': 101},
            headers=headers,
        )
        quarto_id = response.json()['id']

        # Criar membro
        membro_data = {
            'fullname': 'Membro Teste',
            'email': 'membro@example.com',
            'telephone': '11988888888',
        }
        response = client.post(
            f'/membros/{republica_id}', json=membro_data, headers=headers
        )
        membro_id = response.json()['id']

        # 2. Alocar membro no quarto
        response = client.patch(
            f'/quartos/{quarto_id}/membros',
            json={'membro_id': membro_id},
            headers=headers,
        )
        assert response.status_code == HTTPStatus.OK

        # 3. Tentar deletar quarto ocupado
        response = client.delete(
            f'/quartos/{quarto_id}?republica_id={republica_id}',
            headers=headers,
        )
        assert response.status_code == HTTPStatus.CONFLICT
        assert 'ocupado' in response.json()['detail'].lower()

        # 4. Desocupar quarto
        response = client.patch(
            f'/quartos/{quarto_id}/desocupar',
            json={'membro_id': membro_id},
            headers=headers,
        )
        assert response.status_code == HTTPStatus.OK

        # Verificar que membro não tem mais quarto
        response = client.get(
            f'/membros/{republica_id}/{membro_id}', headers=headers
        )
        assert response.json()['quarto_id'] is None

        # 5. Deletar quarto com sucesso
        response = client.delete(
            f'/quartos/{quarto_id}?republica_id={republica_id}',
            headers=headers,
        )
        assert response.status_code == HTTPStatus.OK

        # Verificar que o quarto foi deletado
        response = client.get(
            f'/quartos/{quarto_id}?republica_id={republica_id}',
            headers=headers,
        )

        # Verificar que quarto foi deletado
        response = client.get(
            f'/quartos/{quarto_id}?republica_id={republica_id}',
            headers=headers,
        )
        assert response.status_code == HTTPStatus.NOT_FOUND
