from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, registry, relationship

table_registry = registry()


class TipoDespesa(str, enum.Enum):
    LUZ = 'luz'
    AGUA = 'agua'
    INTERNET = 'internet'
    GAS = 'gas'
    CONDOMINIO = 'condominio'
    LIMPEZA = 'limpeza'
    MANUTENCAO = 'manutencao'
    OUTROS = 'outros'


class StatusDespesa(str, enum.Enum):
    VENCIDA = 'vencida'
    PENDENTE = 'pendente'
    PAGO = 'pago'


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
    despesas: Mapped[list['Despesa']] = relationship(
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
    # allow membro to have no quarto (desocupado)
    quarto_id: Mapped[int | None] = mapped_column(
        ForeignKey('quartos.id'), nullable=True, default=None
    )

    republica: Mapped[Republica] = relationship(
        init=False, back_populates='membros'
    )
    quarto: Mapped[Quarto] = relationship(init=False, back_populates='membros')
    pagamentos: Mapped[list['Pagamento']] = relationship(
        init=False,
        back_populates='membro',
        cascade='all, delete-orphan',
        lazy='selectin',
    )


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


@table_registry.mapped_as_dataclass
class Despesa:
    __tablename__ = 'despesas'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    descricao: Mapped[str]
    valor_total: Mapped[float]
    data_vencimento: Mapped[date]
    categoria: Mapped[TipoDespesa]
    republica_id: Mapped[int] = mapped_column(ForeignKey('republicas.id'))
    status: Mapped[StatusDespesa] = mapped_column(
        default=StatusDespesa.PENDENTE
    )
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now(), onupdate=func.now()
    )

    republica: Mapped[Republica] = relationship(
        init=False, back_populates='despesas'
    )
    pagamentos: Mapped[list['Pagamento']] = relationship(
        init=False,
        back_populates='despesa',
        cascade='all, delete-orphan',
        lazy='selectin',
    )


@table_registry.mapped_as_dataclass
class Pagamento:
    __tablename__ = 'pagamentos'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    valor_pago: Mapped[float]
    data_pagamento: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    membro_id: Mapped[int] = mapped_column(ForeignKey('membros.id'))
    despesa_id: Mapped[int] = mapped_column(ForeignKey('despesas.id'))

    membro: Mapped[Membro] = relationship(
        init=False, back_populates='pagamentos'
    )
    despesa: Mapped[Despesa] = relationship(
        init=False, back_populates='pagamentos'
    )
