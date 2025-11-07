from datetime import datetime
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

from .schema import ListMember, Member, MemberPublic

router = APIRouter(prefix='/membros', tags=['membros'])

CurrentUser = Annotated[User, Depends(get_current_user)]
T_Session = Annotated[Session, Depends(get_session)]


@router.post(
    '/{republica_id}',
    status_code=HTTPStatus.CREATED,
    response_class=JSONResponse,
    response_model=MemberPublic,
)
def create_member(
    member: Member, session: T_Session, user: CurrentUser, republica_id: int
):
    db_republica = session.scalar(
        select(Republica).where(Republica.id == republica_id)
    )

    if db_republica:
        if db_republica.user_id == user.id:
            # Verificar se já existe membro ativo com o mesmo email
            membro_com_email = session.scalar(
                select(Membro).where(
                    Membro.email == member.email,
                    Membro.ativo == True
                )
            )
            
            if membro_com_email:
                raise HTTPException(
                    status_code=HTTPStatus.CONFLICT,
                    detail='Membro ja existe'
                )
            
            # Verificar se já existe membro ativo com o mesmo telefone
            membro_com_telefone = session.scalar(
                select(Membro).where(
                    Membro.telephone == member.telephone,
                    Membro.ativo == True
                )
            )
            
            if membro_com_telefone:
                raise HTTPException(
                    status_code=HTTPStatus.CONFLICT,
                    detail='Membro ja existe'
                )
            
            # Only validate quarto if one is provided
            if member.quarto_id is not None:
                db_quarto = session.scalar(
                    select(Quarto).where(Quarto.id == member.quarto_id)
                )

                if not db_quarto:
                    raise HTTPException(
                        status_code=HTTPStatus.NOT_FOUND,
                        detail='Quarto não encontrado',
                    )

                if db_quarto.republica_id != republica_id:
                    raise HTTPException(
                        status_code=HTTPStatus.BAD_REQUEST,
                        detail='Quarto não pertence a esta república',
                    )

                # Verificar se o quarto já tem um membro ativo
                membro_existente = session.scalar(
                    select(Membro).where(
                        Membro.quarto_id == member.quarto_id,
                        Membro.ativo == True
                    )
                )

                if membro_existente:
                    raise HTTPException(
                        status_code=HTTPStatus.CONFLICT,
                        detail='Este quarto já está ocupado',
                    )

            new_member = Membro(
                fullname=member.fullname,
                email=member.email,
                telephone=member.telephone,
                republica_id=republica_id,
                quarto_id=member.quarto_id,
            )

            session.add(new_member)
            session.commit()
            session.refresh(new_member)

            return new_member
        else:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail='Permissões negadas',
            )

    raise HTTPException(
        status_code=HTTPStatus.NOT_FOUND, detail='Republica nao encontrada'
    )


@router.get(
    '/{republica_id}',
    status_code=HTTPStatus.OK,
    response_class=JSONResponse,
    response_model=ListMember,
)
def read_members(
    session: T_Session,
    user: CurrentUser,
    republica_id: int,
    limit=10,
    offset=0,
    incluir_inativos: bool = False,
):
    db_republica = session.scalar(
        select(Republica).where(Republica.id == republica_id)
    )

    if db_republica:
        if db_republica.user_id == user.id:
            query = select(Membro).where(Membro.republica_id == republica_id)
            
            # Por padrão, retorna apenas membros ativos
            if not incluir_inativos:
                query = query.where(Membro.ativo == True)
            
            members = session.scalars(
                query.offset(offset).limit(limit)
            )
            return {'members': members}
        else:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail='Permissões negadas',
            )

    raise HTTPException(
        status_code=HTTPStatus.NOT_FOUND, detail='Republica nao encontrada'
    )


@router.get(
    '/{republica_id}/{member_id}',
    status_code=HTTPStatus.OK,
    response_class=JSONResponse,
    response_model=MemberPublic,
)
def read_member(
    session: T_Session, user: CurrentUser, republica_id: int, member_id: int
):
    db_republica = session.scalar(
        select(Republica).where(Republica.id == republica_id)
    )

    if db_republica:
        if db_republica.user_id == user.id:
            member = session.scalar(
                select(Membro).where(
                    Membro.republica_id == republica_id, Membro.id == member_id
                )
            )
            if member:
                return member
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='Membro nao encontrado',
            )
        else:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail='Permissões negadas',
            )

    raise HTTPException(
        status_code=HTTPStatus.NOT_FOUND, detail='Republica nao encontrada'
    )


