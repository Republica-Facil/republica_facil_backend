import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from republica_facil.settings import Settings

engine = create_engine(Settings().DATABASE_URL)  # pragma: no cover


def get_session():  # pragma: no cover
    with Session(engine) as session:  # pragma: no cover
        yield session  # pragma: no cover


try:  # pragma: no cover
    redis_client = redis.Redis(  # pragma: no cover
        host=Settings().REDIS_HOST,  # pragma: no cover
        port=Settings().REDIS_PORT,  # pragma: no cover
        db=0,  # pragma: no cover
        decode_responses=True,  # pragma: no cover
    )
    redis_client.ping()  # pragma: no cover
    print('Conectado ao Redis com sucesso!')  # pragma: no cover
except redis.exceptions.ConnectionError as e:  # pragma: no cover
    print(f'Erro ao conectar ao Redis: {e}')  # pragma: no cover
    redis_client = None  # pragma: no cover
