from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from republica_facil.database import get_session
from republica_facil.model.models import (
    Despesa,
    Membro,
    Pagamento,
    Republica,
    StatusDespesa,
    User,
)
from republica_facil.security import get_current_user
from republica_facil.usuarios.schema import Message

from .schema import (
    DespesaList,
    DespesaPublic,
    DespesaSchema,
    PagamentoList,
    PagamentoPublic,
    PagamentoSchema,
)

router = APIRouter(prefix='/despesas', tags=['despesas'])

T_Session = Annotated[Session, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post(
    '/{republica_id}',
    status_code=HTTPStatus.CREATED,
    response_class=JSONResponse,
    response_model=DespesaPublic,
)
def create_despesa(
    despesa: DespesaSchema,
    republica_id: int,
    session: T_Session,
    user: CurrentUser,
):
    db_republica = session.scalar(
        select(Republica).where(Republica.id == republica_id)
    )

    if not db_republica:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='República não encontrada'
        )

    if db_republica.user_id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail='Permissões negadas'
        )

    new_despesa = Despesa(
        descricao=despesa.descricao,
        valor_total=despesa.valor_total,
        data_vencimento=despesa.data_vencimento,
        categoria=despesa.categoria,
        republica_id=republica_id,
    )

    session.add(new_despesa)
    session.commit()
    session.refresh(new_despesa)

    return new_despesa


@router.get(
    '/{republica_id}',
    status_code=HTTPStatus.OK,
    response_class=JSONResponse,
    response_model=DespesaList,
)
def read_despesas(republica_id: int, session: T_Session, user: CurrentUser):
    db_republica = session.scalar(
        select(Republica).where(Republica.id == republica_id)
    )

    if not db_republica:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='República não encontrada'
        )

    if db_republica.user_id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail='Permissões negadas'
        )

    despesas = session.scalars(
        select(Despesa).where(Despesa.republica_id == republica_id)
    ).all()

    return {'despesas': despesas}


@router.get(
    '/{republica_id}/{despesa_id}',
    status_code=HTTPStatus.OK,
    response_class=JSONResponse,
    response_model=DespesaPublic,
)
def read_despesa(
    republica_id: int, despesa_id: int, session: T_Session, user: CurrentUser
):
    db_republica = session.scalar(
        select(Republica).where(Republica.id == republica_id)
    )

    if not db_republica:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='República não encontrada'
        )

    if db_republica.user_id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail='Permissões negadas'
        )

    db_despesa = session.scalar(
        select(Despesa).where(
            Despesa.id == despesa_id, Despesa.republica_id == republica_id
        )
    )

    if not db_despesa:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Despesa não encontrada'
        )

    return db_despesa


@router.patch(
    '/{republica_id}/{despesa_id}',
    status_code=HTTPStatus.OK,
    response_class=JSONResponse,
    response_model=DespesaPublic,
)
def update_despesa(
    republica_id: int,
    despesa_id: int,
    despesa: DespesaSchema,
    session: T_Session,
    user: CurrentUser,
):
    db_republica = session.scalar(
        select(Republica).where(Republica.id == republica_id)
    )

    if not db_republica:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='República não encontrada'
        )

    if db_republica.user_id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail='Permissões negadas'
        )

    db_despesa = session.scalar(
        select(Despesa).where(
            Despesa.id == despesa_id, Despesa.republica_id == republica_id
        )
    )

    if not db_despesa:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Despesa não encontrada'
        )

    db_despesa.descricao = despesa.descricao
    db_despesa.valor_total = despesa.valor_total
    db_despesa.data_vencimento = despesa.data_vencimento
    db_despesa.categoria = despesa.categoria

    session.commit()
    session.refresh(db_despesa)

    return db_despesa


