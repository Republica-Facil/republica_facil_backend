from sqlalchemy import select
from sqlalchemy.orm import Session

from republica_facil.model.models import Republica, User
from republica_facil.republicas.schema import RepublicaCreate


def create_republica(
    session: Session, user_id: int, republica_data: RepublicaCreate
) -> Republica:
    """Cria uma nova república e associa o usuário como admin.

    Args:
        session: Sessão do banco de dados
        user_id: ID do usuário que está criando a república
        republica_data: Dados da república a ser criada

    Returns:
        Republica: A república criada

    Raises:
        ValueError: Se o usuário não existe
    """
    # Verificar se o usuário existe
    db_user = session.scalar(select(User).where(User.id == user_id))
    if not db_user:
        raise ValueError(f'Usuário com ID {user_id} não encontrado')

    try:
        # Criar a república
        republica = Republica(
            nome=republica_data.nome,
            cep=republica_data.cep,
            rua=republica_data.rua,
            numero=republica_data.numero,
            complemento=republica_data.complemento,
            bairro=republica_data.bairro,
            cidade=republica_data.cidade,
            estado=republica_data.estado,
            user_id=db_user.id,
        )
        session.add(republica)
        session.commit()
        session.refresh(republica)

        return republica

    except Exception:
        session.rollback()
        raise


def get_republica_by_id(
    session: Session, republica_id: int
) -> Republica | None:
    """Busca uma república pelo ID.

    Args:
        session: Sessão do banco de dados
        republica_id: ID da república

    Returns:
        Republica | None: A república encontrada ou None
    """
    return session.scalar(
        select(Republica).where(Republica.id == republica_id)
    )


def list_republicas(
    session: Session, skip: int = 0, limit: int = 100
) -> list[Republica]:
    """Lista todas as repúblicas.

    Args:
        session: Sessão do banco de dados
        skip: Número de registros para pular
        limit: Número máximo de registros para retornar

    Returns:
        list[Republica]: Lista de repúblicas
    """
    return list(session.scalars(select(Republica).offset(skip).limit(limit)))
