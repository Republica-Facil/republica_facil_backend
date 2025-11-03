# from sqlalchemy import select
# from sqlalchemy.orm import Session

# from republica_facil.model.models import User
# from republica_facil.security import verify_password


# def authenticate_user(
#     session: Session, username: str, password: str
# ) -> User | None:
#     """
#     Autentica um usuário pelo username e senha.

#     Args:
#         session: Sessão do banco de dados
#         username: Nome de usuário ou email
#         password: Senha em texto plano

#     Returns:
#         User se autenticação bem-sucedida, None caso contrário
#     """
#     db_user = session.scalar(select(User).where(User.username == username))

#     if not db_user:
#         return None

#     if not verify_password(password, db_user.password):
#         return None

#     return db_user
