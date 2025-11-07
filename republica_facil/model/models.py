from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, registry, relationship

table_registry = registry()


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
        init=False,
        back_populates='user',
        cascade='all, delete-orphan',
        lazy='selectin',
    )


@table_registry.mapped_as_dataclass
class Republica:
    __tablename__ = 'republicas'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    nome: Mapped[str]
    cep: Mapped[str]
    rua: Mapped[str]
    numero: Mapped[str]
    bairro: Mapped[str]
    cidade: Mapped[str]
    estado: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    complemento: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(init=False, back_populates='republicas')
    membros: Mapped[list[Membro]] = relationship(
        init=False,
        back_populates='republica',
        cascade='all, delete-orphan',
        lazy='selectin',
    )
    quartos: Mapped[list[Quarto]] = relationship(
        init=False,
        back_populates='republica',
        cascade='all, delete-orphan',
        lazy='selectin',
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
    quarto_id: Mapped[int] = mapped_column(ForeignKey('quartos.id'))

    republica: Mapped[Republica] = relationship(
        init=False, back_populates='membros'
    )
    quarto: Mapped[Quarto] = relationship(init=False, back_populates='membros')


@table_registry.mapped_as_dataclass
class Quarto:
    __tablename__ = 'quartos'
    __table_args__ = (UniqueConstraint('numero', 'republica_id'),)

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    numero: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now(), onupdate=func.now()
    )
    republica_id: Mapped[int] = mapped_column(ForeignKey('republicas.id'))

    republica: Mapped[Republica] = relationship(
        init=False, back_populates='quartos'
    )
    membros: Mapped[list[Membro]] = relationship(
        init=False,
        back_populates='quarto',
        cascade='all, delete-orphan',
        lazy='selectin',
    )
