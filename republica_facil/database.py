import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from republica_facil.settings import Settings

engine = create_engine(Settings().DATABASE_URL)


def get_session():  # pragma: no cover
    with Session(engine) as session:
        yield session


try:
    redis_client = redis.Redis(
        host=Settings().REDIS_HOST,  # ex: "localhost" ou "redis_container"
        port=Settings().REDIS_PORT,  # ex: 6379
        db=0,
        decode_responses=True,
    )
    redis_client.ping()
    print('Conectado ao Redis com sucesso!')
except redis.exceptions.ConnectionError as e:
    print(f'Erro ao conectar ao Redis: {e}')
    redis_client = None
