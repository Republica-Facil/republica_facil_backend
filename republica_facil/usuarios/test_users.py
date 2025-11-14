from http import HTTPStatus

from republica_facil.main import app
from republica_facil.model.models import User
from republica_facil.security import get_current_user, get_password_hash
from republica_facil.usuarios.schema import UserPublic


def test_create_user_should_return_409_email_exists(client, user):
    response = client.post(
        '/users/',
        json={
            'fullname': 'Alice Silva',
            'email': user.email,
            'password': '1t1Testpass123@#S',
            'telephone': '61992991750',
        },
    )
    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': 'Email already exists'}


def test_delete_user_should_return_unauthorized(client):
    response = client.delete('/users/666')

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_update_user_should_return_unauthorized(client):
    response = client.put(
        '/users/666',
        json={
            'fullname': 'Bob Silva',
            'email': 'bob@example.com',
            'password': 'mynewpassword',
            'telephone': '11555555555',
        },
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_get_user_should_return_not_found(client):
    response = client.get('/users/666')

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'User not found'}


def test_get_user(client, user):
    response = client.get(f'/users/{user.id}')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'id': user.id,
        'fullname': user.fullname,
        'email': user.email,
        'telephone': user.telephone,
    }


def test_create_user(client):
    response = client.post(
        '/users/',
        json={
            'fullname': 'Test User',
            'email': 'test@example.com',
            'password': 'password123#S',
            'telephone': '11999999999',
        },
    )
    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {
        'id': 1,
        'fullname': 'Test User',
        'email': 'test@example.com',
        'telephone': '11999999999',
    }


def test_read_users(client):
    response = client.get('/users/')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'users': []}


def test_read_users_with_users(client, user):
    user_schema = UserPublic.model_validate(user).model_dump()
    response = client.get('/users/')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'users': [user_schema]}


