# República Fácil - Backend

API REST para gerenciamento de repúblicas estudantis.

## Tecnologias

- Python 3.13
- FastAPI
- PostgreSQL
- SQLAlchemy 2.0
- Alembic (migrations)
- Redis (reset de senha)
- Poetry (gerenciador de dependências)
- Pytest (testes)
- Docker / Docker Compose

## Pré-requisitos

- Docker
- Docker Compose
- Poetry (opcional, para desenvolvimento local)

## Instalação e Execução

### 1. Clonar o repositório

```bash
git clone https://github.com/Republica-Facil/republica_facil_backend.git
cd republica_facil_backend
```

### 2. Configurar variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
DATABASE_URL=your-database
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REDIS_HOST=redis
REDIS_PORT=6379
```

### 3. Executar com Docker Compose

```bash
docker-compose up -d
```

A API estará disponível em `http://localhost:8000`

### 4. Aplicar migrations

```bash
docker-compose exec app alembic upgrade head
```

## Desenvolvimento Local

### 1. Instalar dependências

```bash
poetry install
```

### 2. Ativar ambiente virtual

```bash
poetry shell
```

### 3. Executar migrations

```bash
alembic upgrade head
```

### 4. Executar servidor de desenvolvimento

```bash
uvicorn republica_facil.main:app --reload
```

## Testes

### Executar todos os testes

```bash
poetry run pytest
```

### Executar testes com cobertura

```bash
poetry run pytest --cov=republica_facil
```

### Executar testes de um módulo específico

```bash
poetry run pytest republica_facil/usuarios/test_users.py -v
```

## Estrutura do Projeto

```
republica_facil_backend/
├── republica_facil/
│   ├── __init__.py
│   ├── main.py                 # Aplicação FastAPI
│   ├── database.py             # Configuração do banco
│   ├── security.py             # Autenticação e segurança
│   ├── settings.py             # Configurações do projeto
│   ├── conftest.py             # Fixtures para testes
│   │
│   ├── model/
│   │   └── models.py           # Modelos SQLAlchemy
│   │
│   ├── autenticacao/
│   │   ├── router.py           # Rotas de autenticação
│   │   ├── schema.py           # Schemas Pydantic
│   │   ├── service.py          # Lógica de negócio
│   │   ├── repository.py       # Acesso a dados
│   │   └── test_autenticacao.py
│   │
│   ├── usuarios/
│   │   ├── router.py           # CRUD de usuários
│   │   ├── schema.py
│   │   ├── repository.py
│   │   └── test_users.py
│   │
│   ├── republicas/
│   │   ├── router.py           # CRUD de repúblicas
│   │   ├── schema.py
│   │   ├── repository.py
│   │   └── test_republicas.py
│   │
│   ├── membros/
│   │   ├── router.py           # CRUD de membros
│   │   ├── schema.py
│   │   └── test_membros.py
│   │
│   ├── quartos/
│   │   ├── router.py           # CRUD de quartos
│   │   ├── schema.py
│   │   └── test_quartos.py
│   │
│   └── despesas/
│       ├── router.py           # CRUD de despesas e pagamentos
│       ├── schema.py
│       └── test_despesas.py
│
├── migrations/                  # Migrations Alembic
│   ├── env.py
│   └── versions/
│
├── docker-compose.yaml
├── Dockerfile
├── entrypoint.sh
├── pyproject.toml
└── alembic.ini
```

## Endpoints Principais

### Autenticação
- `POST /auth/login` - Login
- `POST /auth/forgot-password` - Solicitar código de reset
- `POST /auth/verify-code` - Verificar código
- `POST /auth/reset-password` - Resetar senha
- `POST /auth/logout` - Logout

### Usuários
- `POST /usuarios` - Criar usuário
- `GET /usuarios` - Listar usuários
- `GET /usuarios/{user_id}` - Obter usuário
- `PUT /usuarios/{user_id}` - Atualizar usuário
- `DELETE /usuarios/{user_id}` - Deletar usuário
- `PUT /usuarios/{user_id}/password` - Atualizar senha

### Repúblicas
- `POST /republicas` - Criar república
- `GET /republicas` - Listar repúblicas do usuário
- `GET /republicas/{republica_id}` - Obter república

### Membros
- `POST /membros/{republica_id}` - Criar membro
- `GET /membros/{republica_id}` - Listar membros (ativos por padrão)
- `GET /membros/{republica_id}?incluir_inativos=true` - Incluir inativos
- `GET /membros/{republica_id}/{member_id}` - Obter membro
- `PUT /membros/{republica_id}/{member_id}` - Atualizar membro
- `DELETE /membros/{republica_id}/{member_id}` - Remover membro (soft delete)

### Quartos
- `POST /quartos/{republica_id}` - Criar quarto
- `GET /quartos/{republica_id}` - Listar quartos
- `GET /quartos/{republica_id}/{quarto_id}` - Obter quarto
- `PUT /quartos/{republica_id}/{quarto_id}` - Atualizar quarto
- `DELETE /quartos/{republica_id}/{quarto_id}` - Deletar quarto
- `PUT /quartos/{republica_id}/{quarto_id}/adicionar-membro` - Adicionar membro
- `PUT /quartos/{republica_id}/{quarto_id}/remover-membro` - Remover membro
- `PUT /quartos/{republica_id}/{quarto_id}/desocupar` - Desocupar quarto

### Despesas
- `POST /despesas/{republica_id}` - Criar despesa
- `GET /despesas/{republica_id}` - Listar despesas
- `GET /despesas/{republica_id}/{despesa_id}` - Obter despesa
- `PUT /despesas/{republica_id}/{despesa_id}` - Atualizar despesa
- `DELETE /despesas/{republica_id}/{despesa_id}` - Deletar despesa
- `POST /despesas/{republica_id}/{despesa_id}/pagamentos` - Registrar pagamento
- `GET /despesas/{republica_id}/{despesa_id}/pagamentos` - Listar pagamentos

## Documentação da API

Acesse a documentação interativa (Swagger UI):
- `http://localhost:8000/docs`

Documentação alternativa (ReDoc):
- `http://localhost:8000/redoc`

## Migrations

### Criar nova migration

```bash
alembic revision -m "descricao_da_migration"
```

### Aplicar migrations

```bash
alembic upgrade head
```

### Reverter última migration

```bash
alembic downgrade -1
```

### Rodar Projeto com Docker
```bash
docker compose up --build
```


## Funcionalidades Implementadas

- Autenticação JWT
- Reset de senha via código (email)
- CRUD completo de usuários, repúblicas, membros, quartos e despesas
- Soft delete de membros (preserva histórico financeiro)
- Controle de ocupação de quartos
- Divisão automática de despesas entre membros
- Registro de pagamentos individuais
- Validações de negócio (telefone, senha, permissões)
- Cobertura de testes: 174 testes passando