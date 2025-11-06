from sqlalchemy import select
from sqlalchemy.orm import Session

from republica_facil.model.models import User


def get_user_by_email(session: Session, email: str) -> User | None:
    return session.scalar(select(User).where(User.email == email))


def get_user_by_telephone(session: Session, telephone: str) -> User | None:
    return session.scalar(select(User).where(User.telephone == telephone))


def get_user_by_id(session: Session, user_id: int) -> User | None:
    return session.scalar(select(User).where(User.id == user_id))


def create_user_db(session: Session, user_data: dict) -> User:
    db_user = User(**user_data)  # ✅ CORRIGIDO: Criar instância com dados
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_users(
    session: Session, limit: int = 10, offset: int = 0
) -> list[User]:
    return session.scalars(select(User).limit(limit).offset(offset)).all()
