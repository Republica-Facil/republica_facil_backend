from republica_facil.user.schema import UserDB, UserSchema

database = []


def create_user(user: UserSchema) -> UserDB:
    user_with_id = UserDB(id=len(database) + 1, **user.model_dump())
    database.append(user_with_id)
    return user_with_id
