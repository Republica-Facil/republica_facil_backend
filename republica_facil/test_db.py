from dataclasses import asdict

from sqlalchemy import select

from republica_facil.model.models import User


def test_create_user(session, mock_db_time):
    with mock_db_time(model=User) as time:
        new_user = User(
            fullname='Test User',
            email='testuser@example.com',
            password='secret',
            telephone='11999999999',
        )

        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        user = session.scalar(
            select(User).where(User.email == 'testuser@example.com')
        )

        assert asdict(user) == {
            'id': 1,
            'fullname': 'Test User',
            'email': 'testuser@example.com',
            'password': 'secret',
            'telephone': '11999999999',
            'created_at': time,
            'updated_at': time,
            'republicas': [],
        }
