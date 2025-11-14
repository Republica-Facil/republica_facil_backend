# 🏠 República Fácil - Backend

API REST para gerenciamento de repúblicas estudantis.

## 🛠️ Stack

- Python 3.13 + FastAPI
- PostgreSQL 16 + SQLAlchemy
- Redis 7
- Docker

## 📦 Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) e [Docker Compose](https://docs.docker.com/compose/install/)
- [Python 3.13+](https://www.python.org/downloads/) (apenas para desenvolvimento local)
- [Poetry](https://python-poetry.org/docs/#installation) (apenas para desenvolvimento local)

### Instalando Poetry

```bash
# Linux, macOS, Windows (WSL)
curl -sSL https://install.python-poetry.org | python3 -

# Ou com pipx (recomendado)
pipx install poetry
```

## 🚀 Como Rodar

### Com Docker (Recomendado)

```bash
# 1. Clone o repositório
git clone https://github.com/Republica-Facil/republica_facil_backend.git
cd republica_facil_backend

# 2. Configure o .env (copie do exemplo)
cp .env.example .env
# Edite o .env com suas credenciais reais

# 3. Suba os containers
docker compose up --build -d

# 4. Execute as migrations
docker compose exec backend alembic upgrade head

```

## 🧪 Testes

```bash

poetry run task test
```

## 📚 Documentação

- **Swagger:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