def test_update_user(client, user):
    # Simular autenticação
    def get_current_user_override():
        return user

    app.dependency_overrides[get_current_user] = get_current_user_override

    try:
        response = client.put(
            f'/users/{user.id}',
            json={
                'fullname': 'Bob Silva',
                'email': 'bob@example.com',
                'password': 'secret123',
                'telephone': '11888888888',
            },
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json() == {
            'id': user.id,
            'fullname': 'Bob Silva',
            'email': 'bob@example.com',
            'telephone': '11888888888',
        }
    finally:
        app.dependency_overrides.clear()


# COLOCAR TOKEN NO CONFTEST

# def test_update_integrity_error(client, user):
#     client.post(
#         '/users/',
#         json={
#             'fullname': 'Fausto Silva',
#             'email': 'fausto@example.com',
#             'password': 'secret123',
#             'telephone': '11666666666',
#         },
#     )

#         response_update = client.put(
#             f'/users/{user.id}',
#             json={
#                 'fullname': 'Fausto Silva Updated',
#                 'email': 'bob@example.com',
#                 'password': 'mynewpassword',
#                 'telephone': '11777777777',
#             },
#         )

#         assert response_update.status_code == HTTPStatus.CONFLICT
#         assert response_update.json() == {'detail': 'Email already exists'}
#     finally:
#         app.dependency_overrides.clear()


def test_delete_user(client, user):
    # Simular autenticação
    def get_current_user_override():
        return user

    app.dependency_overrides[get_current_user] = get_current_user_override

    try:
        response = client.delete(f'/users/{user.id}')

        assert response.status_code == HTTPStatus.OK
        assert response.json() == {'message': 'User deleted'}
    finally:
        app.dependency_overrides.clear()


def test_create_user_weak_password(client):
    """Testa criação de usuário com senha fraca."""
    response = client.post(
        '/users/',
        json={
            'fullname': 'Test User Silva',
            'email': 'test@example.com',
            'password': '12345678',  # Senha fraca mas com 8 caracteres
            'telephone': '11999999999',
        },
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json()['detail'] == 'Weak password'


def test_create_user_invalid_telephone(client):
    """Testa criação de usuário com telefone inválido."""
    response = client.post(
        '/users/',
        json={
            'fullname': 'Test User',
            'email': 'test@example.com',
            'password': 'password123#S',
            'telephone': '123',  # Telefone inválido
        },
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert 'phone number is valid' in response.json()['detail']


def test_create_user_invalid_fullname(client):
    """Testa criação de usuário com nome inválido."""
    response = client.post(
        '/users/',
        json={
            'fullname': 'Test',  # Apenas um nome
            'email': 'test@example.com',
            'password': 'password123#S',
            'telephone': '11999999999',
        },
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert 'Enter your full name' in response.json()['detail']


def test_create_user_telephone_already_exists(client, user):
    """Testa criação de usuário com telefone já existente."""
    response = client.post(
        '/users/',
        json={
            'fullname': 'New User',
            'email': 'newuser@example.com',
            'password': 'password123#S',
            'telephone': user.telephone,  # Telefone já existe
        },
    )
    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()['detail'] == 'Telephone already exists'


def test_update_user_forbidden(client, user, session):
    """Testa atualização de usuário sem permissão."""
    # Criar outro usuário para simular autenticação
    other_user = User(
        fullname='Other User',
        email='other@example.com',
        password=get_password_hash('secret123'),
        telephone='11777777777',
    )
    session.add(other_user)
    session.commit()
    session.refresh(other_user)

    def get_current_user_override():
        return other_user

    app.dependency_overrides[get_current_user] = get_current_user_override

    try:
        response = client.put(
            f'/users/{user.id}',
            json={
                'fullname': 'Bob Silva',
                'email': 'bob@example.com',
                'password': 'secret123',
                'telephone': '11888888888',
            },
        )

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert response.json()['detail'] == 'Not enough permissions'
    finally:
        app.dependency_overrides.clear()


def test_update_user_email_conflict(client, user, session):
    """Testa atualização com email já existente."""
    # Criar outro usuário com email diferente
    other_user = User(
        fullname='Other User',
        email='existing@example.com',
        password=get_password_hash('secret123'),
        telephone='11777777777',
    )
    session.add(other_user)
    session.commit()

    def get_current_user_override():
        return user

    app.dependency_overrides[get_current_user] = get_current_user_override

    try:
        response = client.put(
            f'/users/{user.id}',
            json={
                'fullname': 'Updated Name',
                'email': 'existing@example.com',  # Email já existe
                'password': 'secret123',
                'telephone': '11888888888',
            },
        )

        assert response.status_code == HTTPStatus.CONFLICT
        assert response.json()['detail'] == 'Email already exists'
    finally:
        app.dependency_overrides.clear()


def test_update_password_success(client, user):
    """Testa alteração de senha com sucesso."""

    def get_current_user_override():
        return user

    app.dependency_overrides[get_current_user] = get_current_user_override

    try:
        response = client.patch(
            f'/users/change-password/{user.id}',
            json={
                'old_password': 'testpass123',  # Senha do fixture
                'new_password': 'NewPass123!@#',
                'confirm_password': 'NewPass123!@#',
            },
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json()['message'] == 'Senha alterada com sucesso'
    finally:
        app.dependency_overrides.clear()


def test_update_password_forbidden(client, user, session):
    """Testa alteração de senha de outro usuário."""
    other_user = User(
        fullname='Other User',
        email='other@example.com',
        password=get_password_hash('secret123'),
        telephone='11777777777',
    )
    session.add(other_user)
    session.commit()
    session.refresh(other_user)

    def get_current_user_override():
        return other_user

    app.dependency_overrides[get_current_user] = get_current_user_override

    try:
        response = client.patch(
            f'/users/change-password/{user.id}',
            json={
                'old_password': 'secret123',
                'new_password': 'NewPass123!@#',
                'confirm_password': 'NewPass123!@#',
            },
        )

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert response.json()['detail'] == 'Not enough permissions'
    finally:
        app.dependency_overrides.clear()


def test_update_password_wrong_old_password(client, user):
    """Testa alteração de senha com senha antiga incorreta."""

    def get_current_user_override():
        return user

    app.dependency_overrides[get_current_user] = get_current_user_override

    try:
        response = client.patch(
            f'/users/change-password/{user.id}',
            json={
                'old_password': 'wrongpassword',
                'new_password': 'NewPass123!@#',
                'confirm_password': 'NewPass123!@#',
            },
        )

        assert response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT
        assert 'senha antiga' in response.json()['detail']
    finally:
        app.dependency_overrides.clear()


def test_update_password_mismatch(client, user):
    """Testa alteração de senha com confirmação diferente."""

    def get_current_user_override():
        return user

    app.dependency_overrides[get_current_user] = get_current_user_override

    try:
        response = client.patch(
            f'/users/change-password/{user.id}',
            json={
                'old_password': 'testpass123',
                'new_password': 'NewPass123!@#',
                'confirm_password': 'DifferentPass123!@#',
            },
        )

        assert response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT
        assert 'senhas devem ser iguais' in response.json()['detail']
    finally:
        app.dependency_overrides.clear()


def test_update_password_weak_new_password(client, user):
    """Testa alteração de senha com nova senha fraca."""

    def get_current_user_override():
        return user

    app.dependency_overrides[get_current_user] = get_current_user_override

    try:
        response = client.patch(
            f'/users/change-password/{user.id}',
            json={
                'old_password': 'testpass123',
                'new_password': '12345678',  # Fraca mas com 8 chars
                'confirm_password': '12345678',
            },
        )

        assert response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT
        assert 'Senha fraca' in response.json()['detail']
    finally:
        app.dependency_overrides.clear()


def test_delete_user_forbidden(client, user, session):
    """Testa exclusão de outro usuário."""

    other_user = User(
        fullname='Other User',
        email='other@example.com',
        password=get_password_hash('secret123'),
        telephone='11777777777',
    )
    session.add(other_user)
    session.commit()
    session.refresh(other_user)

    def get_current_user_override():
        return other_user

    app.dependency_overrides[get_current_user] = get_current_user_override

    try:
        response = client.delete(f'/users/{user.id}')

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert response.json()['detail'] == 'Not enough permissions'
    finally:
        app.dependency_overrides.clear()
