from republica_facil.autenticacao.repository import create_user
from republica_facil.autenticacao.schema import UserDB, UserSchema


def create_user_service(user: UserSchema) -> UserDB:
    return create_user(user)
