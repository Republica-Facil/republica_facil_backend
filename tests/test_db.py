from dataclasses import asdict

from sqlalchemy import select

from republica_facil.model.models import User


def test_create_user(session, mock_db_time):
    with mock_db_time(model=User) as time:
        new_user = User(
            username='testuser',
            email='testuser@example.com',
            password='secret',
        )

        session.add(new_user)
        session.commit()

        user = session.scalar(select(User).where(User.username == 'testuser'))

        assert asdict(user) == {
            'id': 1,
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'secret',
            'created_at': time,
            'updated_at': time,
        }
