from http import HTTPStatus

from republica_facil.main import app
from republica_facil.security import get_current_user
from republica_facil.usuarios.schema import UserPublic


def test_create_user_should_return_409_email_exists(client, user):
    response = client.post(
        '/users/',
        json={
            'fullname': 'Alice Silva',
            'email': user.email,
            'password': 'secret12',
            'telephone': '11777777777',
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
            'password': 'password123',
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
