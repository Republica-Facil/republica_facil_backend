from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from republica_facil.database import get_session
from republica_facil.model.models import Membro, Quarto, Republica, User
from republica_facil.security import get_current_user
from republica_facil.usuarios.schema import Message

from .schema import (
    AdicionarMembroQuarto,
    QuartoList,
    QuartoPublic,
    QuartoSchema,
)

router = APIRouter(prefix='/quartos', tags=['quartos'])

T_Session = Annotated[Session, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post(
    '/',
    status_code=HTTPStatus.CREATED,
    response_class=JSONResponse,
    response_model=QuartoPublic,
)
def create_quarto(
    quarto: QuartoSchema,
    session: T_Session,
    user: CurrentUser,
    republica_id: int,
):
    db_republica = session.scalar(
        select(Republica).where(Republica.id == republica_id)
    )

    if db_republica:
        if db_republica.user_id == user.id:
            new_quarto = Quarto(
                numero=quarto.numero, republica_id=republica_id
            )
            session.add(new_quarto)
            session.commit()
            session.refresh(new_quarto)
            return new_quarto
        else:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail='Permissões negadas',
            )
    else:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Republica nao encontrada'
        )


@router.get(
    '/',
    status_code=HTTPStatus.OK,
    response_class=JSONResponse,
    response_model=QuartoList,
)
def read_quartos(session: T_Session, user: CurrentUser, republica_id: int):
    db_republica = session.scalar(
        select(Republica).where(Republica.id == republica_id)
    )

    if db_republica:
        if db_republica.user_id == user.id:
            quartos = session.scalars(
                select(Quarto).where(Quarto.republica_id == republica_id)
            )
            if quartos:
                return {'quartos': quartos}
            else:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail='Quartos nao encontrados',
                )
        else:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail='Permissões negadas',
            )
    else:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Republica nao encontrada'
        )


@router.get(
    '/{quarto_id}',
    status_code=HTTPStatus.OK,
    response_class=JSONResponse,
    response_model=QuartoPublic,
)
def read_quarto(
    session: T_Session, user: CurrentUser, republica_id: int, quarto_id: int
):
    db_republica = session.scalar(
        select(Republica).where(Republica.id == republica_id)
    )

    if db_republica:
        if db_republica.user_id == user.id:
            quarto = session.scalar(
                select(Quarto).where(Quarto.id == quarto_id)
            )
            if quarto:
                return quarto
            else:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail='Quartos nao encontrados',
                )
        else:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail='Permissões negadas',
            )
    else:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Republica nao encontrada'
        )


@router.patch(
    '/{quarto_id}',
    status_code=HTTPStatus.OK,
    response_class=JSONResponse,
    response_model=QuartoPublic,
)
def update_quarto(
    quarto: QuartoSchema,
    session: T_Session,
    user: CurrentUser,
    republica_id: int,
    quarto_id: int,
):
    db_republica = session.scalar(
        select(Republica).where(Republica.id == republica_id)
    )

    if db_republica:
        if db_republica.user_id == user.id:
            db_quarto = session.scalar(
                select(Quarto).where(Quarto.id == quarto_id)
            )
            if db_quarto:
                db_quarto.numero = quarto.numero
                session.commit()
                session.refresh(db_quarto)

                return db_quarto
            else:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail='Quartos nao encontrados',
                )
        else:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail='Permissões negadas',
            )
    else:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Republica nao encontrada'
        )


@router.delete(
    '/{quarto_id}',
    status_code=HTTPStatus.OK,
    response_class=JSONResponse,
    response_model=Message,
)
def delete_quarto(
    session: T_Session, user: CurrentUser, republica_id: int, quarto_id: int
):
    db_republica = session.scalar(
        select(Republica).where(Republica.id == republica_id)
    )

    if db_republica:
        if db_republica.user_id == user.id:
            db_quarto = session.scalar(
                select(Quarto).where(Quarto.id == quarto_id)
            )
            if db_quarto:
                # prevent deleting a room that still has occupants
                ocupante = session.scalar(
                    select(Membro).where(Membro.quarto_id == quarto_id)
                )

                if ocupante:
                    raise HTTPException(
                        status_code=HTTPStatus.CONFLICT,
                        detail=(
                            f'Quarto ocupado por {ocupante.fullname}. '
                            'Desocupe antes de excluir.'
                        ),
                    )

                session.delete(db_quarto)
                session.commit()

                return {'message': 'Quarto excluido'}
            else:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail='Quartos nao encontrados',
                )
        else:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail='Permissões negadas',
            )
    else:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Republica nao encontrada'
        )


