from typing import Optional

import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from republica_facil.settings import Settings

engine = create_engine(Settings().DATABASE_URL)  # pragma: no cover


def get_session():  # pragma: no cover
    with Session(engine) as session:  # pragma: no cover
        yield session  # pragma: no cover


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

    cached_client = _redis_client_cache.get()

    if cached_client is not None:
        return cached_client

    try:
        client = _build_redis_client()
        client.ping()  # pragma: no cover
        print('Conectado ao Redis com sucesso!')  # pragma: no cover
    except redis.exceptions.RedisError as exc:  # pragma: no cover
        print(f'Erro ao conectar ao Redis: {exc}')  # pragma: no cover
        _redis_client_cache.set(None)
        return None

    _redis_client_cache.set(client)
    return client


class _RedisClientCache:
    def __init__(self) -> None:
        self._client: Optional[redis.Redis] = None

    def get(self) -> Optional[redis.Redis]:
        return self._client

    def set(self, client: Optional[redis.Redis]) -> None:
        self._client = client


_redis_client_cache = _RedisClientCache()


def reset_redis_client() -> None:
    """Force the next call to get_redis_client to reconnect."""

    _redis_client_cache.set(None)


redis_client = get_redis_client()