@router.put(
    '/{republica_id}/{member_id}',
    status_code=HTTPStatus.OK,
    response_class=JSONResponse,
    response_model=MemberPublic,
)
def update_member(  # noqa: PLR1702
    member: Member,
    session: T_Session,
    user: CurrentUser,
    republica_id: int,
    member_id: int,
):
    db_republica = session.scalar(
        select(Republica).where(Republica.id == republica_id)
    )

    if db_republica:  # noqa: PLR1702
        if db_republica.user_id == user.id:
            db_member = session.scalar(
                select(Membro).where(
                    Membro.republica_id == republica_id, Membro.id == member_id
                )
            )
            if db_member:
                # Verificar se está tentando usar email de outro membro ativo
                if member.email != db_member.email:
                    membro_com_email = session.scalar(
                        select(Membro).where(
                            Membro.email == member.email,
                            Membro.ativo == True,
                            Membro.id != member_id
                        )
                    )
                    
                    if membro_com_email:
                        raise HTTPException(
                            status_code=HTTPStatus.CONFLICT,
                            detail='Membro ja existe'
                        )
                
                # Verificar se está tentando usar telefone de outro membro ativo
                if member.telephone != db_member.telephone:
                    membro_com_telefone = session.scalar(
                        select(Membro).where(
                            Membro.telephone == member.telephone,
                            Membro.ativo == True,
                            Membro.id != member_id
                        )
                    )
                    
                    if membro_com_telefone:
                        raise HTTPException(
                            status_code=HTTPStatus.CONFLICT,
                            detail='Membro ja existe'
                        )
                
                # Verifica se está tentando mudar de quarto
                if member.quarto_id != db_member.quarto_id:
                    # Se quarto_id não é None, validar o novo quarto
                    if member.quarto_id is not None:
                        # Verificar se o novo quarto existe
                        db_quarto = session.scalar(
                            select(Quarto).where(Quarto.id == member.quarto_id)
                        )

                        if not db_quarto:
                            raise HTTPException(
                                status_code=HTTPStatus.NOT_FOUND,
                                detail='Quarto não encontrado',
                            )

                        if db_quarto.republica_id != republica_id:
                            raise HTTPException(
                                status_code=HTTPStatus.BAD_REQUEST,
                                detail='Quarto não pertence a esta república',
                            )

                        membro_no_quarto = session.scalar(
                            select(Membro).where(
                                Membro.quarto_id == member.quarto_id,
                                Membro.id != member_id,
                                Membro.ativo == True
                            )
                        )

                        if membro_no_quarto:
                            raise HTTPException(
                                status_code=HTTPStatus.CONFLICT,
                                detail='Este quarto já está ocupado',
                            )

                db_member.fullname = member.fullname
                db_member.email = member.email
                db_member.telephone = member.telephone
                db_member.quarto_id = member.quarto_id

                session.commit()
                session.refresh(db_member)

                return db_member
        else:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail='Permissões negadas',
            )

    raise HTTPException(
        status_code=HTTPStatus.NOT_FOUND, detail='Republica nao encontrada'
    )


@router.delete(
    '/{republica_id}/{member_id}',
    status_code=HTTPStatus.OK,
    response_class=JSONResponse,
    response_model=Message,
)
def delete_member(
    session: T_Session,
    user: CurrentUser,
    republica_id: int,
    member_id: int,
):
    db_republica = session.scalar(
        select(Republica).where(Republica.id == republica_id)
    )

    if db_republica:
        if db_republica.user_id == user.id:
            db_member = session.scalar(
                select(Membro).where(
                    Membro.republica_id == republica_id, Membro.id == member_id
                )
            )
            if db_member:
                try:
                    # Soft delete: marca como inativo e registra data de saída
                    # preservando o histórico financeiro (pagamentos)
                    db_member.ativo = False
                    db_member.data_saida = datetime.now()
                    db_member.quarto_id = None  # Desvincula do quarto
                    session.commit()
                    session.refresh(db_member)

                    return {'message': 'Membro excluido'}

                except Exception:
                    raise HTTPException(
                        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                        detail='Erro interno do servidor',
                    )
        else:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail='Permissões negadas',
            )

    raise HTTPException(
        status_code=HTTPStatus.NOT_FOUND, detail='Republica nao encontrada'
    )
