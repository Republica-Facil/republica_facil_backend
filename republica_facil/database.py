from typing import Optional

import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from republica_facil.settings import Settings

engine = create_engine(Settings().DATABASE_URL)  # pragma: no cover


def get_session():  # pragma: no cover
    with Session(engine) as session:  # pragma: no cover
        yield session  # pragma: no cover


_redis_client: Optional[redis.Redis] = None


def _build_redis_client() -> redis.Redis:
    return redis.from_url(
        Settings().REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=3,
        socket_timeout=3,
        retry_on_timeout=True,
        health_check_interval=30,
    )


def get_redis_client() -> Optional[redis.Redis]:
    """Return a cached Redis client, reconnecting if necessary."""

    global _redis_client

    if _redis_client is not None:
        return _redis_client

    try:
        client = _build_redis_client()
        client.ping()  # pragma: no cover
        print('Conectado ao Redis com sucesso!')  # pragma: no cover
        _redis_client = client
    except redis.exceptions.RedisError as exc:  # pragma: no cover
        print(f'Erro ao conectar ao Redis: {exc}')  # pragma: no cover
        _redis_client = None

    return _redis_client


def reset_redis_client() -> None:
    """Force the next call to get_redis_client to reconnect."""

    global _redis_client
    _redis_client = None


redis_client = get_redis_client()
