from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, registry, relationship

table_registry = registry()


class RoleEnum(Enum):
    ADMIN = 'ADMIN'
    MEMBER = 'MEMBER'


@table_registry.mapped_as_dataclass
class User:
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    fullname: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    telephone: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now(), onupdate=func.now()
    )
    republicas: Mapped[list[Republica]] = relationship(
        init=False, cascade='all, delete-orphan', lazy='selectin'
    )


@table_registry.mapped_as_dataclass
class Republica:
    __tablename__ = 'republicas'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    name: Mapped[str]
    address: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now(), onupdate=func.now()
    )
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    membros: Mapped[list[Membro]] = relationship(
        init=False, cascade='all, delete-orphan', lazy='selectin'
    )


@table_registry.mapped_as_dataclass
class Membro:
    __tablename__ = 'membros'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    fullname: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    telephone: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now(), onupdate=func.now()
    )
    republica_id: Mapped[int] = mapped_column(ForeignKey('republicas.id'))

    # QUARTO -> REPUBLICA_ID
    # REPUBLICA 1 OU + QUARTOS -> RELAÇÃO DE QUARTOS
    # MEMBRO ->

    # NOVA TABELA -> TERNARIO NOVA TABELA
