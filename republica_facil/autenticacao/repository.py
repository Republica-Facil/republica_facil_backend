from sqlalchemy import select
from sqlalchemy.orm import Session

from republica_facil.model.models import User


def get_user(email: str, session: Session):
    return session.scalar(select(User).where(User.email == email))
