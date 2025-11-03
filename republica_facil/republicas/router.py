from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from republica_facil.database import get_session
from republica_facil.model.models import User
from republica_facil.republicas import repository
from republica_facil.republicas.schema import RepublicaCreate, RepublicaPublic
from republica_facil.security import get_current_user

router = APIRouter(prefix='/republicas', tags=['republicas'])


@router.post(
    '/', status_code=HTTPStatus.CREATED, response_model=RepublicaPublic
)
def create_republica(
    republica_data: RepublicaCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        republica = repository.create_republica(
            session=session,
            user_id=current_user.id,
            republica_data=republica_data,
        )
        return RepublicaPublic.model_validate(republica)
    except ValueError as e:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail='Erro interno do servidor',
        )
    except ValueError as e:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e))
    except Exception as e:  # <-- Adicione "as e" aqui
        print('!!!!!!!!!! ERRO INTERNO NÃO ESPERADO !!!!!!!!!!!')
        print(e)  # <-- Adicione este print
        print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail='Erro interno do servidor',
        )


@router.get('/{republica_id}', response_model=RepublicaPublic)
def get_republica(
    republica_id: int,
    session: Session = Depends(get_session),
):
    """Busca uma república pelo ID.

    Args:
        republica_id: ID da república
        session: Sessão do banco de dados

    Returns:
        RepublicaRead: A república encontrada

    Raises:
        HTTPException: Se a república não for encontrada
    """
    republica = repository.get_republica_by_id(session, republica_id)
    if not republica:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='República não encontrada'
        )
    return RepublicaPublic.model_validate(republica)


@router.get('/', response_model=list[RepublicaPublic])
def list_republicas(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
):
    """Lista todas as repúblicas.

    Args:
        skip: Número de registros para pular
        limit: Número máximo de registros para retornar
        session: Sessão do banco de dados

    Returns:
        list[RepublicaRead]: Lista de repúblicas
    """
    republicas = repository.list_republicas(session, skip, limit)
    return [
        RepublicaPublic.model_validate(republica) for republica in republicas
    ]