@router.delete(
    '/{republica_id}/{despesa_id}',
    status_code=HTTPStatus.OK,
    response_class=JSONResponse,
    response_model=Message,
)
def delete_despesa(
    republica_id: int, despesa_id: int, session: T_Session, user: CurrentUser
):
    db_republica = session.scalar(
        select(Republica).where(Republica.id == republica_id)
    )

    if not db_republica:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='República não encontrada'
        )

    if db_republica.user_id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail='Permissões negadas'
        )

    db_despesa = session.scalar(
        select(Despesa).where(
            Despesa.id == despesa_id, Despesa.republica_id == republica_id
        )
    )

    if not db_despesa:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Despesa não encontrada'
        )

    session.delete(db_despesa)
    session.commit()

    return {'message': 'Despesa excluída com sucesso'}


@router.post(
    '/{republica_id}/{despesa_id}/pagamento',
    status_code=HTTPStatus.CREATED,
    response_class=JSONResponse,
    response_model=PagamentoPublic,
)
def registrar_pagamento(
    republica_id: int,
    despesa_id: int,
    pagamento: PagamentoSchema,
    session: T_Session,
    user: CurrentUser,
):
    db_republica = session.scalar(
        select(Republica).where(Republica.id == republica_id)
    )

    if not db_republica:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='República não encontrada'
        )

    if db_republica.user_id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail='Permissões negadas'
        )

    db_despesa = session.scalar(
        select(Despesa).where(
            Despesa.id == despesa_id, Despesa.republica_id == republica_id
        )
    )

    if not db_despesa:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Despesa não encontrada'
        )

    if db_despesa.status == StatusDespesa.PAGO:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Despesa já está marcada como paga',
        )

    db_membro = session.scalar(
        select(Membro).where(Membro.id == pagamento.membro_id)
    )

    if not db_membro:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Membro não encontrado'
        )

    if db_membro.republica_id != republica_id:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Membro não pertence a esta república',
        )

    pagamento_existente = session.scalar(
        select(Pagamento).where(
            Pagamento.membro_id == pagamento.membro_id,
            Pagamento.despesa_id == despesa_id,
        )
    )

    if pagamento_existente:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail=f'{db_membro.fullname} já pagou esta despesa',
        )

    num_membros = session.scalar(
        select(func.count(Membro.id)).where(
            Membro.republica_id == republica_id
        )
    )

    if num_membros == 0:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='República não tem membros cadastrados',
        )

    valor_por_membro = db_despesa.valor_total / num_membros

    novo_pagamento = Pagamento(
        membro_id=pagamento.membro_id,
        despesa_id=despesa_id,
        valor_pago=valor_por_membro,
    )

    session.add(novo_pagamento)
    session.commit()
    session.refresh(novo_pagamento)

    # Verificar quantos membros já pagaram
    num_pagamentos = session.scalar(
        select(func.count(Pagamento.id)).where(
            Pagamento.despesa_id == despesa_id
        )
    )

    # Se todos os membros pagaram, marcar despesa como PAGA
    if num_pagamentos >= num_membros:
        db_despesa.status = StatusDespesa.PAGO

    session.commit()
    session.refresh(novo_pagamento)

    return novo_pagamento


@router.get(
    '/{republica_id}/{despesa_id}/pagamentos',
    status_code=HTTPStatus.OK,
    response_class=JSONResponse,
    response_model=PagamentoList,
)
def listar_pagamentos_despesa(
    republica_id: int, despesa_id: int, session: T_Session, user: CurrentUser
):
    db_republica = session.scalar(
        select(Republica).where(Republica.id == republica_id)
    )

    if not db_republica:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='República não encontrada'
        )

    if db_republica.user_id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail='Permissões negadas'
        )

    db_despesa = session.scalar(
        select(Despesa).where(
            Despesa.id == despesa_id, Despesa.republica_id == republica_id
        )
    )

    if not db_despesa:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Despesa não encontrada'
        )

    pagamentos = session.scalars(
        select(Pagamento).where(Pagamento.despesa_id == despesa_id)
    ).all()

    return {'pagamentos': pagamentos}