@router.patch(
    '/{quarto_id}/membros',
    status_code=HTTPStatus.OK,
    response_class=JSONResponse,
    response_model=Message,
)
def adicionar_membro_ao_quarto(
    quarto_id: int,
    data: AdicionarMembroQuarto,
    session: T_Session,
    user: CurrentUser,
):
    db_quarto = session.scalar(select(Quarto).where(Quarto.id == quarto_id))

    if not db_quarto:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Quarto não encontrado'
        )

    db_republica = session.scalar(
        select(Republica).where(Republica.id == db_quarto.republica_id)
    )

    if db_republica.user_id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail='Permissões negadas'
        )

    db_membro = session.scalar(
        select(Membro).where(Membro.id == data.membro_id)
    )

    if not db_membro:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Membro não encontrado'
        )

    if db_membro.republica_id != db_quarto.republica_id:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Membro não pertence à mesma república do quarto',
        )

    membro_no_quarto = session.scalar(
        select(Membro).where(
            Membro.quarto_id == quarto_id, Membro.id != data.membro_id
        )
    )

    if membro_no_quarto:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail=f'Quarto já está ocupado por {membro_no_quarto.fullname}',
        )

    db_membro.quarto_id = quarto_id
    session.commit()

    return {'message': 'Membro adicionado ao quarto'}


@router.patch(
    '/{quarto_id}/desocupar',
    status_code=HTTPStatus.OK,
    response_class=JSONResponse,
    response_model=Message,
)
def desocupar_membro_do_quarto(
    quarto_id: int,
    data: AdicionarMembroQuarto,
    session: T_Session,
    user: CurrentUser,
):
    """Remove o vínculo do membro com o quarto (coloca quarto_id = NULL).

    Requires that the member currently is in this quarto and belongs to the
    same república. The Membro model/column must be nullable for this to work.
    """
    db_quarto = session.scalar(select(Quarto).where(Quarto.id == quarto_id))

    if not db_quarto:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Quarto não encontrado'
        )

    db_republica = session.scalar(
        select(Republica).where(Republica.id == db_quarto.republica_id)
    )

    if db_republica.user_id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail='Permissões negadas'
        )

    db_membro = session.scalar(
        select(Membro).where(Membro.id == data.membro_id)
    )

    if not db_membro:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Membro não encontrado'
        )

    if db_membro.quarto_id != quarto_id:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Membro não está neste quarto',
        )

    # set to None (desocupar)
    db_membro.quarto_id = None
    session.commit()

    return {'message': 'Membro desocupado do quarto'}


@router.delete(
    '/{quarto_id}/membros/{membro_id}',
    status_code=HTTPStatus.OK,
    response_class=JSONResponse,
    response_model=Message,
)
def remover_membro_do_quarto(  # noqa: PLR0913
    quarto_id: int,
    membro_id: int,
    novo_quarto_id: int,
    session: T_Session,
    user: CurrentUser,
):
    db_quarto = session.scalar(select(Quarto).where(Quarto.id == quarto_id))

    if not db_quarto:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Quarto não encontrado'
        )

    db_republica = session.scalar(
        select(Republica).where(Republica.id == db_quarto.republica_id)
    )

    if db_republica.user_id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail='Permissões negadas'
        )

    db_membro = session.scalar(select(Membro).where(Membro.id == membro_id))

    if not db_membro:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Membro não encontrado'
        )

    if db_membro.quarto_id != quarto_id:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Membro não está neste quarto',
        )

    db_novo_quarto = session.scalar(
        select(Quarto).where(Quarto.id == novo_quarto_id)
    )

    if not db_novo_quarto:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Novo quarto não encontrado',
        )

    if db_novo_quarto.republica_id != db_republica.id:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Novo quarto não pertence à mesma república',
        )

    db_membro.quarto_id = novo_quarto_id
    session.commit()

    return {'message': 'Membro transferido'}
