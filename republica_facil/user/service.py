from republica_facil.user.repository import create_user
from republica_facil.user.schema import UserDB, UserSchema


def create_user_service(user: UserSchema) -> UserDB:
    return create_user(user)
