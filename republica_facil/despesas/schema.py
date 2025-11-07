from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from republica_facil.model.models import StatusDespesa, TipoDespesa


class DespesaSchema(BaseModel):
    descricao: str
    valor_total: float
    data_vencimento: date
    categoria: TipoDespesa


class DespesaPublic(DespesaSchema):
    id: int
    status: StatusDespesa
    model_config = ConfigDict(from_attributes=True)


class DespesaList(BaseModel):
    despesas: list[DespesaPublic]


class PagamentoSchema(BaseModel):
    membro_id: int
    # valor_pago será calculado automaticamente (valor_total / num_membros)


class PagamentoPublic(BaseModel):
    id: int
    membro_id: int
    despesa_id: int
    valor_pago: float
    data_pagamento: datetime
    model_config = ConfigDict(from_attributes=True)


class PagamentoList(BaseModel):
    pagamentos: list[PagamentoPublic]
